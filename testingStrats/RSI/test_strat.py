import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import datetime

# Load the data
df = pd.read_csv('../BinanceMarketData/klines/BTC/1m/BTCBUSD-1m-#-2019-09-to-2022-12.csv')

# Set klines columns of df
df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'trades',
              'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']

# Calculate the RSI
df['rsi'] = ta.momentum.rsi(df['close'], 14)

# Initialize variables
balance = 100  # Balance
btc_held = 0  # Number of BTC held
trades = []  # List to store trades
starting_balance = balance  # Starting balance

# Define the RSI thresholds for buying and selling
rsi_buy_threshold = 40
rsi_sell_threshold = 60

# Define the risk/reward ratio for buying
risk_reward_ratio = 1

# Loop through the data
for i in range(1, len(df)):
    # Check if RSI is oversold (below RSI buy threshold) and we don't have any BTC
    if df.loc[i, 'rsi'] < rsi_buy_threshold and btc_held == 0:
        # Calculate the amount to spend based on risk/reward ratio
        spend = balance / risk_reward_ratio
        # Calculate the number of BTC to buy
        btc_to_buy = spend / df.loc[i, 'close']
        # Deduct the cost of the BTC from the balance
        balance -= btc_to_buy * df.loc[i, 'close']
        # Update the BTC held
        btc_held += btc_to_buy
        # Record the trade
        trades.append(
            {'timestamp': df.loc[i, 'timestamp'], 'type': 'buy', 'price': df.loc[i, 'close'],
             'rsi': df.loc[i, 'rsi'].__round__(2), 'amount': btc_to_buy, 'balance': balance})

    # Check if RSI is overbought (above RSI sell threshold) and we have some BTC
    if df.loc[i, 'rsi'] > rsi_sell_threshold and btc_held > 0:
        # BTC to sell
        btc_to_sell = btc_held
        # Sell all BTC held
        balance += btc_held * df.loc[i, 'close']
        # Update the number of BTC held
        btc_held = 0
        # Record the trade
        trades.append(
            {'timestamp': df.loc[i, 'timestamp'], 'type': 'sell', 'price': df.loc[i, 'close'],
             'rsi': df.loc[i, 'rsi'].__round__(2), 'amount': btc_to_buy, 'balance': balance})

# Convert the trades list into a DataFrame for analysis
trades_df = pd.DataFrame(trades)

with open("output.txt", "w") as txt_file:
    for item in trades:
        # write each item on a new line
        txt_file.write("%s\n" % item)

# Retrieving the ATL_balance Balance, index and price
ATL_balance = min(trades_df.iloc[1::2]['balance'])
ATL_index = trades_df.iloc[1::2]['balance'].idxmin()
ATL_price = trades[ATL_index]['price']

# ATH that comes after the ATL
ATH_balance = max(trades_df.iloc[ATL_index::2]['balance'])
ATH_index = trades_df.iloc[ATL_index::2]['balance'].idxmax()
ATH_price = trades[ATH_index]['price']

# ATL Date
ATL_date = trades[ATL_index]['timestamp']
# ATH Date
ATH_date = trades[ATH_index]['timestamp']

print('RSI Range:')
print('[ ', rsi_buy_threshold, ' - ', rsi_sell_threshold, ' ]')
print()
print('Portfolio Data:')
print('Starting Balance: $', starting_balance, ' - BTC Price: $', trades[0]['price'], ' - at: ',
      datetime.fromtimestamp(trades[0]['timestamp'] / 1000).strftime("%d/%m/%Y %H:%M:%S"))
print('Portfolio ATL: $', ATL_balance.__round__(2), ' - BTC Price: $', ATL_price, ' - at: ',
      datetime.fromtimestamp(ATL_date / 1000).strftime("%d/%m/%Y %H:%M:%S"))
print('Portfolio ATH: $', ATH_balance.__round__(2), ' - BTC Price: $', ATH_price, ' - at: ',
      datetime.fromtimestamp(ATH_date / 1000).strftime("%d/%m/%Y %H:%M:%S"))
print('Final portfolio balance: $', trades[-1]['balance'].__round__(2), ' - BTC Price: $', trades[-1]['price'],
      ' - at: ', datetime.fromtimestamp(trades[-1]['timestamp'] / 1000).strftime("%d/%m/%Y %H:%M:%S"))
print()
print('RSI Strategy vs BTC: ')
print('Balance if just held BTC: $', (trades[0]['amount'] * trades[-1]['price']).__round__(2))
print('Balance if sold at ATH: $', (trades[0]['amount'] * ATH_price).__round__(2))
print('Balance if bought at ATL and sold at ATH: $',
      ((starting_balance / ATL_price) * ATH_price).__round__(2))

# Calculate the cost of buying the bitcoins at each trade
trades_df['time'] = pd.to_datetime(trades_df['timestamp'], unit='ms')
trades_df['date'] = trades_df['time'].dt.date

plt.subplot(1, 2, 1)  # row 1, col 2 index 1
plt.plot(trades_df['date'], trades_df['amount'])
plt.title("Portfolio in BTC over time")
plt.xlabel('Date')
plt.ylabel('Balance in BTC')
plt.xticks(rotation=90)

plt.subplot(1, 2, 2)  # index 2
plt.plot(trades_df.iloc[1::2]['date'], trades_df.iloc[1::2]['balance'])
plt.xlabel('Date')
plt.ylabel('Balance $')
plt.title('Portfolio balance overtime')
plt.xticks(rotation=90)
plt.show()
