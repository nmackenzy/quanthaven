# IMPORTING LIBRARY MODULES
import numpy as np
import pandas as pd
# IMPORTING USER-DEFINED MODULES
from historicalbot.hist_datagrab import request_data


class Momentum:
    def __init__(self, symbol, lookback_period=10):
        # Initialize the Momentum class with a stock symbol and an optional lookback period for calculations
        self.symbol = symbol
        self.data = request_data(symbol)  # Fetches the stock data
        self.lookback_period = lookback_period
        self.results = None  # A placeholder to store results

    def validation(self):
        if self.data is None:
            return False
        else:
            return True

    def generate_signals(self):
        # Calculate momentum as the difference between the current price and the price 'lookback_period' days ago
        self.data['momentum'] = self.data[self.symbol] - self.data[self.symbol].shift(self.lookback_period)
        # Generate buy signals where momentum is positive, represented as 1
        self.data['buy_signal'] = np.where((self.data['momentum'] > 0), 1, 0)
        # Generate sell signals where momentum is negative, represented as -1
        self.data['sell_signal'] = np.where((self.data['momentum'] < 0), -1, 0)
        # Combine buy and sell signals to get an overall signal (1 for buy, -1 for sell, 0 otherwise)
        self.data['signal'] = self.data['buy_signal'] + self.data['sell_signal']
        self.data.dropna(inplace=True)  # Remove rows with missing data
        return self.data['signal'].iat[-1]  # Return the most recent signal

    def extract_data(self):
        # Extract relevant data for analysis: close price and momentum
        y_close_price = self.data[self.symbol]
        y_momentum = self.data['momentum']
        extracted_data = pd.DataFrame({
            'Close_Price': y_close_price,
            'Momentum': y_momentum
        })
        return extracted_data

    def backtest(self):
        # Calculate logarithmic returns based on the stock's closing prices
        self.data["returns"] = np.log(self.data[self.symbol].div(self.data[self.symbol].shift(1)))
        self.data.dropna(inplace=True)  # Remove rows with missing data
        # Create a 'position' column that holds the difference between buy and sell signals
        self.data['position'] = self.data['buy_signal'] - self.data['sell_signal']

    def test_results(self):
        # Calculate the strategy's returns by multiplying the returns with the previous day's position
        self.data["strategy"] = self.data["returns"] * self.data["position"].shift(1)
        self.data.dropna(inplace=True)  # Remove rows with missing data
        # Calculate cumulative returns for both the strategy and a buy-and-hold approach
        self.data["returnsbh"] = self.data["returns"].cumsum().apply(np.exp)
        self.data["returnsstrategy"] = self.data["strategy"].cumsum().apply(np.exp)
        perf = self.data["returnsstrategy"].iloc[-1]  # Final performance of the strategy
        outperf = perf - self.data["returnsbh"].iloc[-1]  # Outperformance over buy-and-hold
        self.results = self.data  # Store results in the instance variable
        return round(perf, 6), round(outperf, 6)  # Return rounded performance and outperformance

    def calculate_statistics(self, minute_interval):
        if self.data is None or 'strategy' not in self.data.columns:
            print("Strategy results not found. Please run the backtest first.")
            return

        if minute_interval < 60:
            timeframe = 'Minute'
            multiplier = minute_interval
            scaling_unit = 60  # 60 minutes in an hour
        elif 60 <= minute_interval < 1440:
            timeframe = 'Hour'
            multiplier = minute_interval / 60
            scaling_unit = 24  # 24 hours in a day
        else:
            timeframe = 'Day'
            multiplier = minute_interval / 1440
            scaling_unit = 252  # Approximately 252 trading days in a year

        scaling_factor = np.sqrt(scaling_unit / multiplier)

        # Calculate the average return for the specific timeframe
        ret = np.exp(self.data["strategy"].mean() * scaling_factor)

        # Calculate the volatility, scaled to the next higher unit of time
        std = self.data["strategy"].std() * scaling_factor

        return ret, std

    def extract_results(self):
        if self.results is None:
            print("No results to extract. Run the test first.")
            return None
        y_returnsbh = self.results['returnsbh']
        y_returnsstrategy = self.results['returnsstrategy']
        extracted_data = pd.DataFrame({
            'ReturnsBH': y_returnsbh,
            'ReturnsStrategy': y_returnsstrategy
        })
        return extracted_data
