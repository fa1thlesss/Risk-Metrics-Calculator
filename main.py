import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import datetime as dt
import scipy.stats as sps
import apimoex                                  # В КОНЦЕ НЕ ЗАБЫТЬ ДОБАВИТЬ МОСБИРЖУ


class Calculation:

    def __init__(self, filepath, value=1_000_000, VaR=0.99,
                 simulation_number=100_000, degrees_of_freedom=5):
        data = pd.read_csv(filepath, usecols=["Date", "Price"])

        data["Date"] = pd.to_datetime(data["Date"], format="mixed")
        data = data.sort_values("Date").reset_index(drop=True)

        self.p = data["Price"].to_numpy(dtype=float)
        self.profitability = self.p[1:] / self.p[:-1] - 1

        self.mu = np.exp(np.mean(np.log1p(self.profitability))) - 1   # Средняя геометрическая дневная доходность
        self.sigma = np.std(self.profitability, ddof=1)               # Стандартное отклонение

        self.value = value
        self.VaR = VaR
        self.simulation_number = simulation_number
        self.degrees_of_freedom = degrees_of_freedom

    def parametric(self, value=None, mu=None, sigma=None, VaR=None):
        value = self.value if value is None else value
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        VaR = self.VaR if VaR is None else VaR

        return round(-value * (mu + sigma * sps.norm.ppf(1 - VaR)), 2)

    def historical(self, value=None, profitability=None, VaR=None):
        value = self.value if value is None else value
        profitability = self.profitability if profitability is None else profitability
        VaR = self.VaR if VaR is None else VaR

        return round(-value * np.quantile(profitability, 1 - VaR), 2)

    def monte_carlo_normal(self, simulation_number=None, mu=None, sigma=None, value=None, VaR=None):
        simulation_number = self.simulation_number if simulation_number is None else simulation_number
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        value = self.value if value is None else value
        VaR = self.VaR if VaR is None else VaR

        drift = mu - sigma ** 2 / 2
        simulated_returns = np.random.normal(drift, sigma, simulation_number)

        var_result = round(-value * np.quantile(simulated_returns, 1 - VaR), 2)
        simulated_pnl = value * simulated_returns

        return var_result, simulated_pnl

    def monte_carlo_student(self, simulation_number=None, mu=None, sigma=None, value=None,
                            VaR=None, degrees_of_freedom=None):
        simulation_number = self.simulation_number if simulation_number is None else simulation_number
        mu = self.mu if mu is None else mu
        sigma = self.sigma if sigma is None else sigma
        value = self.value if value is None else value
        VaR = self.VaR if VaR is None else VaR
        degrees_of_freedom = self.degrees_of_freedom if degrees_of_freedom is None else degrees_of_freedom

        drift = mu - sigma ** 2 / 2
        scaling = np.sqrt((degrees_of_freedom - 2) / degrees_of_freedom)
        t_samples = np.random.standard_t(degrees_of_freedom, simulation_number)
        simulated_returns = drift + sigma * scaling * t_samples

        var_result = round(-value * np.quantile(simulated_returns, 1 - VaR), 2)
        simulated_pnl = value * simulated_returns

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

