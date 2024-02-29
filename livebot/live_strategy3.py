# IMPORTING LIBRARY MODULES
import numpy as np
import pandas as pd


class MeanReversion:
    def __init__(self, symbol, data, lookback_period=10):
        self.symbol = symbol
        self.data = data[[self.symbol]].copy()
        self.lookback_period = lookback_period
        self.results = None

    def generate_signals(self):
        self.data['mean_price'] = self.data[self.symbol].rolling(window=self.lookback_period).mean()
        self.data['buy_signal'] = np.where((self.data[self.symbol] < self.data['mean_price']), 1, 0)
        self.data['sell_signal'] = np.where((self.data[self.symbol] > self.data['mean_price']), -1, 0)
        self.data['signal'] = self.data['buy_signal'] + self.data['sell_signal']
        self.data.dropna(inplace=True)
        return self.data['signal'].iat[-1]

    def extract_data(self):
        y_close_price = self.data[self.symbol]
        y_mean_price = self.data['mean_price']
        extracted_data = pd.DataFrame({
            'Close Price': y_close_price,
            'Mean Price': y_mean_price
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

        scaling_unit = 60  # 60 minutes in an hour
        scaling_factor = np.sqrt(scaling_unit / minute_interval)

        # Calculate the average return for the specific timeframe
        ret = np.exp(self.data["strategy"].mean() * scaling_factor)

        # Calculate the volatility, scaled to hourly
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
