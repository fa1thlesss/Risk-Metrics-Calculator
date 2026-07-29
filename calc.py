"""Model layer for the Risk Metrics app.

Everything in this module is plain Python/numpy/pandas - no Qt imports.
It loads a price history from a CSV file and exposes methods to compute
Value at Risk (parametric, historical, Monte Carlo), the Sharpe ratio,
and the Sortino ratio, plus the rolling-window and comparison-chart data
each page's View needs to plot. The Views (``var_page.py``,
``sharpe_page.py``, ``sortino_page.py``) call into this class and only
format/display the results - they never compute anything themselves.
"""

from typing import Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import datetime as dt
import scipy.stats as sps
import apimoex                                  # TODO: add MOEX (Moscow Exchange) support


class Calculation:
    """Loads a single instrument's price history and computes risk metrics on it.

    Parameters
    ----------
    filepath:
        Path to a CSV file with ``Date`` and ``Price`` columns. Prices are
        parsed leniently to handle both ``1,234.56`` and ``1234,56`` style
        formatting (see :meth:`_parse_price`).
    value:
        Portfolio value in currency units, used as the base for VaR.
    VaR:
        Confidence level for Value at Risk, e.g. ``0.99`` for 99%.
    simulation_number:
        Number of paths to draw for the Monte Carlo VaR methods.
    degrees_of_freedom:
        Degrees of freedom for the Student's t Monte Carlo method. Lower
        values produce fatter tails (more extreme simulated losses).
    historical_lookback:
        Default number of most recent daily returns to use for the
        historical VaR method, when no explicit ``lookback`` is passed in.
    horizon:
        VaR time horizon in days. Daily VaR is scaled to this horizon via
        the square-root-of-time rule.

    Attributes
    ----------
    p:
        Full array of closing prices, oldest first.
    profitability:
        Daily simple returns, i.e. ``p[1:] / p[:-1] - 1``.
    mu, sigma:
        Mean (geometric) and standard deviation of ``profitability``,
        used as defaults by the parametric and Monte Carlo methods.
    """

    def __init__(self, filepath: str, value: float = 1_000_000, VaR: float = 0.99,
                 simulation_number: int = 100_000, degrees_of_freedom: int = 5,
                 historical_lookback: int = 500, horizon: int = 1):

        data = pd.read_csv(filepath, usecols=["Date", "Price"], dtype={"Price": str})

        data["Date"] = pd.to_datetime(data["Date"], format="mixed")
        data = data.sort_values("Date").reset_index(drop=True)

        self.p = data["Price"].apply(self._parse_price).to_numpy(dtype=float)
        self.profitability = self.p[1:] / self.p[:-1] - 1

        self.mu = np.exp(np.mean(np.log1p(self.profitability))) - 1
        self.sigma = np.std(self.profitability, ddof=1)

        self.value = value
        self.VaR = VaR
        self.simulation_number = simulation_number
        self.degrees_of_freedom = degrees_of_freedom
        self.historical_lookback = historical_lookback
        self.horizon = horizon

    @staticmethod
    def _parse_price(raw: str) -> float:
        """Parse a single price string into a float.

        Handles both thousands-separator styles found in exported price
        data: ``1,234.56`` (comma thousands, dot decimal) and
        ``1234,56`` / ``1.234,56`` (dot thousands, comma decimal). The
        heuristic assumes whichever of ``,``/``.`` appears *last* in the
        string is the decimal separator; if only a comma is present, it's
        treated as decimal when 1-2 digits follow it, otherwise as a
        thousands separator.
        """
        s = str(raw).strip()

        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s:
            decimal_part = s.split(',')[-1]
            if len(decimal_part) <= 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')

        return float(s)

    # -----------------------------------------------------------------
    # Value at Risk
    # -----------------------------------------------------------------

    def parametric(self, value: Optional[float] = None, mu: Optional[float] = None,
                    sigma: Optional[float] = None, VaR: Optional[float] = None,
                    horizon: Optional[int] = None) -> float:
        """Parametric (variance-covariance) VaR, assuming normally distributed returns.

        Any argument left as ``None`` falls back to the value set in
        :meth:`__init__`. Returns the VaR as a positive currency amount
        (i.e. the expected loss, not a return).
        """
        value = self.value if value is None else value
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        VaR = self.VaR if VaR is None else VaR
        horizon = self.horizon if horizon is None else horizon

        one_day_var = -value * (mu + sigma * sps.norm.ppf(1 - VaR))
        return round(one_day_var * np.sqrt(horizon), 2)

    def historical(self, value: Optional[float] = None, profitability: Optional[np.ndarray] = None,
                    VaR: Optional[float] = None, lookback: Optional[int] = None,
                    horizon: Optional[int] = None) -> float:
        """Historical simulation VaR: the empirical quantile of past returns.

        Uses the most recent ``lookback`` daily returns (defaulting to
        ``self.historical_lookback``) with no distributional assumption.
        Returns the VaR as a positive currency amount.
        """
        value = self.value if value is None else value
        VaR = self.VaR if VaR is None else VaR
        horizon = self.horizon if horizon is None else horizon

        full_profitability = self.profitability if profitability is None else profitability
        lookback = self.historical_lookback if lookback is None else lookback

        used_returns = full_profitability[-lookback:] if lookback < len(full_profitability) else full_profitability

        one_day_var = -value * np.quantile(used_returns, 1 - VaR)
        return round(one_day_var * np.sqrt(horizon), 2)

    def monte_carlo_normal(self, simulation_number: Optional[int] = None, mu: Optional[float] = None,
                            sigma: Optional[float] = None, value: Optional[float] = None,
                            VaR: Optional[float] = None, horizon: Optional[int] = None):
        """Monte Carlo VaR using normally distributed simulated returns.

        Returns
        -------
        A ``(var_result, simulated_pnl)`` tuple: the VaR as a positive
        currency amount, and the full array of simulated P&L outcomes
        (used by the Views to plot the P&L distribution histogram).
        """
        simulation_number = self.simulation_number if simulation_number is None else simulation_number
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        value = self.value if value is None else value
        VaR = self.VaR if VaR is None else VaR
        horizon = self.horizon if horizon is None else horizon

        drift = mu - sigma ** 2 / 2
        simulated_returns = np.random.normal(drift, sigma, simulation_number)

        simulated_pnl = value * simulated_returns * np.sqrt(horizon)
        var_result = round(-np.quantile(simulated_pnl, 1 - VaR), 2)

        return var_result, simulated_pnl

    def monte_carlo_student(self, simulation_number: Optional[int] = None, mu: Optional[float] = None,
                             sigma: Optional[float] = None, value: Optional[float] = None,
                             VaR: Optional[float] = None, degrees_of_freedom: Optional[int] = None,
                             horizon: Optional[int] = None):
        """Monte Carlo VaR using a Student's t distribution for simulated returns.

        Fatter-tailed than :meth:`monte_carlo_normal`, controlled by
        ``degrees_of_freedom`` - lower values mean more extreme tail
        losses are simulated. Returns the same ``(var_result,
        simulated_pnl)`` shape as :meth:`monte_carlo_normal`.
        """
        simulation_number = self.simulation_number if simulation_number is None else simulation_number
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        value = self.value if value is None else value
        VaR = self.VaR if VaR is None else VaR
        degrees_of_freedom = self.degrees_of_freedom if degrees_of_freedom is None else degrees_of_freedom
        horizon = self.horizon if horizon is None else horizon

        drift = mu - sigma ** 2 / 2
        scaling = np.sqrt((degrees_of_freedom - 2) / degrees_of_freedom)
        t_samples = np.random.standard_t(degrees_of_freedom, simulation_number)
        simulated_returns = drift + sigma * scaling * t_samples

        simulated_pnl = value * simulated_returns * np.sqrt(horizon)
        var_result = round(-np.quantile(simulated_pnl, 1 - VaR), 2)

        return var_result, simulated_pnl

    def run_all(self) -> dict:
        """Run every VaR method with the instance's default parameters.

        Returns a dict with keys ``parametric``, ``historical``,
        ``monte_carlo_normal``, ``monte_carlo_student`` (all VaR amounts),
        plus ``simulations_normal``/``simulations_student`` (the raw
        simulated P&L arrays, for plotting). This is what ``var_page.py``
        calls when the user clicks "Calculate all methods".
        """
        var_normal, sims_normal = self.monte_carlo_normal()
        var_student, sims_student = self.monte_carlo_student()

        return {
            'parametric': self.parametric(),
            'historical': self.historical(),
            'monte_carlo_normal': var_normal,
            'monte_carlo_student': var_student,
            'simulations_normal': sims_normal,
            'simulations_student': sims_student,
        }

    # -----------------------------------------------------------------
    # Sharpe / Sortino
    # -----------------------------------------------------------------

    def _get_returns(self, lookback: Optional[int] = None) -> np.ndarray:
        """Return the most recent ``lookback`` daily returns, or all of them."""
        returns = self.profitability
        if lookback is not None and lookback < len(returns):
            returns = returns[-lookback:]
        return returns

    def sharpe_ratio(self, lookback: Optional[int] = None, risk_free_annual: float = 0.0,
                      trading_days: int = 252) -> dict:
        """Compute the annualized Sharpe ratio over the most recent ``lookback`` days.

        Parameters
        ----------
        lookback:
            Number of most recent daily returns to use. ``None`` uses the
            full return history.
        risk_free_annual:
            Annual risk-free rate as a decimal (e.g. ``0.045`` for 4.5%),
            converted internally to a daily rate.
        trading_days:
            Trading days per year used for annualizing (252 or 365).

        Returns
        -------
        dict with keys ``sharpe_ratio``, ``annualized_return``,
        ``annualized_volatility``, ``risk_free_daily`` (needed by
        :meth:`rolling_sharpe`), and ``returns`` (the return slice that
        was actually used - handy for the caller to reuse in plots).
        """
        returns = self._get_returns(lookback)

        mu_daily = np.mean(returns)
        sigma_daily = np.std(returns, ddof=1)
        risk_free_daily = risk_free_annual / trading_days

        annualized_return = (1 + mu_daily) ** trading_days - 1
        annualized_volatility = sigma_daily * np.sqrt(trading_days)
        sharpe = (mu_daily - risk_free_daily) / sigma_daily * np.sqrt(trading_days)

        return {
            'sharpe_ratio': sharpe,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'risk_free_daily': risk_free_daily,
            'returns': returns,
        }

    def rolling_sharpe(self, returns: np.ndarray, window: int, risk_free_daily: float,
                        trading_days: int) -> np.ndarray:
        """Compute the Sharpe ratio over a rolling window across ``returns``.

        Returns an array of length ``len(returns) - window`` (empty if
        ``returns`` isn't longer than ``window``), one Sharpe ratio per
        window position, for plotting a rolling-Sharpe line chart.

        Vectorized via pandas ``.rolling()`` rather than a Python loop -
        O(n) instead of the O(n * window) a naive per-window slice/mean
        would cost.
        """
        if len(returns) <= window:
            return np.array([])

        s = pd.Series(returns)
        rolling_mean = s.rolling(window).mean()
        rolling_std = s.rolling(window).std(ddof=1)
        sharpe = (rolling_mean - risk_free_daily) / rolling_std * np.sqrt(trading_days)

        # Output position i (for i in [window, len(returns))) uses the window
        # returns[i-window:i], which ends at i-1. pandas' rolling window ending
        # at i-1 lives at positional index i-1, so we keep positions
        # window-1 .. len(returns)-2 inclusive - the same length/alignment the
        # original per-window loop produced.
        return sharpe.iloc[window - 1: len(returns) - 1].to_numpy()

    def sortino_ratio(self, lookback: Optional[int] = None, mar_annual: float = 0.0,
                       trading_days: int = 252) -> dict:
        """Compute the annualized Sortino ratio over the most recent ``lookback`` days.

        Like :meth:`sharpe_ratio`, but penalizes only downside deviation
        below the minimum acceptable return (MAR) instead of total
        volatility.

        Parameters
        ----------
        lookback:
            Number of most recent daily returns to use. ``None`` uses the
            full return history.
        mar_annual:
            Minimum acceptable annual return as a decimal, converted
            internally to a daily MAR.
        trading_days:
            Trading days per year used for annualizing (252 or 365).

        Returns
        -------
        dict with keys ``sortino_ratio`` (``inf`` if there were no
        downside days in the window), ``annualized_return``,
        ``annualized_downside_deviation``, ``mar_daily`` (needed by
        :meth:`rolling_sortino`), and ``returns``.
        """
        returns = self._get_returns(lookback)

        mu_daily = np.mean(returns)
        mar_daily = mar_annual / trading_days

        downside_returns = returns[returns < mar_daily]
        downside_deviation_daily = (
            np.sqrt(np.mean((downside_returns - mar_daily) ** 2))
            if len(downside_returns) > 0 else 0.0
        )

        annualized_return = (1 + mu_daily) ** trading_days - 1
        annualized_downside_deviation = downside_deviation_daily * np.sqrt(trading_days)

        if downside_deviation_daily > 0:
            sortino = (mu_daily - mar_daily) / downside_deviation_daily * np.sqrt(trading_days)
        else:
            sortino = float("inf")

        return {
            'sortino_ratio': sortino,
            'annualized_return': annualized_return,
            'annualized_downside_deviation': annualized_downside_deviation,
            'mar_daily': mar_daily,
            'returns': returns,
        }

    def rolling_sortino(self, returns: np.ndarray, window: int, mar_daily: float,
                         trading_days: int) -> np.ndarray:
        """Compute the Sortino ratio over a rolling window across ``returns``.

        Returns an array of length ``len(returns) - window`` (empty if
        ``returns`` isn't longer than ``window``); a window with no
        downside days produces ``nan`` rather than ``inf``, since ``nan``
        plots as a gap in the line chart instead of an infinite spike.

        Vectorized via pandas ``.rolling()`` sums rather than a Python
        loop. The trick: clamp each return to ``min(return - mar, 0)`` so
        upside days contribute exactly 0 to both the sum-of-squares and
        the downside count, then a window's downside deviation is just
        ``sqrt(rolling_sum_of_squares / rolling_downside_count)`` - the
        same "mean over downside days only" definition the original
        per-window loop used, just computed with O(n) rolling sums
        instead of O(n * window) per-window slicing.
        """
        if len(returns) <= window:
            return np.array([])

        returns = np.asarray(returns)
        downside = np.minimum(returns - mar_daily, 0.0)   # 0.0 on days at/above MAR
        is_downside = (downside < 0).astype(float)

        rolling_mean = pd.Series(returns).rolling(window).mean()
        sum_sq = pd.Series(downside ** 2).rolling(window).sum()
        downside_count = pd.Series(is_downside).rolling(window).sum()

        with np.errstate(invalid="ignore", divide="ignore"):
            downside_deviation = np.sqrt(sum_sq / downside_count.replace(0, np.nan))
        downside_deviation = downside_deviation.where(downside_deviation > 0)  # 0 -> NaN too

        sortino = (rolling_mean - mar_daily) / downside_deviation * np.sqrt(trading_days)

        # Same alignment as rolling_sharpe: keep positions window-1 .. len(returns)-2.
        return sortino.iloc[window - 1: len(returns) - 1].to_numpy()

    @staticmethod
    def cumulative_return(returns: np.ndarray) -> np.ndarray:
        """Compound a daily return series into a cumulative return series.

        ``cumulative_return(returns)[i]`` is the total return of holding
        the position from day 0 through day ``i``, e.g. ``0.10`` for +10%.
        """
        return np.cumprod(1 + returns) - 1

    @staticmethod
    def risk_free_curve(n_days: int, risk_free_annual: float, trading_days: int) -> np.ndarray:
        """Compound an annual risk-free rate into a daily cumulative-return curve.

        Used as the benchmark line against :meth:`cumulative_return` on
        the Sharpe page's cumulative-return chart, so both series are on
        the same "compounded return since day 0" basis.
        """
        days = np.arange(n_days)
        return (1 + risk_free_annual) ** (days / trading_days) - 1