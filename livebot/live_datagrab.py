# IMPORTING API
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
# IMPORTING OTHER MODULES
from datetime import datetime, timedelta
# IMPORTING USER-DEFINED MODULES
from livebot.live_config import config


def get_timeframe_unit(unit_string):
    timeframe_unit = getattr(TimeFrameUnit, unit_string)
    return timeframe_unit


def request_data(stock):
    configurations = config()
    time_unit_string = configurations[0]
    amount = configurations[1]
    API_KEY = configurations[4]
    API_SECRET_KEY = configurations[5]
    for_the_past_x_days = configurations[7]
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
    data = data.ffill()
    return data
