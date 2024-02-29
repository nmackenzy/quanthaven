# IMPORTING USER-DEFINED MODULES
from livebot.live_datagrab import request_data
from livebot.live_config import config


def get_correlation_data():
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


class Node:
    def __init__(self, weight, value, next=None):
        self.weight = weight
        self.value = value
        self.next = next


def compute_score(node):
    if not node:
        return 0
    return node.weight * node.value + compute_score(node.next)


def calculate_position_size(balance, price, volatility, correlation):
    # Default value if volatility is None
    if volatility is None:
        volatility = 0.5  # Middle ground

    # Maximum allocation percentage
    MAX_ALLOCATION = 0.001  # Can be adjusted

    # 1. Dynamic Weights
    total_weight = 1
    w_volatility = 0.25 + 0.1 * volatility
    w_correlation = 0.25 - 0.1 * volatility  # The weight will decrease as correlation increases
    w_balance = 0.25
    w_price = total_weight - (w_volatility + w_correlation + w_balance)

    # 2. Normalization and Linked List Creation
    normalized_volatility = volatility
    normalized_correlation = 1 - correlation  # Inverting correlation value so higher correlation reduces score
    normalized_balance = balance / max(balance, 1)
    normalized_price = price / max(price, 1)

    # Creating linked list: Head -> Volatility -> Correlation -> Balance -> Price -> None
    price_node = Node(w_price, normalized_price)
    balance_node = Node(w_balance, normalized_balance, price_node)
    correlation_node = Node(w_correlation, normalized_correlation, balance_node)
    head = Node(w_volatility, normalized_volatility, correlation_node)

    # 3. Compute combined score using recursion
    score = compute_score(head)

    # 4. Risk Management
    risk_factor = 0.5 + 0.5 * volatility
    position_size = score * balance * (1 - risk_factor) / price

    # Scaling down by dividing with a constant
    SCALING_FACTOR = 20  # Adjust based on user preference
    position_size = position_size / SCALING_FACTOR

    # 5. Adjust for Maximum Allocation
    position_size = min(position_size, balance * MAX_ALLOCATION)
    position_size = max(1, position_size)

    return int(position_size)
