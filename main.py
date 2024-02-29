# IMPORTING API
from alpaca.trading.client import TradingClient
# IMPORTING MODULES
import customtkinter
import requests
import sqlite3
import multiprocessing
# IMPORTING USER-DEFINED MODULES
from home import StartPage
from bot import PageOne
from run import PageTwo
from task import Task
import security


def generate_salt(length=5):
    # Generate a salt from random integers
    salt = ''.join(chr(i % 256) for i in [int(1000 * abs((i ** 0.5) - int(i ** 0.5))) for i in range(length)])
    return salt


def hash_password(input_string, salt=None):
    if salt is None:
        salt = generate_salt()

    combined_input = input_string + salt

    # Operations involving large prime numbers are not easily reversible
    prime = 7919
    ascii_values = [ord(char) for char in combined_input]
    hash_value = 0

    for i, val in enumerate(ascii_values):
        hash_value += val * (prime ** i)

    hash_value = hash_value % 1000000

    # Store the salt alongside the hash using a delimiter (e.g., $)
    return f"{str(hash_value).zfill(6)}${salt}"


def verify(stored_hash, input_string):
    hash_part, salt = stored_hash.split('$')
    return hash_part == hash_password(input_string, salt).split('$')[0]


customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("turquoise.json")

# Connect to SQLite database
conn = sqlite3.connect('database.db')
# Create a cursor
c = conn.cursor()
# Create users table
c.execute("""CREATE TABLE IF NOT EXISTS users (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             username text,
             password text
             )""")
# Create details table
c.execute("""CREATE TABLE IF NOT EXISTS details (
             user_id INTEGER PRIMARY KEY,
             name text,
             api_key text,
             api_secret_key text,
             av_key text,
             FOREIGN KEY(user_id) REFERENCES users(id)
             )""")
# Commit and close connection
conn.commit()
conn.close()


class App(customtkinter.CTkToplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.master = master
        self.user_id = user_id
        self._frames = {}
        self._frame = None
        self.bot_time_frame = customtkinter.StringVar()
        self.bot_type = customtkinter.StringVar()
        self.bot_stocks = customtkinter.StringVar()
        self.bot_strategies = customtkinter.StringVar()
        self.data_queue = multiprocessing.Queue()
        self.stdout_queue = multiprocessing.Queue()
        self.task = Task(self.data_queue, self.stdout_queue)
        self.switch_frame('StartPage')

        # Configure window
        self.title("♜ QuantHaven")
        screen_width = 1440
        screen_height = 900
        window_width = 1000
        window_height = 580
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.resizable(False, False)

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.configure(fg_color="#434343")

        # Create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, fg_color="#666666", width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame,
                                                 text="♜ QuantHaven",
                                                 font=customtkinter.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame,
                                                        text="Home",
                                                        font=customtkinter.CTkFont(size=12, weight="bold"),
                                                        height=30,
                                                        corner_radius=15,
                                                        command=lambda: self.switch_frame('StartPage'))
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame,
                                                        text="Bots",
                                                        font=customtkinter.CTkFont(size=12, weight="bold"),
                                                        height=30, corner_radius=15,
                                                        command=lambda: self.switch_frame('PageOne'))
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame,
                                                        text="Running",
                                                        font=customtkinter.CTkFont(size=12, weight="bold"),
                                                        height=30,
                                                        corner_radius=15,
                                                        command=lambda: self.switch_frame('PageTwo'))
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        self.forget_account = customtkinter.CTkButton(self.sidebar_frame,
                                                      text="Forget",
                                                      font=customtkinter.CTkFont(size=12, weight="bold"),
                                                      height=30,
                                                      corner_radius=15,
                                                      command=lambda: self.are_you_sure())
        self.forget_account.grid(row=7, column=0, padx=20, pady=10)
        self.quit_button = customtkinter.CTkButton(self.sidebar_frame,
                                                   text="Quit",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"),
                                                   height=30,
                                                   corner_radius=15,
                                                   command=lambda: self.close_program())
        self.quit_button.grid(row=8, column=0, padx=20, pady=(10, 20))

        # Set default values
        self.sidebar_button_3.configure(state="disabled")
        self.bind("<Destroy>", self.close_program)

    def enable_running_button(self):
        self.sidebar_button_3.configure(state="normal")
        self.sidebar_button_1.configure(state='disabled')
        self.sidebar_button_2.configure(state='disabled')

    def disable_running_button(self):
        self.sidebar_button_3.configure(state="disabled")
        self.sidebar_button_1.configure(state='normal')
        self.sidebar_button_2.configure(state='normal')

    def switch_frame(self, frame_class):  # Raise requested frame
        frame = self._frames.get(frame_class, None)

        if frame is None:
            if frame_class == 'PageOne':
                frame = PageOne(master=self, task=self.task, user_id=self.user_id, controller=self)
            elif frame_class == 'PageTwo':
                frame = PageTwo(master=self,
                                task=self.task,
                                data_queue=self.data_queue,
                                stdout_queue=self.stdout_queue,
                                controller=self)
            else:
                frame = StartPage(master=self, user_id=self.user_id)
            self._frames[frame_class] = frame

        if self._frame is not None:
            self._frame.grid_forget()

        self._frame = frame
        self._frame.grid(row=0, column=1, rowspan=4, columnspan=3, sticky="nsew")

    def are_you_sure(self):
        are_you_sure = customtkinter.CTkToplevel(self)
        are_you_sure.title("Login")
        screen_width = 1440
        screen_height = 900
        window_width = 300
        window_height = 200
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        are_you_sure.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        are_you_sure.resizable(False, False)
        are_you_sure.configure(fg_color="#434343")
        customtkinter.CTkLabel(are_you_sure,
                               text="Confirm: Delete Account",
                               font=customtkinter.CTkFont(size=22, weight="bold")).place(relx=0.5,
                                                                                         rely=0.2,
                                                                                         anchor='center')
        customtkinter.CTkLabel(are_you_sure,
                               text_color="#CCCCCC",
                               text="Are you sure you want to delete your QuantHaven account?",
                               font=customtkinter.CTkFont(size=14, weight="bold"),
                               wraplength=200).place(relx=0.5, rely=0.4, anchor='center')
        customtkinter.CTkButton(are_you_sure,
                                text="Yes",
                                fg_color="transparent",
                                border_width=2,
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                width=80,
                                height=30,
                                corner_radius=15,
                                command=self.delete_user).place(relx=0.3, rely=0.7, anchor='center')
        customtkinter.CTkButton(are_you_sure,
                                text="No",
                                fg_color="transparent",
                                border_width=2,
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                width=80,
                                height=30,
                                corner_radius=15,
                                command=are_you_sure.destroy).place(relx=0.7, rely=0.7, anchor='center')

    def delete_user(self):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Delete the user's data entries
        c.execute('DELETE FROM configurations WHERE user_id = ?', (self.user_id,))
        c.execute('DELETE FROM details WHERE user_id = ?', (self.user_id,))
        # Delete the user
        c.execute('DELETE FROM users WHERE id = ?', (self.user_id,))
        conn.commit()
        conn.close()
        # Choosing to delete your user data also closes the app
        self.close_program()

    def close_program(self, event=None):
        self.unbind("<Destroy>")
        self.task.stop()
        self.destroy()
        self.master.quit()


