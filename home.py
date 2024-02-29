# IMPORTING MODULES
import customtkinter
import yfinance as yf
import datetime
import time
from pytz import timezone
import matplotlib.figure as figure
from matplotlib import font_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
# IMPORTING USER-DEFINED MODULES
from home_datagrab import home_data
from popup import get_news, get_overview
import security

market_open = datetime.time(9, 30, tzinfo=timezone('US/Eastern'))  # 9:30 AM Eastern Time
market_close = datetime.time(16, 0, tzinfo=timezone('US/Eastern'))  # 4:00 PM Eastern Time


class StartPage(customtkinter.CTkFrame):
    def __init__(self, master, user_id):
        customtkinter.CTkFrame.__init__(self, master)
        self.user_id = user_id
        self.entry_used_time = 0
        self.total_seconds = 0

        home = home_data(self.user_id)
        account_balance = home[0]
        total_profit_or_loss = home[1]
        sentiment_values = home[2]
        top_3 = home[3]
        watchlist_stats = home[4]
        watchlist_keys = list(watchlist_stats.keys())

        # Configure grid
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.configure(fg_color="#434343")

        # COLUMN 1

        # Frame 1
        self.frame1 = customtkinter.CTkFrame(self, fg_color="#999999", width=200, height=100)
        self.frame1.grid(row=0, column=0, padx=(20, 10), pady=(20, 0), sticky="nsew")

        self.market = customtkinter.CTkLabel(master=self.frame1,
                                             text="",
                                             font=customtkinter.CTkFont(size=12, weight="bold"))
        self.market.place(relx=0.5, rely=0.25, anchor='center')  # center alignment
        self.status = customtkinter.CTkLabel(master=self.frame1,
                                             text="",
                                             font=customtkinter.CTkFont(size=18, weight="bold"))
        self.status.place(relx=0.5, rely=0.4, anchor='center')  # center alignment
        self.countdown = customtkinter.CTkLabel(master=self.frame1,
                                                text_color="#CCCCCC",
                                                text="",
                                                font=customtkinter.CTkFont(size=38, weight="bold"))
        self.countdown.place(relx=0.5, rely=0.7, anchor='center')  # center alignment
        self.update_time()

        # Frame 2 left
        self.frame2 = customtkinter.CTkFrame(self, fg_color="transparent", width=200, height=100)
        self.frame2.grid(row=1, column=0, padx=(20, 10), pady=(20, 0), sticky="nsew")

        # Frame 2 right
        self.frame2l = customtkinter.CTkFrame(self.frame2, fg_color="#666666", width=100, height=100)
        self.frame2l.place(relx=0, rely=0, relwidth=0.48, relheight=1.0)
        self.top3 = customtkinter.CTkLabel(master=self.frame2l,
                                           text="Top gainers",
                                           font=customtkinter.CTkFont(size=18, weight="bold"))
        self.top3.place(relx=0.5, rely=0.2, anchor='center')
        self.top3_1 = customtkinter.CTkLabel(master=self.frame2l,
                                             text=top_3[0][:-6],
                                             font=customtkinter.CTkFont(size=12, weight="bold"))
        self.top3_1.place(relx=0.3, rely=0.4, anchor='center')
        self.top3_1_s = customtkinter.CTkLabel(master=self.frame2l,
                                               text_color="#B6D7A8",
                                               text=top_3[0][-6:],
                                               font=customtkinter.CTkFont(size=12, weight="bold"))
        self.top3_1_s.place(relx=0.7, rely=0.4, anchor='center')
        self.top3_2 = customtkinter.CTkLabel(master=self.frame2l,
                                             text=top_3[1][:-6],
                                             font=customtkinter.CTkFont(size=12, weight="bold"))
        self.top3_2.place(relx=0.3, rely=0.6, anchor='center')
        self.top3_2_s = customtkinter.CTkLabel(master=self.frame2l,
                                               text_color="#B6D7A8",
                                               text=top_3[1][-6:],
                                               font=customtkinter.CTkFont(size=12, weight="bold"))
        self.top3_2_s.place(relx=0.7, rely=0.6, anchor='center')
        self.top3_3 = customtkinter.CTkLabel(master=self.frame2l,
                                             text=top_3[2][:-6],
                                             font=customtkinter.CTkFont(size=12, weight="bold"))
        self.top3_3.place(relx=0.3, rely=0.8, anchor='center')
        self.top3_3_s = customtkinter.CTkLabel(master=self.frame2l,
                                               text_color="#B6D7A8",
                                               text=top_3[2][-6:],
                                               font=customtkinter.CTkFont(size=12, weight="bold"))
        self.top3_3_s.place(relx=0.7, rely=0.8, anchor='center')

        self.frame2r = customtkinter.CTkFrame(self.frame2, fg_color="#666666", width=100, height=100)
        self.frame2r.place(relx=0.52, rely=0, relwidth=0.48, relheight=1.0)
        self.watchlist = customtkinter.CTkLabel(master=self.frame2r,
                                                text="Watchlist",
                                                font=customtkinter.CTkFont(size=18, weight="bold"))
        self.watchlist.place(relx=0.5, rely=0.2, anchor='center')
        self.spy = customtkinter.CTkLabel(master=self.frame2r,
                                          text=f"{watchlist_keys[0]}:",
                                          font=customtkinter.CTkFont(size=12, weight="bold"))
        self.spy.place(relx=0.3, rely=0.4, anchor='center')
        self.spy_s = customtkinter.CTkLabel(master=self.frame2r,
                                            text_color=self.define_colour(watchlist_stats[watchlist_keys[0]]),
                                            text=self.format_watchlist(watchlist_stats[watchlist_keys[0]]),
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.spy_s.place(relx=0.7, rely=0.4, anchor='center')
        self.qqq = customtkinter.CTkLabel(master=self.frame2r,
                                          text=f"{watchlist_keys[1]}:",
                                          font=customtkinter.CTkFont(size=12, weight="bold"))
        self.qqq.place(relx=0.3, rely=0.6, anchor='center')
        self.qqq_s = customtkinter.CTkLabel(master=self.frame2r,
                                            text_color=self.define_colour(watchlist_stats[watchlist_keys[1]]),
                                            text=self.format_watchlist(watchlist_stats[watchlist_keys[1]]),
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.qqq_s.place(relx=0.7, rely=0.6, anchor='center')
        self.dia = customtkinter.CTkLabel(master=self.frame2r,
                                          text=f"{watchlist_keys[2]}:",
                                          font=customtkinter.CTkFont(size=12, weight="bold"))
        self.dia.place(relx=0.3, rely=0.8, anchor='center')
        self.dia_s = customtkinter.CTkLabel(master=self.frame2r,
                                            text_color=self.define_colour(watchlist_stats[watchlist_keys[2]]),
                                            text=self.format_watchlist(watchlist_stats[watchlist_keys[2]]),
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.dia_s.place(relx=0.7, rely=0.8, anchor='center')

        # Frame 3
        self.frame3 = customtkinter.CTkFrame(self, fg_color="#999999", width=200, height=200)
        self.frame3.grid(row=2, column=0, rowspan=2, padx=(20, 10), pady=(20, 20), sticky="nsew")

        sp500 = yf.download(tickers="SPY", period="5y", interval="1d")
        close = sp500['Close']

        # Create FontProperties object for title
        title_font_prop = font_manager.FontProperties(weight='bold', size=14, family='Roboto')
        # Create FontProperties object for labels
        label_font_prop = font_manager.FontProperties(weight='bold', size=8, family='Roboto')

        fig = figure.Figure(figsize=(4, 2), dpi=100)
        fig.set_facecolor("#999999")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#999999")
        ax.plot_date(close.index, close, linestyle='-', marker=None, linewidth=1, color='white')
        ax.grid(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Set title with bold text
        ax.set_title('S&P 500', color='white', fontproperties=title_font_prop)

        ax.tick_params(colors='white')
        for label in ax.get_xticklabels():
            label.set_fontproperties(label_font_prop)
        for label in ax.get_yticklabels():
            label.set_fontproperties(label_font_prop)

        canvas = FigureCanvasTkAgg(fig, master=self.frame3)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.55, rely=0.5, anchor='center')

        # COLUMN 2

        # Frame 4
        self.frame4 = customtkinter.CTkFrame(self, fg_color="#666666", width=200, height=100)
        self.frame4.grid(row=0, column=1, padx=(10, 20), pady=(20, 0), sticky="nsew")

        self.welcome = customtkinter.CTkLabel(master=self.frame4,
                                              text=f"Welcome, {self.get_name(user_id).title()}",
                                              font=customtkinter.CTkFont(size=18, weight="bold"))
        self.welcome.place(relx=0.5, rely=0.25, anchor='center')
        self.balance = customtkinter.CTkLabel(master=self.frame4,
                                              text="Account balance:",
                                              font=customtkinter.CTkFont(size=18, weight="bold"))
        self.balance.place(relx=0.3, rely=0.5, anchor='center')
        self.balance = customtkinter.CTkLabel(master=self.frame4,
                                              text_color="#B7B7B7",
                                              text=f"${(int(account_balance))}",
                                              font=customtkinter.CTkFont(size=18, weight="bold"))
        self.balance.place(relx=0.7, rely=0.5, anchor='center')
        self.profitloss = customtkinter.CTkLabel(master=self.frame4,
                                                 text="Total profit/loss:",
                                                 font=customtkinter.CTkFont(size=18, weight="bold"))
        self.profitloss.place(relx=0.3, rely=0.75, anchor='center')
        self.profitloss = customtkinter.CTkLabel(master=self.frame4,
                                                 text_color=self.define_colour(int(total_profit_or_loss)),
                                                 text=self.format_profitloss(int(total_profit_or_loss)),
                                                 font=customtkinter.CTkFont(size=18, weight="bold"))
        self.profitloss.place(relx=0.7, rely=0.75, anchor='center')

        # Frame 5
        self.frame5 = customtkinter.CTkFrame(self, fg_color="#999999", width=200, height=200)
        self.frame5.grid(row=1, column=1, rowspan=2, padx=(10, 20), pady=(20, 0), sticky="nsew")

        self.sentiment = customtkinter.CTkLabel(master=self.frame5,
                                                text="Sector sentiment",
                                                font=customtkinter.CTkFont(size=18, weight="bold"))
        self.sentiment.place(relx=0.5, rely=0.125, anchor='center')
        self.technology = customtkinter.CTkLabel(master=self.frame5,
                                                 text="Technology:",
                                                 font=customtkinter.CTkFont(size=12, weight="bold"))
        self.technology.place(relx=0.4, rely=0.25, anchor='center')
        self.technology_s = customtkinter.CTkLabel(master=self.frame5,
                                                   text=str(sentiment_values[5]),
                                                   text_color="#CCCCCC",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"))
        self.technology_s.place(relx=0.8, rely=0.25, anchor='center')
        self.energy_transportation = customtkinter.CTkLabel(master=self.frame5,
                                                            text="Energy & Transportation:",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.energy_transportation.place(relx=0.4, rely=0.375, anchor='center')
        self.energy_transportation_s = customtkinter.CTkLabel(master=self.frame5,
                                                              text=str(sentiment_values[0]),
                                                              text_color="#CCCCCC",
                                                              font=customtkinter.CTkFont(size=12, weight="bold"))
        self.energy_transportation_s.place(relx=0.8, rely=0.375, anchor='center')
        self.manufacturing = customtkinter.CTkLabel(master=self.frame5,
                                                    text="Manufacturing:",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        self.manufacturing.place(relx=0.4, rely=0.5, anchor='center')
        self.manufacturing_s = customtkinter.CTkLabel(master=self.frame5,
                                                      text=str(sentiment_values[1]),
                                                      text_color="#CCCCCC",
                                                      font=customtkinter.CTkFont(size=12, weight="bold"))
        self.manufacturing_s.place(relx=0.8, rely=0.5, anchor='center')
        self.life_sciences = customtkinter.CTkLabel(master=self.frame5,
                                                    text="Life Sciences:",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        self.life_sciences.place(relx=0.4, rely=0.625, anchor='center')
        self.life_sciences_s = customtkinter.CTkLabel(master=self.frame5,
                                                      text=str(sentiment_values[2]),
                                                      text_color="#CCCCCC",
                                                      font=customtkinter.CTkFont(size=12, weight="bold"))
        self.life_sciences_s.place(relx=0.8, rely=0.625, anchor='center')
        self.real_estate = customtkinter.CTkLabel(master=self.frame5,
                                                  text="Real Estate & Construction:",
                                                  font=customtkinter.CTkFont(size=12, weight="bold"))
        self.real_estate.place(relx=0.4, rely=0.75, anchor='center')
        self.real_estate_s = customtkinter.CTkLabel(master=self.frame5,
                                                    text=str(sentiment_values[3]),
                                                    text_color="#CCCCCC",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        self.real_estate_s.place(relx=0.8, rely=0.75, anchor='center')
        self.retail_wholesale = customtkinter.CTkLabel(master=self.frame5,
                                                       text="Retail & Wholesale:",
                                                       font=customtkinter.CTkFont(size=12, weight="bold"))
        self.retail_wholesale.place(relx=0.4, rely=0.875, anchor='center')
        self.retail_wholesale_s = customtkinter.CTkLabel(master=self.frame5,
                                                         text=str(sentiment_values[4]),
                                                         text_color="#CCCCCC",
                                                         font=customtkinter.CTkFont(size=12, weight="bold"))
        self.retail_wholesale_s.place(relx=0.8, rely=0.875, anchor='center')

        # Frame 6
        self.frame6 = customtkinter.CTkFrame(self, fg_color="#666666", width=200, height=50)
        self.frame6.grid(row=3, column=1, padx=(10, 20), pady=(20, 20), sticky="nsew")

        self.label1 = customtkinter.CTkLabel(master=self.frame6,
                                             text="Choose a stock to analyse:",
                                             font=customtkinter.CTkFont(size=22, weight="bold"))
        self.label1.place(relx=0.5, rely=0.3, anchor='center')
        self.entry = customtkinter.CTkEntry(master=self.frame6,
                                            placeholder_text="Symbol",
                                            font=customtkinter.CTkFont(size=12, weight="bold"), height=30,
                                            corner_radius=15)
        self.entry.place(relx=0.25, rely=0.7, anchor='center')
        self.main_button_1 = customtkinter.CTkButton(master=self.frame6,
                                                     text="Submit",
                                                     fg_color="transparent",
                                                     border_width=2,
                                                     font=customtkinter.CTkFont(size=12, weight="bold"),
                                                     height=30, corner_radius=15, command=self.submit)
        self.main_button_1.place(relx=0.75, rely=0.7, anchor='center')

        self.input_value = None

    def get_name(self, user_id):
        # Connect to the SQLite database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Execute the query
        c.execute("SELECT name FROM details WHERE user_id = ?", (user_id,))
        # Fetch the result
        result = c.fetchone()
        # Close the connection
        conn.close()
        # If a result was found, return the name; otherwise, return None
        if result:
            return result[0]
        else:
            return None

    def update_time(self):
        now = datetime.datetime.now(timezone('US/Eastern'))
        current_day = now.weekday()  # Monday is 0 and Sunday is 6

        # If we hit 0 or the state is not initialized, we need to recalculate
        if self.total_seconds <= 0:
            if current_day > 4:  # Saturday or Sunday
                market = "Market is closed"
                status = "Time till market opens:"
                days_till_monday = 1 if current_day == 6 else 2
                next_open = datetime.datetime.combine(
                    now.date() + datetime.timedelta(days=days_till_monday), market_open
                )
                self.total_seconds = int((next_open - now).total_seconds())
            else:
                if now.time() >= market_open and now.time() <= market_close:
                    market = "Market is open"
                    status = "Time till market closes:"
                    self.total_seconds = int(
                        (datetime.datetime.combine(now.date(), market_close) - now).total_seconds()
                    )
                else:
                    market = "Market is closed"
                    status = "Time till market opens:"
                    if now.time() > market_close:
                        next_day = now + datetime.timedelta(days=1)
                        next_open = datetime.datetime.combine(next_day.date(), market_open)
                        self.total_seconds = int((next_open - now).total_seconds())
                    else:
                        self.total_seconds = int(
                            (datetime.datetime.combine(now.date(), market_open) - now).total_seconds()
                        )

            self.market.configure(text=market)
            self.status.configure(text=status)

        # Reduce the total_seconds by 1 for each call
        self.total_seconds -= 1

        hours, remainder = divmod(self.total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

        self.countdown.configure(text=countdown)

        # Always reschedule every second since we're counting down
        self.after(1000, self.update_time)

    def define_colour(self, num):
        if num >= 0:
            colour = "#B6D7A8"  # Green
        elif num < 0:
            colour = "#EA9999"  # Red
        else:
            colour = "#EA58F9"  # Magenta
        return colour

    def format_watchlist(self, value):
        if value >= 0:
            formatted = f" + {value}%"
        elif value < 0:
            formatted = f" - {str(value)[1:]}%"
        else:
            formatted = "Error"
        return formatted

    def format_profitloss(self, value):
        if value >= 0:
            formatted = f" + ${value}"
        elif value < 0:
            formatted = f" - ${str(value)[1:]}"
        else:
            formatted = "Error"
        return formatted

    def validate_input(self):
        try:
            data = yf.Ticker(self.input_value).history(period='1d')  # Get recent 1-day trading data
            if data.empty:
                return False
            else:
                return True
        except Exception as e:
            print(f"Exception occurred: {e}")
            return False

    def submit(self):
        current_time = time.time()

        if current_time - self.entry_used_time >= 60:
            self.input_value = self.entry.get().upper()
            if self.validate_input():
                self.entry_used_time = current_time  # Update entry_used_time when a new window is opened
                self.open_new_window()
            else:
                self.open_error_window()
        else:
            print("Rate Limit:", "Please wait for a minute before making another API call.")
            self.open_rate_limit_window()

    def open_rate_limit_window(self):
        self.entry.delete(0, customtkinter.END)
        rate_limit_window = customtkinter.CTkToplevel(self)
        rate_limit_window.title("Login")
        screen_width = 1440
        screen_height = 900
        window_width = 300
        window_height = 200
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        rate_limit_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        rate_limit_window.resizable(False, False)
        rate_limit_window.configure(fg_color="#434343")
        customtkinter.CTkLabel(rate_limit_window,
                               text="Error: Rate Limit",
                               font=customtkinter.CTkFont(size=22, weight="bold")).place(relx=0.5,
                                                                                         rely=0.2,
                                                                                         anchor='center')
        customtkinter.CTkLabel(rate_limit_window,
                               text_color="#CCCCCC",
                               text="Please wait for a minute before making another API call",
                               font=customtkinter.CTkFont(size=14, weight="bold"),
                               wraplength=200).place(relx=0.5, rely=0.4, anchor='center')
        customtkinter.CTkButton(rate_limit_window,
                                text="Close",
                                fg_color="transparent",
                                border_width=2,
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                height=30,
                                corner_radius=15,
                                command=rate_limit_window.destroy).place(relx=0.5, rely=0.7, anchor='center')

    def open_error_window(self):
        self.entry.delete(0, customtkinter.END)
        error_window = customtkinter.CTkToplevel(self)
        error_window.title("Login")
        screen_width = 1440
        screen_height = 900
        window_width = 300
        window_height = 200
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        error_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        error_window.resizable(False, False)
        error_window.configure(fg_color="#434343")
        customtkinter.CTkLabel(error_window,
                               text="Error: Invalid Input",
                               font=customtkinter.CTkFont(size=22, weight="bold")).place(relx=0.5,
                                                                                         rely=0.3,
                                                                                         anchor='center')
        customtkinter.CTkLabel(error_window,
                               text_color="#CCCCCC",
                               text="You need to enter a valid ticker symbol for analysis",
                               font=customtkinter.CTkFont(size=14, weight="bold"),
                               wraplength=200).place(relx=0.5, rely=0.45, anchor='center')
        customtkinter.CTkButton(error_window,
                                text="Close",
                                fg_color="transparent",
                                border_width=2,
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                height=30,
                                corner_radius=15,
                                command=error_window.destroy).place(relx=0.5, rely=0.7, anchor='center')

    def open_new_window(self):
        print("window button pressed")

        new_window = customtkinter.CTkToplevel(self)

        new_window.title("♜ QuantHaven")
        screen_width = 1440
        screen_height = 900
        window_width = 820
        window_height = 580
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        new_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        new_window.resizable(False, False)

        symbol = self.input_value
        self.entry.delete(0, customtkinter.END)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT av_key FROM details WHERE user_id=?", (self.user_id,))
        record = c.fetchone()
        c.close()
        conn.close()
        AVKEY = security.decrypt_data(record[0], str(self.user_id) + 'C')
        overview = get_overview(symbol, AVKEY)
        news = get_news(symbol, AVKEY)

        # Configure grid
        new_window.grid_columnconfigure((0, 1), weight=1)
        new_window.grid_rowconfigure((0, 1, 2, 3), weight=1)
        new_window.configure(fg_color="#434343")

        # COLUMN 1

        # Frame 1
        new_window.frame1 = customtkinter.CTkFrame(new_window, fg_color="#666666", width=200, height=100)
        new_window.frame1.grid(row=0, column=0, padx=(20, 10), pady=(20, 0), sticky="nsew")

        new_window.symbol_l = customtkinter.CTkLabel(master=new_window.frame1,
                                                     text="Symbol:  ",
                                                     font=customtkinter.CTkFont(size=28, weight="bold"))
        new_window.symbol = customtkinter.CTkLabel(master=new_window.frame1,
                                                   text=symbol,
                                                   text_color="#B7B7B7",
                                                   font=customtkinter.CTkFont(size=28, weight="bold"))
        new_window.name_l = customtkinter.CTkLabel(master=new_window.frame1,
                                                   text="Name:  ",
                                                   font=customtkinter.CTkFont(size=18, weight="bold"))
        new_window.name = customtkinter.CTkLabel(master=new_window.frame1,
                                                 text=overview[0],
                                                 text_color="#B7B7B7",
                                                 font=customtkinter.CTkFont(size=18, weight="bold"),
                                                 wraplength=200)

        def place_labels():
            new_window.frame1.update_idletasks()
            center_point = (new_window.frame1.winfo_width() / 2) - 60
            total_width = new_window.symbol_l.winfo_reqwidth() + new_window.symbol.winfo_reqwidth()
            total_width_2 = new_window.name_l.winfo_reqwidth() + new_window.name.winfo_reqwidth()
            start_x1 = center_point - total_width / 2
            start_x2 = start_x1 + new_window.symbol_l.winfo_reqwidth()
            start_x1_2 = center_point - total_width_2 / 2
            start_x2_2 = start_x1_2 + new_window.name_l.winfo_reqwidth()
            new_window.name_l.place(x=start_x1_2, rely=0.2)  # adjust y as needed
            new_window.name.place(x=start_x2_2, rely=0.2)
            new_window.symbol_l.place(x=start_x1, rely=0.5)
            new_window.symbol.place(x=start_x2, rely=0.5)

        place_labels()

        # Frame 2
        new_window.frame2 = customtkinter.CTkFrame(new_window, fg_color="transparent", width=200, height=100)
        new_window.frame2.grid(row=1, column=0, padx=(20, 10), pady=(20, 0), sticky="nsew")

        def get_current_price(s):
            stock = yf.Ticker(s)
            hist = stock.history(period="1d")
            current_price = round(hist['Close'][0], 2)
            return current_price

        # Frame 2 left
        new_window.frame2l = customtkinter.CTkFrame(new_window.frame2, fg_color="#999999", width=100, height=100)
        new_window.frame2l.place(relx=0, rely=0, relwidth=0.48, relheight=1.0)
        new_window.close = customtkinter.CTkLabel(master=new_window.frame2l,
                                                  text="Close prices",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"))
        new_window.close.place(relx=0.5, rely=0.2, anchor='center')
        new_window.currentprice_l = customtkinter.CTkLabel(master=new_window.frame2l,
                                                           text="Current:",
                                                           font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.currentprice_l.place(relx=0.3, rely=0.4, anchor='center')
        new_window.currentprice = customtkinter.CTkLabel(master=new_window.frame2l,
                                                         text=str(get_current_price(symbol)),
                                                         text_color="#CCCCCC",
                                                         font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.currentprice.place(relx=0.7, rely=0.4, anchor='center')
        new_window.MA50_l = customtkinter.CTkLabel(master=new_window.frame2l,
                                                   text="50DMA:",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.MA50_l.place(relx=0.3, rely=0.6, anchor='center')
        new_window.MA50 = customtkinter.CTkLabel(master=new_window.frame2l,
                                                 text=overview[11],
                                                 text_color="#CCCCCC",
                                                 font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.MA50.place(relx=0.7, rely=0.6, anchor='center')
        new_window.MA200_l = customtkinter.CTkLabel(master=new_window.frame2l,
                                                    text="200DMA",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.MA200_l.place(relx=0.3, rely=0.8, anchor='center')
        new_window.MA200 = customtkinter.CTkLabel(master=new_window.frame2l,
                                                  text=overview[12],
                                                  text_color="#CCCCCC",
                                                  font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.MA200.place(relx=0.7, rely=0.8, anchor='center')

        # Frame 2 right
        new_window.frame2r = customtkinter.CTkFrame(new_window.frame2, fg_color="#999999", width=100, height=100)
        new_window.frame2r.place(relx=0.52, rely=0, relwidth=0.48, relheight=1.0)
        new_window.about = customtkinter.CTkLabel(master=new_window.frame2r,
                                                  text="About:",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"))
        new_window.about.place(relx=0.5, rely=0.2, anchor='center')
        new_window.exchange_l = customtkinter.CTkLabel(master=new_window.frame2r,
                                                       text="Exchange:",
                                                       font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.exchange_l.place(relx=0.3, rely=0.4, anchor='center')
        new_window.exchange = customtkinter.CTkLabel(master=new_window.frame2r,
                                                     text=overview[2],
                                                     text_color="#CCCCCC",
                                                     font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.exchange.place(relx=0.7, rely=0.4, anchor='center')
        new_window.currency_l = customtkinter.CTkLabel(master=new_window.frame2r,
                                                       text="Currency",
                                                       font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.currency_l.place(relx=0.3, rely=0.6, anchor='center')
        new_window.currency = customtkinter.CTkLabel(master=new_window.frame2r,
                                                     text=overview[3],
                                                     text_color="#CCCCCC",
                                                     font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.currency.place(relx=0.7, rely=0.6, anchor='center')
        new_window.country_l = customtkinter.CTkLabel(master=new_window.frame2r,
                                                      text="Country:",
                                                      font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.country_l.place(relx=0.3, rely=0.8, anchor='center')
        new_window.country = customtkinter.CTkLabel(master=new_window.frame2r,
                                                    text=overview[4],
                                                    text_color="#CCCCCC",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.country.place(relx=0.7, rely=0.8, anchor='center')

        # Frame 3
        new_window.frame3 = customtkinter.CTkFrame(new_window, fg_color="#666666", width=200, height=200)
        new_window.frame3.grid(row=2, column=0, rowspan=2, padx=(20, 10), pady=(20, 20), sticky="nsew")

        data = yf.download(tickers=symbol, period="5y", interval="1d")
        close = data['Close']

        title_font_prop = font_manager.FontProperties(weight='bold', size=14, family='Roboto')
        label_font_prop = font_manager.FontProperties(weight='bold', size=8, family='Roboto')

        fig = figure.Figure(figsize=(4, 2), dpi=100)
        fig.set_facecolor("#666666")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#666666")
        ax.plot_date(close.index, close, linestyle='-', marker=None, linewidth=1, color='white')
        ax.grid(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)

        ax.set_title('Historical Close Price', color='white', fontproperties=title_font_prop)

        ax.tick_params(colors='white')
        for label in ax.get_xticklabels():
            label.set_fontproperties(label_font_prop)
        for label in ax.get_yticklabels():
            label.set_fontproperties(label_font_prop)

        canvas = FigureCanvasTkAgg(fig, master=new_window.frame3)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.55, rely=0.5, anchor='center')

        # COLUMN 2

        # Frame 4
        new_window.textbox1 = customtkinter.CTkTextbox(new_window, fg_color="#000000", width=200, height=100)
        new_window.textbox1.grid(row=0, column=1, padx=(10, 20), pady=(20, 0), sticky="nsew")
        new_window.textbox1.insert(
            "0.0", "COMPANY OVERVIEW\n\n" + f"Sector: {overview[5].title()}\n\n" + f"Description: {overview[1]}"
        )
        new_window.textbox1.configure(state="disabled")

        # Frame 5
        new_window.textbox2 = customtkinter.CTkTextbox(new_window, fg_color="#000000", width=200, height=150)
        new_window.textbox2.grid(row=1, column=1, rowspan=2, padx=(10, 20), pady=(20, 0), sticky="nsew")
        new_window.textbox2.insert(
            "0.0",
            "NEWS\n\n" +
            f"Title: {news[0].title()}\n" +
            f"Source: {news[1]}\n" +
            f"Date Published: {news[2]}\n\n" +
            f"Title: {news[3].title()}\n" +
            f"Source: {news[4]}\n" +
            f"Date Published: {news[5]}\n\n" +
            f"Title: {news[6].title()}\n" +
            f"Source: {news[7]}\n" +
            f"Date Published: {news[8]}\n\n" +
            f"Title: {news[9].title()}\n" +
            f"Source: {news[10]}\n" +
            f"Date Published: {news[11]}\n\n" +
            f"Title: {news[12].title()}\n" +
            f"Source: {news[13]}\n" +
            f"Date Published: {news[14]}"
        )
        new_window.textbox2.configure(state="disabled")

        # Frame 6
        new_window.frame6 = customtkinter.CTkFrame(new_window, fg_color="transparent", width=200, height=100)
        new_window.frame6.grid(row=3, column=1, padx=(10, 20), pady=(20, 20), sticky="nsew")

        padding = 0.1
        scale_factor = (1 - 2 * padding) / 6

        # Frame 6 left
        new_window.frame6l = customtkinter.CTkFrame(new_window.frame6, fg_color="#999999", width=100, height=100)
        new_window.frame6l.place(relx=0, rely=0, relwidth=0.48, relheight=1.0)

        new_window.eps_l = customtkinter.CTkLabel(master=new_window.frame6l,
                                                  text="EPS:",
                                                  font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.eps_l.place(relx=0.5, rely=padding + scale_factor * 0.5, anchor='center')
        new_window.eps = customtkinter.CTkLabel(master=new_window.frame6l,
                                                text=overview[8],
                                                text_color="#CCCCCC",
                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.eps.place(relx=0.5, rely=padding + scale_factor * 1.5, anchor='center')
        new_window.pe_ratio_l = customtkinter.CTkLabel(master=new_window.frame6l,
                                                       text="PE Ratio:",
                                                       font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.pe_ratio_l.place(relx=0.5, rely=padding + scale_factor * 2.5, anchor='center')
        new_window.pe_ratio = customtkinter.CTkLabel(master=new_window.frame6l,
                                                     text=overview[7],
                                                     text_color="#CCCCCC",
                                                     font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.pe_ratio.place(relx=0.5, rely=padding + scale_factor * 3.5, anchor='center')
        new_window.beta_l = customtkinter.CTkLabel(master=new_window.frame6l,
                                                   text="Beta:",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.beta_l.place(relx=0.5, rely=padding + scale_factor * 4.5, anchor='center')
        new_window.beta = customtkinter.CTkLabel(master=new_window.frame6l,
                                                 text=overview[10],
                                                 text_color="#CCCCCC",
                                                 font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.beta.place(relx=0.5, rely=padding + scale_factor * 5.5, anchor='center')

        #  Frame 6 right
        new_window.frame6r = customtkinter.CTkFrame(new_window.frame6, fg_color="#999999", width=100, height=100)
        new_window.frame6r.place(relx=0.52, rely=0, relwidth=0.48, relheight=1.0)

        new_window.shares_outstanding_l = customtkinter.CTkLabel(master=new_window.frame6r,
                                                                 text="Shares Outstanding:",
                                                                 font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.shares_outstanding_l.place(relx=0.5, rely=padding + scale_factor * 0.5, anchor='center')
        new_window.shares_outstanding = customtkinter.CTkLabel(master=new_window.frame6r,
                                                               text=overview[13],
                                                               text_color="#CCCCCC",
                                                               font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.shares_outstanding.place(relx=0.5, rely=padding + scale_factor * 1.5, anchor='center')
        new_window.market_capitalisation_l = customtkinter.CTkLabel(master=new_window.frame6r,
                                                                    text="Market Capitalisation:",
                                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.market_capitalisation_l.place(relx=0.5, rely=padding + scale_factor * 2.5, anchor='center')
        new_window.market_capitalisation = customtkinter.CTkLabel(master=new_window.frame6r,
                                                                  text=overview[6],
                                                                  text_color="#CCCCCC",
                                                                  font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.market_capitalisation.place(relx=0.5, rely=padding + scale_factor * 3.5, anchor='center')
        new_window.profit_margin_l = customtkinter.CTkLabel(master=new_window.frame6r,
                                                            text="Profit Margin:",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.profit_margin_l.place(relx=0.5, rely=padding + scale_factor * 4.5, anchor='center')
        new_window.profit_margin = customtkinter.CTkLabel(master=new_window.frame6r,
                                                          text=overview[9],
                                                          text_color="#CCCCCC",
                                                          font=customtkinter.CTkFont(size=12, weight="bold"))
        new_window.profit_margin.place(relx=0.5, rely=padding + scale_factor * 5.5, anchor='center')
