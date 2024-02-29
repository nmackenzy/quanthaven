# IMPORTING API
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
# IMPORTING OTHER MODULES
import time
# IMPORTING USER-DEFINED MODULES
from historicalbot.hist_market import check_if_open, sleep
from historicalbot.hist_strategy import Momentum
from historicalbot.hist_strategy2 import SMACrossover
from historicalbot.hist_strategy3 import Breakout
from historicalbot.hist_strategy4 import SVRStrategy
from historicalbot.hist_risk import get_correlation_data, calculate_position_size, get_sentiment_data
from historicalbot.hist_datagrab import calculate_current_price
from historicalbot.hist_config import config


class HistoricalBot:
    def __init__(self, data_queue, stdout_queue):
        self.configurations = config()
        self.in_minutes = self.configurations[7]
        self.data_queue = data_queue
        self.stdout_queue = stdout_queue
        self.API_KEY = self.configurations[4]
        self.API_SECRET_KEY = self.configurations[5]
        self.stocks = self.configurations[2]
        self.strategies = [globals()[name] for name in self.configurations[3]]

        self.trading_client = TradingClient(self.API_KEY, self.API_SECRET_KEY, paper=True)
        self.risk_per_trade = 0.01
        self.min_risk = 0.005
        self.max_risk = 0.02

        self.correlation_list = get_correlation_data()
        self.sentiment_data = get_sentiment_data()
        self.is_running = False

    def start(self):
        self.is_running = True
        while self.is_running:
            if check_if_open():
                start_time = time.time()
                for stock in self.stocks:

                    account_balance = float(self.trading_client.get_account().cash)
                    self.stdout_queue.put(f"Account balance: {int(account_balance)}. ")

                    try:
                        position = self.trading_client.get_open_position(stock)
                        current_holding = position.qty
                    except:
                        current_holding = 0

                    current_price = calculate_current_price(stock)

                    signals = []
                    volatility_for_stock = []
                    correlation_for_stock = self.correlation_list[self.stocks.index(stock)]
                    sentiment_for_stock = self.sentiment_data[self.stocks.index(stock)]

                    for Strategy in self.strategies:
                        strategy_instance = Strategy(stock)
                        validation = strategy_instance.validation()
                        if validation:
                            pass
                        else:
                            self.connection_error()
                            break
                        generated_signal = strategy_instance.generate_signals()
                        data = strategy_instance.extract_data()
                        self.data_queue.put(data)
                        strategy_instance.backtest()
                        if not strategy_instance.test_results()[1] > 0:
                            self.stdout_queue.put(
                                f'Skipping {Strategy.__name__} for {stock} due to negative performance. '
                            )
                            continue
                        signals.append(generated_signal)
                        _, annual_std = strategy_instance.calculate_statistics(self.in_minutes)
                        volatility_for_stock.append(annual_std)
                        results = strategy_instance.extract_results()
                        self.data_queue.put(results)

                    if not signals:
                        self.stdout_queue.put(f"All strategies skipped for stock {stock}. Moving to next stock. ")
                        continue

                    average_volatility = sum(volatility_for_stock) / len(volatility_for_stock)

                    if all(signal == 1 for signal in signals) and int(current_holding) == 0:
                        num_shares = calculate_position_size(account_balance, current_price, average_volatility,
                                                             correlation_for_stock, sentiment_for_stock)
                        market_order_data = MarketOrderRequest(
                            symbol=stock,
                            qty=num_shares,
                            side=OrderSide.BUY,
                            type='market',
                            time_in_force=TimeInForce.GTC,
                        )
                        market_order = self.trading_client.submit_order(
                            order_data=market_order_data
                        )
                        self.stdout_queue.put(f'Placed a buy order for {num_shares} shares of {stock}. ')

                    elif all(signal == -1 for signal in signals) and int(current_holding) > 0:
                        market_order_data = MarketOrderRequest(
                            symbol=stock,
                            qty=current_holding,
                            side=OrderSide.SELL,
                            type='market',
                            time_in_force=TimeInForce.GTC,
                        )
                        market_order = self.trading_client.submit_order(
                            order_data=market_order_data
                        )
                        self.stdout_queue.put(f'Placed a sell order for {current_holding} shares of {stock}. ')

                    else:
                        self.stdout_queue.put("No action. ")
                        pass

                end_time = time.time()
                execution_time = end_time - start_time
                sleep_duration = max(60*self.in_minutes - execution_time, 0)  # Necessary due to the machine learning
                # strategies
                time.sleep(sleep_duration)
            else:
                self.stdout_queue.put("Sleeping till market opens. ")
                sleep()

    def connection_error(self):
        self.stdout_queue.put("Connection error. Please restart the program. ")
        self.is_running = False

    def stop(self):
        self.is_running = False