def check_credentials(api_key, secret_key):
    trading_client = TradingClient(api_key, secret_key, paper=True)
    try:
        account_info = trading_client.get_account()
        print(account_info)
        return True
    except Exception as e:
        print(e)
        return False


def validate_alpha_vantage_key(api_key):
    test_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SPY&apikey={api_key}"
    response = requests.get(test_url)

    if response.status_code == 200:  # Successful request will return 200
        json_response = response.json()
        if json_response.get("message") == "forbidden.":
            print("Invalid Alpha Vantage API key.")
            return False
        elif "Global Quote" in json_response:
            print("Valid Alpha Vantage API key.")
            return True
        else:
            print("Received unexpected JSON response from Alpha Vantage API.")
            return False
    else:
        print(f"Received unexpected status code {response.status_code} from Alpha Vantage API")
        return False


class LoginApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Account System")
        self.screen_width = 1440
        self.screen_height = 900
        window_width = 250
        window_height = 250
        x_position = (self.screen_width - window_width) // 2
        y_position = (self.screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.resizable(False, False)
        self.configure(fg_color="#434343")

        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()

        # Create login and sign up buttons
        customtkinter.CTkLabel(self,
                               text="♜ QuantHaven",
                               font=customtkinter.CTkFont(size=22, weight="bold")).place(relx=0.5,
                                                                                         rely=0.2,
                                                                                         anchor='center')
        self.login_btn = customtkinter.CTkButton(self,
                                                 text="Login",
                                                 font=customtkinter.CTkFont(size=12, weight="bold"),
                                                 height=30,
                                                 corner_radius=15,
                                                 command=self.login)
        self.login_btn.place(relx=0.5, rely=0.4, anchor='center')
        customtkinter.CTkLabel(self,
                               text_color="#CCCCCC",
                               text="Or if you don't have a QuantHaven account:",
                               font=customtkinter.CTkFont(size=14, weight="bold"),
                               wraplength=180).place(relx=0.5, rely=0.6, anchor='center')
        self.sign_up_btn = customtkinter.CTkButton(self,
                                                   text="Sign Up",
                                                   fg_color="transparent",
                                                   border_width=2,
                                                   font=customtkinter.CTkFont(size=12, weight="bold"),
                                                   height=30,
                                                   corner_radius=15,
                                                   command=self.sign_up)
        self.sign_up_btn.place(relx=0.5, rely=0.8, anchor='center')

    def login(self):
        self.login_btn.configure(state='disabled')
        login_window = customtkinter.CTkToplevel(self)
        login_window.title("Login")
        window_width = 250
        window_height = 300
        x_position = (self.screen_width - window_width) // 2
        y_position = (self.screen_height - window_height) // 2
        login_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        login_window.resizable(False, False)
        login_window.configure(fg_color="#434343")
        customtkinter.CTkLabel(login_window,
                               text="Login",
                               font=customtkinter.CTkFont(size=22, weight="bold")).place(relx=0.5,
                                                                                         rely=0.2,
                                                                                         anchor='center')

        customtkinter.CTkLabel(login_window,
                               text_color="#CCCCCC",
                               text="Username:",
                               font=customtkinter.CTkFont(size=14, weight="bold")).place(relx=0.5,
                                                                                         rely=0.3,
                                                                                         anchor='center')
        username_entry = customtkinter.CTkEntry(login_window,
                                                height=30,
                                                corner_radius=15,
                                                placeholder_text="Username",
                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        username_entry.place(relx=0.5, rely=0.4, anchor='center')

        customtkinter.CTkLabel(login_window,
                               text_color="#CCCCCC",
                               text="Password:",
                               font=customtkinter.CTkFont(size=14, weight="bold")).place(relx=0.5,
                                                                                         rely=0.5,
                                                                                         anchor='center')
        password_entry = customtkinter.CTkEntry(login_window,
                                                show="\u2022",
                                                height=30,
                                                corner_radius=15,
                                                placeholder_text="Password",
                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        password_entry.place(relx=0.5, rely=0.6, anchor='center')

        self.login_error_label = customtkinter.CTkLabel(login_window,
                                                        text="",
                                                        font=customtkinter.CTkFont(size=14, weight="bold"))
        self.login_error_label.place(relx=0.5, rely=0.7, anchor='center')
        customtkinter.CTkButton(login_window,
                                text="Login",
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                height=30,
                                corner_radius=15,
                                command=lambda: self.check_login(username_entry.get(),
                                                                 password_entry.get(),
                                                                 login_window)).place(relx=0.5,
                                                                                      rely=0.8,
                                                                                      anchor='center')
        login_window.bind("<Destroy>", self.enable_buttons)

    def check_login(self, username, password, login_window):
        self.c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = self.c.fetchone()

        if username == "" or password == "":
            self.login_error_label.configure(text="Fields cannot be blank", text_color="#EA9999")
            return

        if user:
            if verify(user[2], password):
                # Passwords match
                self.login_error_label.configure(text="Successfully logged in", text_color="#B6D7A8")
                # CLOSE  WINDOW
                login_window.withdraw()
                self.withdraw()  # Hide the login window
                App(self, user[0])
            else:
                # Passwords do not match
                self.login_error_label.configure(text="Password does not match user", text_color="#EA9999")
                user = None
        else:
            self.login_error_label.configure(text="User not found", text_color="#EA9999")

    def sign_up(self):
        self.sign_up_btn.configure(state='disabled')
        sign_up_window = customtkinter.CTkToplevel(self)
        sign_up_window.title("Sign Up")
        window_width = 250
        window_height = 500
        x_position = (self.screen_width - window_width) // 2
        y_position = (self.screen_height - window_height) // 2
        sign_up_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        sign_up_window.resizable(False, False)
        sign_up_window.configure(fg_color="#434343")
        sign_up_window.grid_rowconfigure(0, weight=1)
        sign_up_window.grid_rowconfigure(16, weight=1)
        sign_up_window.grid_columnconfigure(0, weight=1)
        sign_up_window.grid_columnconfigure(2, weight=1)
        customtkinter.CTkLabel(sign_up_window,
                               text="Sign up",
                               font=customtkinter.CTkFont(size=22, weight="bold")).grid(row=1, column=1)

        customtkinter.CTkLabel(sign_up_window,
                               text_color="#CCCCCC",
                               text="Username:",
                               font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=2, column=1)
        username_entry = customtkinter.CTkEntry(sign_up_window,
                                                height=30,
                                                corner_radius=15,
                                                placeholder_text="Username",
                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        username_entry.grid(row=3, column=1)

        customtkinter.CTkLabel(sign_up_window,
                               text_color="#CCCCCC",
                               text="Password:",
                               font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=4, column=1)
        password_entry = customtkinter.CTkEntry(sign_up_window,
                                                show="\u2022",
                                                height=30,
                                                corner_radius=15,
                                                placeholder_text="Password",
                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        password_entry.grid(row=5, column=1)

        customtkinter.CTkLabel(sign_up_window,
                               text_color="#CCCCCC",
                               text="Name",
                               font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=6, column=1)
        name_entry = customtkinter.CTkEntry(sign_up_window,
                                            height=30,
                                            corner_radius=15,
                                            placeholder_text="Name",
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        name_entry.grid(row=7, column=1)

        customtkinter.CTkLabel(sign_up_window,
                               text_color="#CCCCCC",
                               text="Alpaca Key:",
                               font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=8, column=1)
        api_key_entry = customtkinter.CTkEntry(sign_up_window,
                                               show="\u2022",
                                               height=30,
                                               corner_radius=15,
                                               placeholder_text="API Key",
                                               font=customtkinter.CTkFont(size=12, weight="bold"))
        api_key_entry.grid(row=9, column=1)

        customtkinter.CTkLabel(sign_up_window,
                               text_color="#CCCCCC",
                               text="Alpaca Secret Key:",
                               font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=10, column=1)
        api_secret_key_entry = customtkinter.CTkEntry(sign_up_window,
                                                      show="\u2022",
                                                      height=30,
                                                      corner_radius=15,
                                                      placeholder_text="API Key",
                                                      font=customtkinter.CTkFont(size=12, weight="bold"))
        api_secret_key_entry.grid(row=11, column=1)

        customtkinter.CTkLabel(sign_up_window,
                               text_color="#CCCCCC",
                               text="Alpha Vantage Key",
                               font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=12, column=1)
        av_key_entry = customtkinter.CTkEntry(sign_up_window,
                                              show="\u2022",
                                              height=30,
                                              corner_radius=15,
                                              placeholder_text="API Key",
                                              font=customtkinter.CTkFont(size=12, weight="bold"))
        av_key_entry.grid(row=13, column=1)

        self.sign_up_error_label = customtkinter.CTkLabel(sign_up_window,
                                                          text="",
                                                          font=customtkinter.CTkFont(size=14, weight="bold"))
        self.sign_up_error_label.grid(row=14, column=1)

        customtkinter.CTkButton(sign_up_window,
                                text="Sign Up",
                                font=customtkinter.CTkFont(size=12, weight="bold"),
                                height=30,
                                corner_radius=15,
                                command=lambda: self.create_account(username_entry.get(),
                                                                    password_entry.get(),
                                                                    name_entry.get(),
                                                                    api_key_entry.get(),
                                                                    api_secret_key_entry.get(),
                                                                    av_key_entry.get(),
                                                                    sign_up_window)).grid(row=15, column=1)
        sign_up_window.bind("<Destroy>", self.enable_buttons)

    def create_account(self, username, password, name, api_key, api_secret_key, av_key, sign_up_window):

        if username == "" or password == "" or name == "" or api_key == "" or api_secret_key == "" or av_key == "":
            self.sign_up_error_label.configure(text="Fields cannot be blank", text_color="#EA9999")
            return

        self.c.execute("SELECT * FROM users WHERE username=?", (username,))
        if self.c.fetchone():
            self.sign_up_error_label.configure(text="Username already exists", text_color="#EA9999")
            return

        if not check_credentials(api_key, api_secret_key):
            self.sign_up_error_label.configure(text="Alpaca keys invalid", text_color="#EA9999")
            return

        if not validate_alpha_vantage_key(av_key):
            self.sign_up_error_label.configure(text="Alpha vantage invalid", text_color="#EA9999")
            return

        # HASH
        hashed_password = hash_password(password)

        self.c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        self.conn.commit()
        self.c.execute("SELECT id FROM users WHERE username=?", (username,))
        user_id = self.c.fetchone()[0]

        # ENCRYPT
        encrypted_api_key = security.encrypt_data(api_key, str(user_id) + 'A')
        encrypted_api_secret_key = security.encrypt_data(api_secret_key, str(user_id) + 'B')
        encrypted_av_key = security.encrypt_data(av_key, str(user_id) + 'C')

        self.c.execute("INSERT INTO details (user_id, name, api_key, api_secret_key, av_key) VALUES (?, ?, ?, ?, ?)",
                       (user_id, name, encrypted_api_key, encrypted_api_secret_key, encrypted_av_key))
        self.conn.commit()
        self.sign_up_error_label.configure(text="Account created successfully", text_color="#B6D7A8")
        self.sign_up_btn.configure(state='normal')
        # CLOSE SIGN UP PAGE
        sign_up_window.withdraw()

    def enable_buttons(self, event=None):
        self.login_btn.configure(state='normal')
        self.sign_up_btn.configure(state='normal')


if __name__ == "__main__":
    loginapp = LoginApp()
    loginapp.mainloop()
