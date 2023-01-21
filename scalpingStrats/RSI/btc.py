import math
import pandas as pd
import ta
import datetime
from binance.client import Client  # install the python-binance library


# Function to update values of balance after trades
def update_file(balance_var, btc_held_var):
    with open("balance.txt", "w") as file:
        file.write(f"balance:{balance_var}\nbtc_held:{btc_held_var}")


# Initialize variables
trades = []  # List to store trades

# Import balance values from file
with open("balance.txt", "r") as file:
    contents = file.readlines()
    for line in contents:
        variable_name, variable_value = line.strip().split(":")
        if variable_name == "balance":
            balance = float(variable_value)
        elif variable_name == "btc_held":
            btc_held = float(variable_value)

# Import keys from file
with open("keys/main_keys.txt", "r") as file:
    contents = file.readlines()
    for line in contents:
        variable_name, variable_value = line.strip().split(":")
        if variable_name == "api_key":
            api_key = variable_value
        elif variable_name == "api_secret":
            api_secret = variable_value

# TODO Run the script with args to chose between DiveMode and TestMode
# Using the binance testnet
# Client.API_URL = Client.API_TESTNET_URL

# Currently diving

# Authenticate with the Binance API using your API key and secret key
client = Client(api_key=api_key, api_secret=api_secret)

# Printing the account information
print(client.get_account())

# Open a file to store the trade history
with open('trade_history.txt', 'a+') as f:
    # Loop indefinitely to check the RSI in real-time
    while True:

        symbol = 'BTCBUSD'
        # Choosing the timeframe
        interval = Client.KLINE_INTERVAL_1MINUTE

        # Retrieve the klines for the symbol and interval
        klines = client.futures_klines(symbol=symbol, interval=interval)
        # Convert the klines to a pandas DataFrame
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                           'quote_asset_volume', 'trades', 'taker_buy_base_asset_volume',
                                           'taker_buy_quote_asset_volume', 'ignore'])

        # Convert the timestamp column to a datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate the RSI for the close column
        df['close'] = pd.to_numeric(df['close'])
        current_rsi = ta.momentum.rsi(df['close'], 14)

        # Print the RSI value
        # print(current_rsi.iloc[-1]) (enable statement to see the values of RSI in real time)

        # Check if RSI is oversold (below 40) and we don't have any BTC
        if current_rsi.iloc[-1] < 40 and btc_held == 0:
            # Get the current BTC price
            ticker = client.futures_ticker(symbol=symbol)
            current_price = float(ticker['lastPrice'])
            # TODO Auto-manage the LOT-SIZE depends on the symbol from the Binance API
            # Calculate the number of BTC to buy based on risk/reward ratio
            btc_to_buy = round(balance / current_price, 5)
            # Place a buy order using the Binance API
            order = client.order_market_buy(symbol=symbol, quantity=btc_to_buy)
            # Deduct the cost of the BTC from the balance
            balance -= btc_to_buy * current_price
            # Update the BTC held
            btc_held += btc_to_buy
            # Update in text file
            update_file(balance, btc_held)
            # Record the trade
            trades.append({'time': datetime.datetime.now(), 'type': 'buy', 'price': current_price, 'amount': btc_to_buy,
                           'balance': balance})
            print({'time': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), 'type': 'buy', 'price': current_price,
                   'amount': btc_to_buy, 'balance': balance})
            # Write the trade details to the trade history file
            f.write(
                f'time: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}, type: buy, price: ${current_price}, '
                f'amount: {btc_to_buy} BTC, balance: ${balance}, BTC held: {btc_held} BTC\n')
            f.flush()

        # Check if RSI is overbought (above 60) and we have some BTC
        if current_rsi.iloc[-1] > 60 and btc_held > 0:
            # BTC to sell
            btc_to_sell = btc_held
            # Sell all BTC held
            order = client.order_market_sell(symbol=symbol, quantity=btc_to_sell)
            # Get the current BTC price
            ticker = client.futures_ticker(symbol=symbol)
            current_price = float(ticker['lastPrice'])
            balance += btc_held * current_price
            # Reset the BTC held
            btc_held = 0
            # Update in text file
            update_file(balance, btc_held)
            # Record the trade
            trades.append(
                {'time': datetime.datetime.now(), 'type': 'sell', 'price': current_price, 'amount': btc_to_sell,
                 'balance': balance})
            print({'time': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), 'type': 'sell', 'price': current_price,
                   'amount': btc_to_sell, 'balance': balance})
            # Write the trade details to the trade history file
            f.write(
                f'time: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}, type: sell, price: ${current_price}, '
                f'amount: {btc_to_sell} BTC, balance: ${balance}, BTC held: {btc_held} BTC\n')
            f.flush()
