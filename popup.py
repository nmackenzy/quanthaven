import requests
from datetime import datetime

# OVERVIEW

def get_overview(symbol, AVKEY):
    url1 = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={AVKEY}'
    r1 = requests.get(url1)
    data_latest1 = r1.json()

    name = data_latest1["Name"]
    description = data_latest1["Description"]
    exchange = data_latest1["Exchange"]
    currency = data_latest1["Currency"]
    country = data_latest1["Country"]
    sector = data_latest1["Sector"]
    market_capitalisation = data_latest1["MarketCapitalization"]
    pe_ratio = data_latest1["PERatio"]
    eps = data_latest1["EPS"]
    profit_margin = data_latest1["ProfitMargin"]
    beta = data_latest1["Beta"]
    MA50 = data_latest1["50DayMovingAverage"]
    MA200 = data_latest1["200DayMovingAverage"]
    shares_outstanding = data_latest1["SharesOutstanding"]

    overview = [name, description, exchange, currency, country, sector, market_capitalisation, pe_ratio, eps,
                profit_margin, beta, MA50, MA200, shares_outstanding]
    return overview

# NEWS

def get_news(symbol, AVKEY):
    news = []

    url3 = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&limit=5&apikey={AVKEY}'
    r3 = requests.get(url3)
    data_latest3 = r3.json()

    for item in data_latest3["feed"]:
        title = item["title"]
        news.append(title)
        source = item["source"]
        news.append(source)
        date = item["time_published"]
        dt = datetime.strptime(date, "%Y%m%dT%H%M%S")
        date_str = dt.strftime("%Y-%m-%d")
        news.append(date_str)
    return news
