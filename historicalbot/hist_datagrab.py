# IMPORTING API
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
# IMPORTING MODULES
from datetime import datetime, timedelta
import requests
# IMPORTING USER-DEFINED MODULES
from historicalbot.hist_config import config


def get_timeframe_unit(unit_string):  # Convert string to an actual value
    timeframe_unit = getattr(TimeFrameUnit, unit_string)
    return timeframe_unit


def request_data(stock):  # Reqeust close price for a specific stock
    try:
        configurations = config()
        time_unit_string = configurations[0]
        amount = configurations[1]
        API_KEY = configurations[4]
        API_SECRET_KEY = configurations[5]
        for_the_past_x_days = configurations[8]
        client = StockHistoricalDataClient(API_KEY, API_SECRET_KEY)
        current_date = datetime.now()
        date_x_days_ago = current_date - timedelta(days=for_the_past_x_days)
        formatted_date = date_x_days_ago.strftime('%Y-%m-%d')
        request_params = StockBarsRequest(
            symbol_or_symbols=stock,
            timeframe=TimeFrame(amount, get_timeframe_unit(time_unit_string)),
            start=datetime.strptime(f"{formatted_date}", '%Y-%m-%d'),
        )
        bars = client.get_stock_bars(request_params).df
        data = bars["close"].to_frame()
        data = data.reset_index().pivot(index='timestamp', columns='symbol', values='close')
        data = data.ffill()  # NaN values get forward filled
        return data
    except requests.exceptions.ConnectionError as e:
        # Handle the connection error
        return None

def request_all_data(stock):  # Request all data for a specific stock
    try:
        configurations = config()
        time_unit_string = configurations[0]
        amount = configurations[1]
        API_KEY = configurations[4]
        API_SECRET_KEY = configurations[5]
        for_the_past_x_days = configurations[8]
        # DECLARING GLOBAL VARIABLES
        client = StockHistoricalDataClient(API_KEY, API_SECRET_KEY)
        current_date = datetime.now()
        date_x_days_ago = current_date - timedelta(days=for_the_past_x_days)
        formatted_date = date_x_days_ago.strftime('%Y-%m-%d')
        request_params = StockBarsRequest(
            symbol_or_symbols=stock,
            timeframe=TimeFrame(amount, get_timeframe_unit(time_unit_string)),
            start=datetime.strptime(f"{formatted_date}", '%Y-%m-%d'),
        )
        df = client.get_stock_bars(request_params).df
        df_reset = df.reset_index()
        df_reset.set_index('timestamp', inplace=True)
        df_reset = df_reset.ffill()  # Forward fill assumed to best account for market behaviour for NaN values
        return df_reset
    except requests.exceptions.ConnectionError as e:
        # Handle the connection error
        return None

def calculate_current_price(stock):  # Return the current price of a stock
    df = request_data(stock).copy()
    value = df.iloc[-1:].values[0]
    return value
