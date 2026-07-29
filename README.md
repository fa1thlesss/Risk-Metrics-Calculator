# Risk Metrics Calculator
 
## Features
 
- **Value at Risk (VaR)** calculated three ways, side by side:
  - Parametric (variance-covariance)
  - Historical simulation
  - Monte Carlo simulation (Normal and Student's t distributions)
- **Sharpe Ratio** — risk-adjusted return using total volatility, with a rolling-window chart and cumulative return vs. risk-free rate comparison
- **Sortino Ratio** — risk-adjusted return using only downside volatility, with a returns distribution chart highlighting the downside tail
- Works with any CSV containing a date column and a price column — automatically handles:
  - Mixed date formats (`MM/DD/YYYY`, `DD.MM.YYYY`, etc.)
  - Mixed decimal separators (`.` or `,`)
- **Refresh Data** button pulls the latest prices for a loaded ticker via `yfinance`

<img width="1373" height="794" alt="изображение" src="https://github.com/user-attachments/assets/51d2c516-f06a-49b2-a1ef-a48df78c7b65" />

<img width="1376" height="796" alt="изображение" src="https://github.com/user-attachments/assets/15ad2394-80f2-4adc-b601-f7ed83b4abba" />

## Project Structure
 
```
├── ui.py               # App entry point - MainWindow, page navigation
├── var_page.py          # Value at Risk page (UI)
├── sharpe_page.py        # Sharpe Ratio page (UI)
├── sortino_page.py        # Sortino Ratio page (UI)
├── calc.py                 # Calculation class - loads CSV data, computes all metrics
├── widgets.py                # Shared UI helpers (layout utilities, Open File/Refresh Data buttons)
├── style.qss                   # App-wide stylesheet
├── assets/                       # Icons, fonts, and images used by the UI
└── Data/                           # Sample CSV files
```

## How It Works
 
The app expects a CSV with at least a date column and a price column (`Date`, `Price`). On load, it:
 
1. Parses dates flexibly and sorts them chronologically
2. Auto-detects the decimal separator per value
3. Computes daily log returns, mean, and standard deviation
4. Feeds those into whichever page's calculations are requested
   
### Value at Risk
 
For a given confidence level and time horizon, VaR estimates the maximum expected loss over that period, calculated three independent ways so the methods can be compared directly.
 
### Sharpe Ratio
 
`(annualized return − risk-free rate) / annualized volatility` — measures return earned per unit of *total* risk taken.
 
### Sortino Ratio
 
Same idea as Sharpe, but only penalizes downside volatility (returns below a minimum acceptable return), rather than all volatility.
