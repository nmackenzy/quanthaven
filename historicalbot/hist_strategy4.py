# IMPORTING LIBRARY MODULES
import numpy as np
import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVR
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
# IMPORTING USER-DEFINED MODULES
from historicalbot.hist_datagrab import request_all_data


class SVRStrategy:
    def __init__(self, symbol, indicators=None):
        self.data = request_all_data(symbol)
        self.indicators = indicators if indicators is not None else {'RSI': 15, 'EMAF': 20, 'EMAM': 100, 'EMAS': 150}
        self.results = None

    def validation(self):
        if self.data is None:
            return False
        else:
            return True

    # Training + signal generation
    def generate_signals(self):
        # INDICATORS
        for indicator, length in self.indicators.items():
            if indicator == 'RSI':
                self.data['RSI'] = ta.rsi(self.data.close, length=length)
            elif indicator == 'EMAF':
                self.data['EMAF'] = ta.ema(self.data.close, length=length)
            elif indicator == 'EMAM':
                self.data['EMAM'] = ta.ema(self.data.close, length=length)
            elif indicator == 'EMAS':
                self.data['EMAS'] = ta.ema(self.data.close, length=length)

        self.data['targetnextclose'] = self.data['close'].shift(-1)
        self.data.drop(['volume', 'trade_count', 'vwap', 'symbol'], axis=1, inplace=True)
        self.data.dropna(inplace=True)

        # SPLITTING DATASET
        X = self.data.drop('targetnextclose', axis=1).values
        y = self.data['targetnextclose'].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # SCALING & MODEL TRAINING
        model = make_pipeline(MinMaxScaler(), SVR(C=1.0, epsilon=0.2))
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        df = pd.DataFrame({
            'Close': y_test,
            'Pred Close': y_pred
        })

        self.results = df
        self.results['buy_signal'] = np.where(df['Pred Close'].shift(-1) > df['Close'], 1, 0)
        self.results['sell_signal'] = np.where(df['Pred Close'].shift(-1) < df['Close'], -1, 0)
        self.results['signal'] = self.results['buy_signal'] + self.results['sell_signal']
        self.results.dropna(inplace=True)
        return self.results['signal'].iat[-1]

    def extract_data(self):
        if self.results is None:
            print("No results to extract. Run the test first.")
            return None
        y_actual_close = self.results["Close"]
        y_predicted_close = self.results["Pred Close"]
        extracted_data = pd.DataFrame({
            'Actual_Close': y_actual_close,
            'Predicted_Close': y_predicted_close
        })
        return extracted_data

    def backtest(self):
        self.results["returns"] = np.log(self.results['Close'].div(self.results['Close'].shift(1)))
        self.results.dropna(inplace=True)
        self.results['position'] = self.results['buy_signal'] - self.results['sell_signal']

    def test_results(self):
        self.results["strategy"] = self.results["returns"] * self.results["position"].shift(1)
        self.results.dropna(inplace=True)
        self.results["returnsbh"] = self.results["returns"].cumsum().apply(np.exp)
        self.results["returnsstrategy"] = self.results["strategy"].cumsum().apply(np.exp)
        perf = self.results["returnsstrategy"].iloc[-1]
        outperf = perf - self.results["returnsbh"].iloc[-1]
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

        rmse = np.sqrt(np.mean(((self.results["Pred Close"] - self.results["Close"]) ** 2)))

        std = self.results["strategy"].std() * scaling_factor  # Standard deviation scaled to the appropriate timeframe

        return rmse, std

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
