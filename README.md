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
├── ui.py # entry point, builds the main window and page navigation
├── var_page.py # VaR page
├── sharpe_page.py # Sharpe Ratio page
├── sortino_page.py # Sortino Ratio page
├── calc.py # loads a CSV and computes all the metrics
├── widgets.py # shared buttons/layout helpers used across pages
├── style.qss # stylesheet for the whole app
├── assets/ # icons, fonts, images
└── Data/ # sample CSVs to test with
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


### Requirements
 
- Python 3.10+
- Windows, macOS, or Linux
  
### Installation
 
```bash
git clone https://github.com/fa1thlesss/Risk-Metrics-Calculator.git
cd Risk-Metrics-Calculator
pip install -r requirements.txt
```
 
### Running
 
```bash
python main.py
```
