# SipStack – NSE Stock Analysis & Backtesting Dashboard

SipStack is a Python-based stock analysis and backtesting dashboard that analyses historical NSE stock data and compares different trading strategies.

It allows users to enter an NSE stock symbol and explore historical price trends, technical indicators, and strategy performance through an interactive Streamlit interface.

## Features

- Interactive NSE stock selection.
- Historical stock data analysis using weekly data.
- 20-week Moving Average (MA).
- 14-week Wilder Relative Strength Index (RSI).
- Mean Reversion trading strategy.
- Momentum trading strategy.
- Buy & Hold benchmark comparison.
- Trade logs and completed trade statistics.
- Win rate and average trade return calculations.
- Maximum drawdown analysis.
- Interactive charts for price trends, RSI, and cumulative returns.

## Trading Strategies

### 1. Mean Reversion

Uses the idea that prices may return towards their historical average.

- Entry: Closing price falls at least 5% below the 20-week Moving Average.
- Exit: Closing price reaches or exceeds the 20-week Moving Average.

### 2. Momentum

Uses the idea that an existing price trend may continue.

- Entry: Closing price moves above the 20-week Moving Average.
- Exit: Closing price moves below the 20-week Moving Average.

### 3. Buy & Hold

Acts as a benchmark by holding the stock throughout the backtesting period.

## Technologies Used

- Python
- Pandas
- yfinance
- Matplotlib
- Streamlit

## Installation & Setup

1. Clone this repository:

   `git clone YOUR_GITHUB_REPOSITORY_URL`

2. Navigate to the project folder:

   `cd SIPStack`

3. Install the required libraries:

   `pip install -r requirements.txt`

4. Run the application:

   `python -m streamlit run app.py`

## Backtesting Methodology

- Uses approximately two years of historical weekly stock data.
- Generates trading signals using historical closing prices.
- Executes signals at the following week's opening price.
- Compares strategy returns against a Buy & Hold benchmark.
- Calculates performance statistics using historical data.

## Limitations

- Backtesting results are based on historical data and do not predict future performance.
- Brokerage charges, taxes, and slippage are not included.
- Trading strategies use simplified assumptions.
- This project is for educational and analytical purposes only and is not financial advice.

## Project Status

Developed as a personal learning project to explore Python, financial data analysis, technical indicators, and algorithmic trading concepts.