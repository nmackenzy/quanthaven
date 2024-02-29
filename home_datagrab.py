# IMPORTING API
from alpaca.trading.client import TradingClient
# IMPORTING MODULES
import requests
import yfinance as yf
import sqlite3
# IMPORTING USER-DEFINED MODULES
import security


def home_data(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT api_key, api_secret_key, av_key FROM details WHERE user_id=?", (user_id,))
    record = c.fetchone()
    c.close()
    conn.close()

    API_KEY = security.decrypt_data(record[0], str(user_id) + 'A')
    API_SECRET_KEY = security.decrypt_data(record[1], str(user_id) + 'B')
    AVKEY = security.decrypt_data(record[2], str(user_id) + 'C')

    trading_client = TradingClient(API_KEY, API_SECRET_KEY, paper=True)

    # BALANCE AND PROFIT/LOSS

    account_balance = float(trading_client.get_account().cash)
    account_equity = 100000
    total_profit_or_loss = -(float(account_equity) - float(account_balance))

    # SECTOR SENTIMENT

    topics = {'energy_transportation': 'Energy & Transportation',
              'manufacturing': 'Manufacturing',
              'life_sciences': 'Life Sciences',
              'real_estate': 'Real Estate & Construction',
              'retail_wholesale': 'Retail & Wholesale',
              'technology': 'Technology'
              }

    sentiment_values = []

    for topic in topics:
        url3 = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics={topic}&apikey={AVKEY}'
        r3 = requests.get(url3)
        data_latest = r3.json()

        def calculate_weighted_sentiment(data, current_topic):
            sentiment_sum = 0.0
            relevance_sum = 0.0

            for item in data["feed"]:

                relevance = 0.0

                for topic_item in item["topics"]:
                    if topic_item["topic"] == topics[current_topic]:
                        relevance = float(topic_item["relevance_score"])

                sentiment = float(item["overall_sentiment_score"])

                sentiment_sum += sentiment * relevance
                relevance_sum += relevance

            if relevance_sum == 0.0:
                return None

            return sentiment_sum / relevance_sum

        val = calculate_weighted_sentiment(data_latest, topic)
        sentiment_values.append(round(val, 2))

    # TOP 3 GAINERS

    top_3 = []

    url1 = f'https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={AVKEY}'
    r1 = requests.get(url1)
    data1 = r1.json()

    top_gainers = data1['top_gainers'][:3]

    for gainer in top_gainers:
        top_3.append(f"{gainer['ticker']}: + {round(float(gainer['change_percentage'][:-1]))}%")

    # WATCHLIST

    watchlist = ['SPY', 'QQQ', 'DIA']
    watchlist_stats = {}

    for symbol in watchlist:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")  # Get last 2 days' historical market data
        latest = hist['Close'].iloc[-1]  # The latest closing price
        previous = hist['Close'].iloc[-2]  # The previous closing price
        percent_change = round(((latest - previous) / previous) * 100, 2)
        watchlist_stats[symbol] = percent_change

    final = [account_balance, total_profit_or_loss, sentiment_values, top_3, watchlist_stats]

    return final
