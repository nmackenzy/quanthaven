# IMPORTING MODULES
import requests
from datetime import datetime
import math
# IMPORTING USER-DEFINED MODULES
from historicalbot.hist_datagrab import request_data
from historicalbot.hist_config import config


def get_correlation_data():  # How correlated is the stock to the other stocks in the portfolio?
    configurations = config()
    stocks = configurations[2]
    correlation_data = []
    df = request_data(stocks)
    for stock in stocks:
        correlation_matrix = df.corr()
        stock_correlations = correlation_matrix[stock]
        average_correlation = stock_correlations.mean()
        correlation_data.append(average_correlation)
    return correlation_data


def get_sentiment_data():
    configurations = config()
    stocks = configurations[2]
    AVKEY = configurations[6]

    try:
        sentiment_data = []

        for stock in stocks:
            url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={stock}&apikey={AVKEY}'
            r = requests.get(url)
            data_latest = r.json()

            def calculate_weighted_sentiment(data, ticker):
                sentiment_sum = 0.0
                relevance_sum = 0.0
                today = datetime.now()

                for item in data["feed"]:
                    for ticker_sentiment in item["ticker_sentiment"]:
                        if ticker_sentiment["ticker"] == ticker:
                            sentiment = float(ticker_sentiment["ticker_sentiment_score"])
                            relevance = float(ticker_sentiment["relevance_score"])

                            # Calculate time decay factor
                            time_published = datetime.strptime(item["time_published"], "%Y%m%dT%H%M%S")
                            days_since_published = (today - time_published).days
                            decay_factor = pow(0.5, days_since_published / 7.0)  # Half-life of 7 days

                            sentiment_sum += sentiment * relevance * decay_factor
                            relevance_sum += relevance * decay_factor

                if relevance_sum == 0.0:
                    return None

                return sentiment_sum / relevance_sum

            val = calculate_weighted_sentiment(data_latest, stock)
            sentiment_data.append(val)

        return sentiment_data
    except Exception as e:
        print(f"Error occurred: {e}")  # If request fails, return neutral sentiment
        return [0] * len(stocks)


class TreeNode:
    def __init__(self, weight, value, key):
        self.weight = weight
        self.value = value
        self.key = key
        self.height = 1
        self.left = None
        self.right = None


class AVLTree:
    def __init__(self):
        self.root = None

    def _height(self, node):
        if not node:
            return 0
        return node.height

    def _update_height(self, node):
        if node:
            node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node):
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _left_rotate(self, z):
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        self._update_height(z)
        self._update_height(y)
        return y

    def _right_rotate(self, z):
        y = z.left
        T3 = y.right
        y.right = z
        z.left = T3
        self._update_height(z)
        self._update_height(y)
        return y

    def insert(self, root, key, weight, value):
        if not root:
            return TreeNode(weight, value, key)

        if key < root.key:
            root.left = self.insert(root.left, key, weight, value)
        else:
            root.right = self.insert(root.right, key, weight, value)

        self._update_height(root)
        balance = self._balance_factor(root)

        # Left heavy
        if balance > 1:
            if key < root.left.key:
                return self._right_rotate(root)
            else:
                root.left = self._left_rotate(root.left)
                return self._right_rotate(root)

        # Right heavy
        if balance < -1:
            if key > root.right.key:
                return self._left_rotate(root)
            else:
                root.right = self._right_rotate(root.right)
                return self._left_rotate(root)

        return root

    def compute_score(self, root):
        if not root:
            return 0
        left_score = self.compute_score(root.left)
        right_score = self.compute_score(root.right)
        return left_score + root.weight * root.value + right_score


def calculate_position_size(balance, price, volatility, correlation, sentiment):
    # Default values if volatility or sentiment is None
    if volatility is None:
        volatility = 0.5  # Middle ground
    if sentiment is None:
        sentiment = 0  # Neutral sentiment

    # Dynamic Weights
    total_weight = 1
    w_volatility = 0.2 + 0.1 * volatility
    w_correlation = 0.2 - 0.1 * volatility
    w_sentiment = 0.2
    w_balance = 0.2
    w_price = total_weight - (w_volatility + w_correlation + w_sentiment + w_balance)

    # Normalization
    normalized_sentiment = (math.tanh(sentiment) + 1) / 2  # Using tanh for non-linear mapping
    normalized_volatility = volatility
    normalized_correlation = 1 - correlation
    normalized_balance = balance / max(balance, 1)
    normalized_price = price / max(price, 1)

    # Create AVL Tree
    tree = AVLTree()
    tree.root = tree.insert(tree.root, 1, w_volatility, normalized_volatility)
    tree.root = tree.insert(tree.root, 2, w_correlation, normalized_correlation)
    tree.root = tree.insert(tree.root, 3, w_sentiment, normalized_sentiment)
    tree.root = tree.insert(tree.root, 4, w_balance, normalized_balance)
    tree.root = tree.insert(tree.root, 5, w_price, normalized_price)

    # Compute combined score using AVL Tree
    score = tree.compute_score(tree.root)

    # Risk Management
    risk_factor = 0.5 + 0.5 * volatility
    position_size = score * balance * (1 - risk_factor) / price

    # Scaling down
    SCALING_FACTOR = 20  # Adjust based on user preference
    position_size = position_size / SCALING_FACTOR

    # Adjust for Maximum Allocation
    MAX_ALLOCATION = 0.001
    position_size = min(position_size, balance * MAX_ALLOCATION)
    position_size = max(1, position_size)

    return int(position_size)
