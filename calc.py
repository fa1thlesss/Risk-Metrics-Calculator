import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import datetime as dt
import scipy.stats as sps
import apimoex                                  # В КОНЦЕ НЕ ЗАБЫТЬ ДОБАВИТЬ МОСБИРЖУ


class Calculation:

    def __init__(self, filepath, value=1_000_000, VaR=0.99,
                 simulation_number=100_000, degrees_of_freedom=5,
                 historical_lookback=500, horizon=1):

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
        self.historical_lookback = historical_lookback
        self.horizon = horizon

    @staticmethod
    def _parse_price(raw):
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

    def parametric(self, value=None, mu=None, sigma=None, VaR=None, horizon=None):
        value = self.value if value is None else value
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        VaR = self.VaR if VaR is None else VaR
        horizon = self.horizon if horizon is None else horizon

        one_day_var = -value * (mu + sigma * sps.norm.ppf(1 - VaR))
        return round(one_day_var * np.sqrt(horizon), 2)

    def historical(self, value=None, profitability=None, VaR=None, lookback=None, horizon=None):
        value = self.value if value is None else value
        VaR = self.VaR if VaR is None else VaR
        horizon = self.horizon if horizon is None else horizon

        full_profitability = self.profitability if profitability is None else profitability
        lookback = self.historical_lookback if lookback is None else lookback

        used_returns = full_profitability[-lookback:] if lookback < len(full_profitability) else full_profitability

        one_day_var = -value * np.quantile(used_returns, 1 - VaR)
        return round(one_day_var * np.sqrt(horizon), 2)

    def monte_carlo_normal(self, simulation_number=None, mu=None, sigma=None, value=None, VaR=None, horizon=None):
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

    def monte_carlo_student(self, simulation_number=None, mu=None, sigma=None, value=None,
                            VaR=None, degrees_of_freedom=None, horizon=None):
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

    def run_all(self):
        var_normal, sims_normal = self.monte_carlo_normal()
        var_student, sims_student = self.monte_carlo_student()

        print("sigma:", self.sigma, " mu:", self.mu, " rows:", len(self.p))
        print(self.profitability.min(), self.profitability.max())

        return {
            'parametric': self.parametric(),
            'historical': self.historical(),
            'monte_carlo_normal': var_normal,
            'monte_carlo_student': var_student,
            'simulations_normal': sims_normal,
            'simulations_student': sims_student,
        }

calc = Calculation('Data/AAPL.csv')

