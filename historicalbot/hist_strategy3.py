# IMPORTING LIBRARY MODULES
import numpy as np
import pandas as pd
# IMPORTING USER-DEFINED MODULES
from historicalbot.hist_datagrab import request_data


class Breakout:
    def __init__(self, symbol, lookback_period=20):
        self.symbol = symbol
        self.data = request_data(symbol)
        self.lookback_period = lookback_period
        self.results = None

    def validation(self):
        if self.data is None:
            return False
        else:
            return True

    def generate_signals(self):
        self.data['high'] = self.data[self.symbol].rolling(self.lookback_period).max()
        self.data['low'] = self.data[self.symbol].rolling(self.lookback_period).min()
        self.data['buy_signal'] = np.where((self.data[self.symbol] > self.data['high'].shift(1)), 1, 0)
        self.data['sell_signal'] = np.where((self.data[self.symbol] < self.data['low'].shift(1)), -1, 0)
        self.data['signal'] = self.data['buy_signal'] + self.data['sell_signal']
        self.data.dropna(inplace=True)
        return self.data['signal'].iat[-1]

    def extract_data(self):
        y_close_price = self.data[self.symbol]
        y_high = self.data['high']
        y_low = self.data['low']
        extracted_data = pd.DataFrame({
            'Close Price': y_close_price,
            'High': y_high,
            'Low': y_low
        })
        return extracted_data

    def backtest(self):
        self.data["returns"] = np.log(self.data[self.symbol].div(self.data[self.symbol].shift(1)))
        self.data.dropna(inplace=True)
        self.data['position'] = self.data['buy_signal'] - self.data['sell_signal']

    def test_results(self):
        self.data["strategy"] = self.data["returns"] * self.data["position"].shift(1)
        self.data.dropna(inplace=True)
        self.data["returnsbh"] = self.data["returns"].cumsum().apply(np.exp)
        self.data["returnsstrategy"] = self.data["strategy"].cumsum().apply(np.exp)
        perf = self.data["returnsstrategy"].iloc[-1]
        outperf = perf - self.data["returnsbh"].iloc[-1]
        self.results = self.data
        return round(perf, 6), round(outperf, 6)

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