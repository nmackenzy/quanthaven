import customtkinter
from matplotlib import dates
import pandas as pd
import queue
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PageTwo(customtkinter.CTkFrame):
    def __init__(self, master, task, data_queue=None, stdout_queue=None, controller=None):
        customtkinter.CTkFrame.__init__(self, master)

        self.controller = controller
        self.task = task
        self.data_queue = data_queue
        self.stdout_queue = stdout_queue
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1), weight=1)
        self.configure(fg_color="#434343")

        # Frame 1
        self.frame1 = customtkinter.CTkFrame(self, fg_color="#666666", width=200, height=150)
        self.frame1.grid(row=0, column=0, padx=(20, 10), pady=(20, 0), sticky="nsew")

        self.container = customtkinter.CTkFrame(self.frame1, fg_color="#666666", width=200, height=100)
        self.container.place(relx=0.5, rely=0.45, anchor='center')
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(7, weight=1)

        self.config_label = customtkinter.CTkLabel(master=self.container,
                                                   text='Configurations',
                                                   font=customtkinter.CTkFont(size=24, weight="bold"))
        self.config_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(10, 0), pady=(0, 10))
        self.label1 = customtkinter.CTkLabel(master=self.container,
                                             text='Time Frame:',
                                             font=customtkinter.CTkFont(size=15, weight="bold"))
        self.label1.grid(row=2, column=0, sticky="w", padx=(10, 0), pady=(0, 5))
        self.label1_data = customtkinter.CTkLabel(master=self.container,
                                                  font=customtkinter.CTkFont(size=15, weight="bold"),
                                                  textvariable=self.controller.bot_time_frame,
                                                  text_color="#B7B7B7")
        self.label1_data.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        self.label2 = customtkinter.CTkLabel(master=self.container,
                                             text='Type:',
                                             font=customtkinter.CTkFont(size=15, weight="bold"))
        self.label2.grid(row=3, column=0, sticky="w", padx=(10, 0), pady=(0, 5))
        self.label2_data = customtkinter.CTkLabel(master=self.container,
                                                  font=customtkinter.CTkFont(size=15, weight="bold"),
                                                  textvariable=self.controller.bot_type, text_color="#B7B7B7")
        self.label2_data.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        self.label3 = customtkinter.CTkLabel(master=self.container,
                                             text='Stocks:',
                                             font=customtkinter.CTkFont(size=15, weight="bold"))
        self.label3.grid(row=4, column=0, sticky="w", padx=(10, 0), pady=(0, 5))
        self.label3_data = customtkinter.CTkLabel(master=self.container,
                                                  font=customtkinter.CTkFont(size=15, weight="bold"),
                                                  textvariable=self.controller.bot_stocks,
                                                  wraplength=200,
                                                  text_color="#B7B7B7")
        self.label3_data.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        self.label4 = customtkinter.CTkLabel(master=self.container,
                                             text='Strategies:',
                                             font=customtkinter.CTkFont(size=15, weight="bold"))
        self.label4.grid(row=5, column=0, sticky="w", padx=(10, 0), pady=(0, 20))
        self.label4_data = customtkinter.CTkLabel(master=self.container,
                                                  font=customtkinter.CTkFont(size=15, weight="bold"),
                                                  textvariable=self.controller.bot_strategies,
                                                  wraplength=200,
                                                  text_color="#B7B7B7")
        self.label4_data.grid(row=5, column=1, padx=(10, 0), pady=(0, 20))
        self.stop_button = customtkinter.CTkButton(master=self.frame1,
                                                   text="Stop",
                                                   font=customtkinter.CTkFont(size=14, weight="bold"),
                                                   fg_color="transparent",
                                                   border_width=2,
                                                   height=30,
                                                   corner_radius=15,
                                                   command=self.stop_clicked)
        self.stop_button.place(relx=0.25, rely=0.85, anchor='center')
        self.clear_button = customtkinter.CTkButton(master=self.frame1,
                                                    text="Clear",
                                                    font=customtkinter.CTkFont(size=14, weight="bold"),
                                                    fg_color="transparent",
                                                    border_width=2,
                                                    height=30,
                                                    corner_radius=15,
                                                    command=self.clear_text)
        self.clear_button.place(relx=0.75, rely=0.85, anchor='center')

        # Frame 2
        self.frame2 = customtkinter.CTkFrame(self, fg_color="#999999", width=200, height=150)
        self.frame2.grid(row=1, column=0, padx=(20, 10), pady=(20, 20), sticky="nsew")

        self.title_font_prop = font_manager.FontProperties(weight='bold', size=14, family='Roboto')
        self.label_font_prop = font_manager.FontProperties(weight='bold', size=8, family='Roboto')

        # Plot setup
        self.fig, self.ax = plt.subplots(figsize=(3.5, 2.5))
        self.ax.set_facecolor("#999999")
        self.fig.set_facecolor("#999999")
        self.ax.grid(False)
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self.ax.axis('off')  # Hide the axes initially

        self.canvas = FigureCanvasTkAgg(self.fig, self.frame2)
        self.canvas.get_tk_widget().place(relx=0.5, rely=0.5, anchor='center')

        # Frame 3
        self.textbox1 = customtkinter.CTkTextbox(self, fg_color="#000000", width=200, height=200)
        self.textbox1.grid(row=0, column=1, rowspan=2, padx=(10, 20), pady=(20, 20), sticky="nsew")

        self.poll_data_queue()
        self.poll_stdout_queue()

    def poll_data_queue(self):
        try:
            x = self.data_queue.get_nowait()
            print("Received dataframe of length:", x.shape[0])
            self.update_plot(x)
        except queue.Empty:
            pass
        # Check the queue again in 1 second
        self.after(1000, self.poll_data_queue)

    def poll_stdout_queue(self):
        try:
            message = self.stdout_queue.get_nowait()
            self.textbox1.insert("end", message)  # Insert the message to the end of the textbox
            self.textbox1.see("end")
        except queue.Empty:
            pass
        self.after(1000, self.poll_stdout_queue)

    def update_plot(self, df):
        self.ax.clear()
        self.ax.axis('on')  # Show the axes
        line_styles = ['-', '--', ':', '-.']

        # Ensure the 'timestamp' column is a datetime object
        df.index = pd.to_datetime(df.index)

        # Plot each column with different line styles
        for index, column in enumerate(df.columns):
            style = line_styles[index % len(line_styles)]
            self.ax.plot(df.index, df[column], label=column, linestyle=style, color='white')

        # Set title and labels
        self.ax.set_title("Received Data", color='white', fontproperties=self.title_font_prop)
        self.ax.set_xlabel("Timestamp", color='white', fontproperties=self.label_font_prop)
        self.ax.set_ylabel("Value", color='white', fontproperties=self.label_font_prop)

        # Determine x-axis tick interval and formatting
        locator = dates.AutoDateLocator()

        # Depending on the range, determine the appropriate format
        time_range = df.index[-1] - df.index[0]
        if time_range <= pd.Timedelta(hours=1):  # less than 1 hour
            formatter = dates.DateFormatter('%H:%M')
        elif time_range <= pd.Timedelta(days=1):  # less than 1 day but more than 1 hour
            formatter = dates.DateFormatter('%H:%M')
        else:  # more than a day
            formatter = dates.DateFormatter('%m-%d')

        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)

        # Legend adjustments
        legend = self.ax.legend(loc='upper left', frameon=False)
        for text in legend.get_texts():
            text.set_color('white')
            text.set_fontproperties(self.label_font_prop)

        # Handle background and grid
        self.ax.set_facecolor("#999999")
        self.ax.grid(False)
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.tick_params(colors='white')

        # Apply font properties to tick labels
        for label in self.ax.get_xticklabels():
            label.set_fontproperties(self.label_font_prop)
        for label in self.ax.get_yticklabels():
            label.set_fontproperties(self.label_font_prop)

        # Ensure that labels and titles fit
        self.fig.tight_layout()
        self.canvas.draw()

    def clear_text(self):
        self.textbox1.delete('1.0', 'end')

    def stop_clicked(self):
        self.controller.switch_frame('PageOne')
        self.controller.disable_running_button()
        self.task.stop()
