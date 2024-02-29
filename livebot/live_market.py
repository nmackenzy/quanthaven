# IMPORTING MODULES
import datetime
import pytz
import time
from alpaca.trading.client import TradingClient
from livebot.live_config import config

# DECLARING GLOBAL VARIABLES
market_open_time = datetime.time(9, 30)
market_close_time = datetime.time(16, 0)
market_timezone = pytz.timezone('America/New_York')


def sleep():
    configurations = config()
    API_KEY = configurations[4]
    API_SECRET_KEY = configurations[5]
    trading_client = TradingClient(API_KEY, API_SECRET_KEY, paper=True)
    now = datetime.datetime.now(market_timezone)
    clock = trading_client.get_clock()
    next_open = clock.next_open.astimezone(market_timezone)
    time_until_open = next_open - now
    sleep_duration = time_until_open.total_seconds() + 5
    print(f"Sleeping for {time_until_open} until market opens...")
    time.sleep(sleep_duration)


def check_if_open():
    current_datetime = datetime.datetime.now(market_timezone)
    current_day = current_datetime.weekday()

    if current_day > 4:
        return False

    start_datetime = current_datetime.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0,
                                              microsecond=0)
    end_datetime = current_datetime.replace(hour=market_close_time.hour, minute=market_close_time.minute, second=0,
                                            microsecond=0)

    if start_datetime <= current_datetime <= end_datetime:
        return True
    return False