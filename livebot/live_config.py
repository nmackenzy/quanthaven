import os
import sqlite3
import security


def config():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_directory, '..', 'bot_configuration.txt')
    db_path = os.path.join(current_directory, '..', 'database.db')
    configurations = []
    with open(config_path, 'r') as f:
        content = f.read()
        content_list = content.split('$')
        configurations.append(content_list[1])
        configurations.append(content_list[2])
        stocks_list = content_list[4].split(', ')
        configurations.append(stocks_list)
        strats_list = content_list[5].split(', ')
        configurations.append(strats_list)
        configurations.append(content_list[6])
    time_unit_string = configurations[0]
    amount = int(configurations[1])
    stocks = configurations[2]
    strategies = configurations[3]
    user_id = int(configurations[4])
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT api_key, api_secret_key, av_key FROM details WHERE user_id=?", (user_id,))
    record = c.fetchone()
    c.close()
    conn.close()

    API_KEY = security.decrypt_data(record[0], str(user_id) + 'A')
    API_SECRET_KEY = security.decrypt_data(record[1], str(user_id) + 'B')

    limit = 500

    def convert_to_base(unit, amount):
        if unit == "Day":
            return amount * 24 * 60
        elif unit == "Hour":
            return amount * 60
        elif unit == "Minute":
            return amount
        else:
            raise ValueError(f"Unsupported unit: {unit}")

    in_minutes = convert_to_base(time_unit_string, amount)

    def calculate_days_back(bars, frequency):
        trading_minutes_per_day = 6.5 * 60
        total_minutes = bars * frequency
        days = total_minutes / trading_minutes_per_day
        return int(days) + 1

    for_the_past_x_days = calculate_days_back(limit, in_minutes)
    config = [time_unit_string, amount, stocks, strategies, API_KEY, API_SECRET_KEY, in_minutes, for_the_past_x_days]
    return config