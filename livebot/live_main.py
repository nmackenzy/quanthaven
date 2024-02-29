# IMPORTING API
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
# IMPORTING OTHER MODULES
import queue
import threading
import json
import websocket
import time
import traceback
# IMPORTING USER-DEFINED MODULES
from livebot.live_market import check_if_open, sleep
from livebot.live_strategy import Momentum
from livebot.live_strategy2 import Scalping
from livebot.live_strategy3 import MeanReversion
from livebot.live_datagrab import request_data
from livebot.live_risk import get_correlation_data, calculate_position_size
from livebot.live_config import config


class LiveBot:
    def __init__(self, data_queue, stdout_queue):
        self.configurations = config()
        self.data_queue = data_queue
        self.stdout_queue = stdout_queue
        self.in_minutes = self.configurations[7]
        self.API_KEY = self.configurations[4]
        self.API_SECRET_KEY = self.configurations[5]
        self.stocks = self.configurations[2]
        self.strategies = [globals()[name] for name in self.configurations[3]]
        self.trading_client = TradingClient(self.API_KEY, self.API_SECRET_KEY, paper=True)
        self.risk_per_trade = 0.01
        self.min_risk = 0.005
        self.max_risk = 0.02
        self.reconnection_attempts = 0
        self.MAX_RECONNECTION_ATTEMPTS = 5
        self.correlation_list = get_correlation_data()
        self.data = request_data(self.stocks)
        self.message_count = 0
        self.x = self.configurations[6]
        self.is_running = False
        self.start_event = threading.Event()
        self.message_queue = queue.Queue()

    def action(self, stock, current_price):
        account_balance = float(self.trading_client.get_account().cash)
        self.stdout_queue.put(f"Account balance: {int(account_balance)}. ")

        try:
            position = self.trading_client.get_open_position(stock)
            current_holding = position.qty
        except:
            current_holding = 0

        signals = []
        volatility_for_stock = []
        correlation_for_stock = self.correlation_list[self.stocks.index(stock)]

        for Strategy in self.strategies:
            strategy_instance = Strategy(stock, self.data)
            generated_signal = strategy_instance.generate_signals()
            data = strategy_instance.extract_data()
            self.data_queue.put(data)
            strategy_instance.backtest()
            if not strategy_instance.test_results()[1] > 0:
                self.stdout_queue.put(f'Skipping {Strategy.__name__} for {stock} due to negative performance. ')
                continue
            signals.append(generated_signal)
            _, annual_std = strategy_instance.calculate_statistics(self.in_minutes)
            volatility_for_stock.append(annual_std)
            results = strategy_instance.extract_results()
            self.data_queue.put(results)

        if signals:
            average_volatility = sum(volatility_for_stock) / len(volatility_for_stock)

            if all(signal == 1 for signal in signals) and int(current_holding) == 0:
                num_shares = calculate_position_size(account_balance, current_price, average_volatility,
                                                     correlation_for_stock)
                market_order_data = MarketOrderRequest(
                    symbol=stock,
                    qty=num_shares,
                    side=OrderSide.BUY,
                    type='market',
                    time_in_force=TimeInForce.IOC,
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
                    time_in_force=TimeInForce.IOC,
                )
                market_order = self.trading_client.submit_order(
                    order_data=market_order_data
                )
                self.stdout_queue.put(f'Placed a sell order for {current_holding} shares of {stock}. ')
        else:
            self.stdout_queue.put("No action. ")
            pass

    def update_rolling(self, symbol, new_value):
        try:
            if self.data.index.dtype == 'int64':
                self.data.loc[self.data.index[-1] + 1] = self.data.iloc[-1]
            else:
                self.data.loc[self.data.index[-1]] = self.data.iloc[-1]
            # Update the new last row's specified column with the new value
            self.data.at[self.data.index[-1], symbol] = new_value
            # Drop the first row
            self.data.drop(self.data.index[0], inplace=True)
            # Reset index, so it remains sequential
            self.data.reset_index(drop=True, inplace=True)
        except Exception as e:
            print(f"Error in update_rolling: {e}")
            traceback.print_exc()

    def bot_message_processor(self):
        self.start_event.wait()
        try:
            print("Message processor started and waiting for messages... ")
            while self.is_running:
                message = self.message_queue.get()
                print("Processing a new message... ")
                msg = json.loads(message)
                # Ensure the message is a list and has at least one item
                if isinstance(msg, list) and len(msg) > 0 and "S" in msg[0]:
                    symbol = msg[0]["S"]
                    close = [msg[0]["c"]]
                    self.update_rolling(symbol, close[0])
                    self.action(symbol, close[0])
                else:
                    print(f"Ignoring message: {msg} ")

                self.message_queue.task_done()  # Mark the task as done after processing

        except Exception as e:
            print(f"Exception in message_processor: {e}")
            traceback.print_exc()

    def on_open(self, ws):
        self.reconnection_attempts = 0
        print("Opened connection")
        auth_data = {"action": "auth", "key": self.API_KEY, "secret": self.API_SECRET_KEY}
        ws.send(json.dumps(auth_data))
        listen_message = {"action": "subscribe", "bars": self.stocks}
        ws.send(json.dumps(listen_message))

    def on_message(self, ws, message):
        print("Received a message")
        print(message)
        self.message_count += 1
        if self.message_count % self.x == 0:
            self.message_queue.put(message)
            print(f"Queued message: {message[:100]}...")  # Print the first 100 characters of the message for brevity
            print("Is the processor thread alive?", self.processor_thread.is_alive())

    def on_close(self, ws):
        print("Closed connection")

    def on_error(self, ws, error):
        print("Error", error)
        # Check if max attempts reached
        if self.reconnection_attempts >= self.MAX_RECONNECTION_ATTEMPTS:
            print(f"Reached max reconnection attempts ({self.MAX_RECONNECTION_ATTEMPTS}). Not reconnecting.")
            self.stdout_queue.put("Connection error. Please restart the program. ")
            self.stop()
            return

        # If not, attempt to reconnect
        time.sleep(5)  # Wait for 5 seconds before attempting to reconnect
        self.reconnection_attempts += 1  # Increment the counter
        print(f"Reconnection attempt {self.reconnection_attempts} of {self.MAX_RECONNECTION_ATTEMPTS}")
        self.start_socket()  # Try to restart the connection

    def start_socket(self):
        socket = "wss://stream.data.alpaca.markets/v2/iex"
        self.ws = websocket.WebSocketApp(socket, on_open=self.on_open, on_message=self.on_message,
                                         on_close=self.on_close, on_error=self.on_error)
        self.ws.run_forever()

    def start(self):
        self.is_running = True
        while self.is_running:
            if check_if_open():
                self.processor_thread = threading.Thread(target=self.bot_message_processor)
                self.processor_thread.start()
                self.start_event.set()  # Signal the processor thread to start processing
                self.start_socket()  # Open the connection
            else:
                self.stdout_queue.put("Sleeping till market opens. ")
                sleep()

    def stop(self):
        self.is_running = False
        if hasattr(self, 'ws') and self.ws:
            self.ws.close()
        if hasattr(self, 'processor_thread') and self.processor_thread.is_alive():
            self.start_event.clear()  # Signal the processor thread to stop processing
            self.processor_thread.join()
