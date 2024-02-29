from tkinter import ttk
import time
import customtkinter
import sqlite3
import yfinance as yf


class PageOne(customtkinter.CTkFrame):
    def __init__(self, master, task, user_id, controller=None):
        customtkinter.CTkFrame.__init__(self, master)
        self.controller = controller
        self.task = task
        self.user_id = user_id
        self.window_opened = None
        self.MAX_STOCKS = 3
        self.last_api_call_time = 0
        self.entry_used_time = 0
        self.total_seconds = 0

        # Configure grid
        self.screen_width = 1440
        self.screen_height = 900
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(fg_color="#666666")

        # Set style
        style = ttk.Style(self)
        style.theme_use("clam")
        # Eliminate borders and lines
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        # Configure Treeview style
        style.configure("Treeview",
                        background="#000000",  # Black background
                        fieldbackground="#000000",  # Black field background
                        foreground="#ffffff",  # White text
                        borderwidth=0,  # No border
                        highlightthickness=0,  # No highlight
                        bd=0,  # No border width
                        font=('Roboto', 14))
        # Configure Treeview Heading style
        style.configure("Treeview.Heading",
                        background="#434343",  # Dark gray heading background
                        foreground="#ffffff",  # White heading text
                        borderwidth=0,  # No border
                        font=('Roboto', 14, 'bold'))

        # Create the table
        self.table = ttk.Treeview(self,
                                  columns=("id", "time_unit", "time_amount", "bot_type", "stocks", "strategies"),
                                  show='headings')
        self.table.heading("#1", text="ID")
        self.table.heading("#2", text="Time Frame")
        self.table.heading("#3", text="Bar Frequency")
        self.table.heading("#4", text="Bot Type")
        self.table.heading("#5", text="Stocks")
        self.table.heading("#6", text="Strategies")
        self.table.grid(row=0, column=0, sticky="nsew", rowspan=8)
        self.table.column('#1', stretch=False, minwidth=0, width=0)

        # Connect to the SQLite database
        self.conn = sqlite3.connect('database.db')
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.c = self.conn.cursor()

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS configurations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                time_unit TEXT,
                time_amount TEXT,
                bot_type TEXT,
                stocks TEXT,
                strategies TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Frame
        widget_frame = customtkinter.CTkFrame(self, fg_color="#666666")
        widget_frame.grid(row=0, column=1, padx=25, sticky="nsew")

        # GUI setup
        self.setup_gui(widget_frame)

        # Load the data into the table
        self.load_data()

    def setup_gui(self, frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(12, weight=1)

        # Delete widgets
        delete_label = customtkinter.CTkLabel(frame, text="Delete configuration:", font=("Roboto", 12, "bold"))
        self.delete_button = customtkinter.CTkButton(frame,
                                                     text="Delete",
                                                     command=self.delete_record,
                                                     font=customtkinter.CTkFont(size=12, weight="bold"),
                                                     height=30,
                                                     corner_radius=15,
                                                     state="disabled")

        delete_label.grid(row=1, column=0, sticky="n", pady=(0, 10))
        self.delete_button.grid(row=2, column=0, sticky="n", pady=(0, 20))

        # Add widgets
        add_label = customtkinter.CTkLabel(frame, text="Add a configuration:", font=("Roboto", 12, "bold"))
        add_unit_label = customtkinter.CTkLabel(frame, text="Time  Unit:", font=("Roboto", 10, "bold"))
        self.unit = customtkinter.StringVar()
        self.unit_entry = customtkinter.CTkEntry(frame,
                                                 font=("Roboto", 12, "bold"),
                                                 height=30,
                                                 corner_radius=15,
                                                 textvariable=self.unit)
        add_amount_label = customtkinter.CTkLabel(frame, text="Time  Amount:", font=("Roboto", 10, "bold"))
        self.amount = customtkinter.StringVar()
        self.amount_entry = customtkinter.CTkEntry(frame,
                                                   font=("Roboto", 12, "bold"),
                                                   height=30,
                                                   corner_radius=15,
                                                   textvariable=self.amount)

        add_label.grid(row=3, column=0, sticky="n", pady=(0, 10))
        add_unit_label.grid(row=4, column=0, sticky="n")
        self.unit_entry.grid(row=5, column=0, sticky="n", pady=(0, 10))
        add_amount_label.grid(row=6, column=0, sticky="n")
        self.amount_entry.grid(row=7, column=0, sticky="n")

        self.error_label = customtkinter.CTkLabel(frame, text="", text_color="#EA9999", font=("Roboto", 12, "bold"))
        self.add_button = customtkinter.CTkButton(frame,
                                                  text="Add",
                                                  command=self.validate,
                                                  font=customtkinter.CTkFont(size=12, weight="bold"),
                                                  height=30,
                                                  corner_radius=15)

        self.error_label.grid(row=8, column=0, sticky="n")
        self.add_button.grid(row=9, column=0, sticky="n", pady=(10, 20))

        # Run widgets
        run_label = customtkinter.CTkLabel(frame, text="Run configuration:", font=("Roboto", 12, "bold"))
        self.run_button = customtkinter.CTkButton(frame,
                                                  text="Run",
                                                  command=self.handle_api_limit,
                                                  font=customtkinter.CTkFont(size=12, weight="bold"),
                                                  state="disabled",
                                                  height=30,
                                                  corner_radius=15)

        run_label.grid(row=10, column=0, sticky="n", pady=(0, 10))
        self.run_button.grid(row=11, column=0, sticky="n", pady=(0, 0))

        self.table.bind("<<TreeviewSelect>>", self.on_select)

    def open_window_1(self):
        print("window button 1 pressed")
        self.error_label.configure(text="")
        self.window_1 = customtkinter.CTkToplevel(self)
        self.window_opened = "window 1"

        self.window_1.title("Customisation")
        window_width = 250
        window_height = 350
        x_position = (self.screen_width - window_width) // 2
        y_position = (self.screen_height - window_height) // 2
        self.window_1.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.window_1.resizable(False, False)
        self.window_1.configure(fg_color="#434343")
        self.window_1.grid_rowconfigure(0, weight=1)
        self.window_1.grid_rowconfigure(9, weight=1)
        self.window_1.grid_columnconfigure(0, weight=1)
        self.window_1.grid_columnconfigure(2, weight=1)

        customtkinter.CTkLabel(master=self.window_1,
                               text="Customisation",
                               font=("Roboto", 18, "bold")).grid(row=1, column=1, pady=(0, 10))
        self.var1_1 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_1,
                                  text="Momentum",
                                  variable=self.var1_1,
                                  onvalue="Momentum",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=2,
                                                                    column=1,
                                                                    padx=(20, 0),
                                                                    pady=(0, 10), sticky="w")
        self.var1_2 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_1,
                                  text="SMACrossover",
                                  variable=self.var1_2,
                                  onvalue="SMACrossover",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=3,
                                                                    column=1,
                                                                    padx=(20, 0),
                                                                    pady=(0, 10),
                                                                    sticky="w")
        self.var1_3 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_1,
                                  text="Breakout",
                                  variable=self.var1_3,
                                  onvalue="Breakout",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=4,
                                                                    column=1,
                                                                    padx=(20, 0),
                                                                    pady=(0, 10),
                                                                    sticky="w")
        self.var1_4 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_1,
                                  text="SVR",
                                  variable=self.var1_4,
                                  onvalue="SVRStrategy",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=5,
                                                                    column=1,
                                                                    padx=(20, 0),
                                                                    pady=(0, 15),
                                                                    sticky="w")

        self.stocks_entry_1 = customtkinter.CTkEntry(master=self.window_1,
                                                     placeholder_text="Stocks",
                                                     font=("Roboto", 12, "bold"),
                                                     height=30,
                                                     corner_radius=15)
        self.stocks_entry_1.grid(row=6, column=1)

        self.window_error_label_1 = customtkinter.CTkLabel(master=self.window_1,
                                                           text="",
                                                           text_color="#EA9999",
                                                           font=("Roboto", 12, "bold"))
        self.window_error_label_1.grid(row=7, column=1, pady=(0, 10))

        customtkinter.CTkButton(master=self.window_1,
                                text="Done",
                                command=self.submit,
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                height=30,
                                corner_radius=15).grid(row=8, column=1, pady=(0, 10))
        self.window_1.bind("<Destroy>", self.enable_add_button)

    def open_window_2(self):
        print("window button 2 pressed")
        self.error_label.configure(text="")
        self.window_2 = customtkinter.CTkToplevel(self)
        self.window_opened = "window 2"
        self.window_2.title("Customisation")
        window_width = 250
        window_height = 300
        x_position = (self.screen_width - window_width) // 2
        y_position = (self.screen_height - window_height) // 2
        self.window_2.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.window_2.resizable(False, False)
        self.window_2.configure(fg_color="#434343")
        self.window_2.grid_rowconfigure(0, weight=1)
        self.window_2.grid_rowconfigure(8, weight=1)
        self.window_2.grid_columnconfigure(0, weight=1)
        self.window_2.grid_columnconfigure(2, weight=1)

        customtkinter.CTkLabel(master=self.window_2,
                               text="Customisation",
                               font=("Roboto", 18, "bold")).grid(row=1, column=1, pady=(0, 10))
        self.var2_1 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_2,
                                  text="Momentum",
                                  variable=self.var2_1,
                                  onvalue="Momentum",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=2,
                                                                    column=1,
                                                                    padx=(20, 0),
                                                                    pady=(0, 10),
                                                                    sticky="w")
        self.var2_2 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_2,
                                  text="Scalping",
                                  variable=self.var2_2,
                                  onvalue="Scalping",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=3,
                                                                    column=1,
                                                                    padx=(20, 0),
                                                                    pady=(0, 10),
                                                                    sticky="w")
        self.var2_3 = customtkinter.StringVar()
        customtkinter.CTkCheckBox(master=self.window_2,
                                  text="Mean Reversion",
                                  variable=self.var2_3,
                                  onvalue="MeanReversion",
                                  offvalue="",
                                  font=("Roboto", 12, "bold")).grid(row=4,
                                                                    padx=(20, 0),
                                                                    column=1,
                                                                    pady=(0, 15),
                                                                    sticky="w")

        self.stocks_entry_2 = customtkinter.CTkEntry(master=self.window_2,
                                                     placeholder_text="Stocks",
                                                     font=("Roboto", 12, "bold"),
                                                     height=30,
                                                     corner_radius=15)
        self.stocks_entry_2.grid(row=5, column=1)

        self.window_error_label_2 = customtkinter.CTkLabel(master=self.window_2,
                                                           text="",
                                                           text_color="#EA9999",
                                                           font=("Roboto", 12, "bold"))
        self.window_error_label_2.grid(row=6, column=1, pady=(0, 10))

        customtkinter.CTkButton(master=self.window_2,
                                text="Done",
                                command=self.submit,
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                height=30, corner_radius=15).grid(row=7, column=1, pady=(0, 10))
        self.window_2.bind("<Destroy>", self.enable_add_button)

    def enable_add_button(self, event=None):
        self.add_button.configure(state='normal')

    def open_rate_limit_window(self):
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

    def submit(self):
        if self.window_opened == "window 1":
            options_1 = [self.var1_1.get(), self.var1_2.get(), self.var1_3.get(), self.var1_4.get()]
            checked_options_1 = [option for option in options_1 if option != ""]
            result_1 = ', '.join(checked_options_1)
            stocks_str = self.stocks_entry_1.get()
            if result_1 == "":
                self.window_error_label_1.configure(text="Please check at least one box")
            elif not stocks_str:
                self.window_error_label_1.configure(text="Please enter at lest one stock")
            elif self.validate_tickers(stocks_str) == "Too many":
                self.window_error_label_1.configure(text="Too many stocks entered.")
            elif self.validate_tickers(stocks_str) == "Invalid":
                self.window_error_label_1.configure(text="Stock(s) invalid")
            else:
                self.add_record(result_1, stocks_str)
                self.window_1.destroy()
                self.add_button.configure(state='normal')
        elif self.window_opened == "window 2":
            options_2 = [self.var2_1.get(), self.var2_2.get(), self.var2_3.get()]
            checked_options_2 = [option for option in options_2 if option != ""]
            result_2 = ', '.join(checked_options_2)
            stocks_str = self.stocks_entry_2.get()
            if result_2 == "":
                self.window_error_label_2.configure(text="Please check at least one box")
            elif not stocks_str:
                self.window_error_label_2.configure(text="Please enter at lest one stock")
            elif self.validate_tickers(stocks_str) == "Too many":
                self.window_error_label_2.configure(text="Too many stocks entered.")
            elif self.validate_tickers(stocks_str) == "Invalid":
                self.window_error_label_2.configure(text="Stock(s) invalid")
            else:
                self.add_record(result_2, stocks_str)
                self.window_2.destroy()
                self.add_button.configure(state='normal')
        else:
            print("error no window opened")

    def validate(self):
        time_unit = self.unit_entry.get().title()
        time_amount = self.amount_entry.get().title()

        if not time_unit or not time_amount:
            self.error_label.configure(text="Please enter a time frame")
        else:
            minutes = self.convert_to_base(unit=time_unit, amount=time_amount)
            if minutes == "Unsupported unit":
                self.error_label.configure(text="Unsupported unit")
            if minutes == "Amount must be an integer":
                self.error_label.configure(text="Amount must be an integer")
            elif int(minutes) <= 15:
                self.open_window_2()
                self.add_button.configure(state='disabled')
            else:
                self.open_window_1()
                self.add_button.configure(state='disabled')

    def convert_to_base(self, unit, amount):
        try:
            x = int(amount)
            if unit == "Day":
                return x * 24 * 60
            elif unit == "Hour":
                return x * 60
            elif unit == "Minute":
                return x
            else:
                return "Unsupported unit"
        except ValueError:
            return "Amount must be an integer"

    def validate_tickers(self, tickers_str):
        tickers = tickers_str.split(', ')

        if len(tickers) > self.MAX_STOCKS:
            print(f"Error: Too many tickers entered.")
            return "Too many"

        for ticker in tickers:
            try:
                data = yf.Ticker(ticker).history(period='1d')  # Get recent 1-day trading data
                if data.empty:  # If the data is empty, ticker is invalid
                    return "Invalid"
            except Exception as e:  # If any exception occurs, ticker is invalid
                print(f"Exception occurred: {e}")
                return "Invalid"

        return "Valid"

    def load_data(self):
        # Remove all existing rows from the table
        for row in self.table.get_children():
            self.table.delete(row)
        # Query the database
        self.c.execute(
            "SELECT id, time_unit, time_amount, bot_type, stocks, strategies FROM configurations WHERE user_id = ?",
            (self.user_id,)
        )
        rows = self.c.fetchall()
        # Insert data into the table
        for row in rows:
            self.table.insert('', 'end', values=row)

    def on_select(self, event):
        selected = self.table.selection()
        if selected:
            self.run_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            self.run_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")

    def delete_record(self):
        selected_id = self.table.selection()[0]  # Get selected item's ID
        selected_item = self.table.item(selected_id)  # Get selected item's details
        selected_values = selected_item['values']
        id_to_delete = selected_values[0]
        # Check if the user owns this data
        self.c.execute('SELECT user_id FROM configurations WHERE id = ?', (id_to_delete,))
        owner_id = self.c.fetchone()[0]
        if owner_id == self.user_id:
            # If the user owns this data, delete it
            self.c.execute("DELETE FROM configurations WHERE id=?", (id_to_delete,))
            self.conn.commit()
            self.load_data()
        else:
            print("Error user does not own data to delete")

    def add_record(self, strategies, stocks):
        unit_to_add = self.unit_entry.get().title()
        amount_to_add = self.amount_entry.get().title()
        stocks_to_add = stocks
        strategies_to_add = strategies
        if self.window_opened == "window 1":
            bot_type_to_add = "Historical"
        else:
            bot_type_to_add = "Live"
        # Autoincrement for id
        self.c.execute("INSERT INTO configurations (time_unit, time_amount, bot_type, stocks, strategies, user_id) "
                       "VALUES (?, ?, ?, ?, ?, ?)",
                       (unit_to_add, amount_to_add, bot_type_to_add, stocks_to_add, strategies_to_add, self.user_id)
                       )
        self.conn.commit()
        self.load_data()
        # Clear the entry fields
        self.unit_entry.delete(0, customtkinter.END)
        self.amount_entry.delete(0, customtkinter.END)

    def handle_api_limit(self):
        current_time = time.time()

        if current_time - self.last_api_call_time >= 60:
            self.last_api_call_time = current_time
            self.entry_used_time = current_time
            self.run_record()
        else:
            if current_time - self.entry_used_time >= 60:
                self.entry_used_time = current_time
                self.run_record()
            else:
                print("Rate Limit:", "Please wait for a minute before making another API call.")
                self.open_rate_limit_window()

    def run_record(self):
        selected_id = self.table.selection()[0]  # Get selected item's ID
        selected_item = self.table.item(selected_id)  # Get selected item's details
        selected_values = selected_item['values']
        selected_values.append(self.user_id)
        result_string = '$'.join(map(str, selected_values))
        with open('bot_configuration.txt', 'w') as file:
            file.write(result_string)
        self.controller.bot_time_frame.set(f'{selected_values[2]} {selected_values[1]}')
        self.controller.bot_type.set(selected_values[3])
        self.controller.bot_stocks.set(selected_values[4])
        self.controller.bot_strategies.set(selected_values[5])
        self.controller.enable_running_button()
        self.controller.switch_frame('PageTwo')
        self.task.start()
