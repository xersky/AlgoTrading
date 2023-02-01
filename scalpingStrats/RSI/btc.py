import time
import pandas as pd
import ta
import datetime
from binance.client import Client  # install the python-binance library


# Function to update values of balance after trades
def update_file(balance_var, btc_held_var):
    with open("portfolio/balance.txt", "w") as writable_balance_file:
        writable_balance_file.write(f"balance:{balance_var}\nbtc_held:{btc_held_var}")


# Import balance values from file
with open("portfolio/balance.txt", "r") as readable_balance_file:
    contents = readable_balance_file.readlines()
    for line in contents:
        variable_name, variable_value = line.strip().split(":")
        if variable_name == "balance":
            balance = float(variable_value)
        elif variable_name == "btc_held":
            btc_held = float(variable_value)

# Import keys from file
with open("keys/test_keys.txt", "r") as keys_file:
    contents = keys_file.readlines()
    for line in contents:
        variable_name, variable_value = line.strip().split(":")
        if variable_name == "api_key":
            api_key = variable_value
        elif variable_name == "api_secret":
            api_secret = variable_value

# TODO Run the script with args to chose between DiveMode and TestMode
# Using the binance testnet
Client.API_URL = Client.API_TESTNET_URL

# Authenticate with the Binance API using your API key and secret key
client = Client(api_key=api_key, api_secret=api_secret)

# Printing the account information
print(client.get_account())

# Initialize variables
trades = []  # List to store trades

# Pair to trade
symbol = 'BTCBUSD'

# Choosing the timeframe
interval = Client.KLINE_INTERVAL_1MINUTE

# Define the RSI thresholds for buying and selling
rsi_buy_threshold = 40
rsi_sell_threshold = 60

# Define the risk/reward ratio for buying
risk_reward_ratio = 1

# Open a file to store the trade history
with open('portfolio/trade_history.txt', 'a+') as f:
    # Loop indefinitely to check the RSI in real-time
    while True:
        """
        The objective of using the localtime in seconds is to eliminate the emotional part of the trade.
        
        In other words, we wait the RSI close of the 1min chart then we execute, eliminating the possibility
            to execute trades in chops/volatility in order to achieve future results similar to the ones realised
            when testing based on past data.
            Other reason, is to optimize in terms of performance and efficiency
        """
        current_time = time.localtime()
        # print(current_time.tm_sec)
        # print('looping')  # Debugging to see the frequency of the loop
        if current_time.tm_sec == 0:
            # print('inside')  # Debugging we passed the condition
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
            current_rsi = ta.momentum.rsi(df['close'], 14).__round__(2)

            # Print the RSI value
            # print(current_rsi.iloc[-1])  # (enable statement to see the values of RSI in real time)

            # Check if RSI is oversold (below RSI buy threshold) and we don't have any BTC
            if current_rsi.iloc[-1] < rsi_buy_threshold and btc_held == 0:
                # Get the current BTC price
                # ticker = client.futures_ticker(symbol=symbol)
                current_price = float(client.futures_ticker(symbol=symbol)['lastPrice'])
                # Calculate the amount to spend based on risk/reward ratio
                spend = balance / risk_reward_ratio
                # TODO Auto-manage the LOT-SIZE depends on the symbol from the Binance API
                # Calculate the number of BTC to buy based on risk/reward ratio
                btc_to_buy = round(spend / current_price, 5)
                # Place a buy order using the Binance API
                order = client.order_market_buy(symbol=symbol, quantity=btc_to_buy)
                # Deduct the cost of the BTC from the balance
                balance -= btc_to_buy * current_price
                # Update the BTC held
                btc_held += btc_to_buy
                # Update in text file
                update_file(balance, btc_held)
                # Record the trade
                trades.append({'time': datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 'type': 'buy',
                               'price': current_price, 'amount': btc_to_buy, 'rsi': current_rsi.iloc[-1],
                               'balance': balance.__round__(2)})
                print(trades[-1])
                # Write the trade details to the trade history file
                f.write(
                    f'time: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}, type: buy,'
                    f' rsi: {current_rsi.iloc[-1]}, price: ${current_price}, amount: {btc_to_buy} BTC,'
                    f' balance: ${balance.__round__(2)}, BTC held: {btc_held} BTC\n')
                f.flush()

            # Check if RSI is overbought (above RSI sell threshold) and we have some BTC
            if current_rsi.iloc[-1] > rsi_sell_threshold and btc_held > 0:
                # BTC to sell
                btc_to_sell = btc_held
                # Sell all BTC held
                order = client.order_market_sell(symbol=symbol, quantity=btc_to_sell)
                # Get the current BTC price
                # ticker = client.futures_ticker(symbol=symbol)
                current_price = float(client.futures_ticker(symbol=symbol)['lastPrice'])
                balance += btc_held * current_price
                # Reset the BTC held
                btc_held = 0
                # Update in text file
                update_file(balance, btc_held)
                # Record the trade
                trades.append(
                    {'time': datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 'type': 'sell',
                     'price': current_price, 'amount': btc_to_sell, 'rsi': current_rsi.iloc[-1],
                     'balance': balance.__round__(2)})
                print(trades[-1])
                # Write the trade details to the trade history file
                f.write(f'time: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}, type: sell,'
                        f' rsi: {current_rsi.iloc[-1]}, price: ${current_price}, amount: {btc_to_sell} BTC,'
                        f' balance: ${balance.__round__(2)}, BTC held: {btc_held} BTC\n')
                f.flush()
        # Calculating the sleeping period of the loop to be 1 min when localtime is exactly at 0 seconds
        sleeping_period = 60 - time.localtime().tm_sec
        # print(sleeping_period)  # Making sure the sleeping period is exactly 1 min for every loop
        time.sleep(sleeping_period)
