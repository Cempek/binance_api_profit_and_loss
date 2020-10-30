from binance.client import Client

# This is the class that is creted to retrieve historical price, balance details, trade history with profit and loss, and live 
import binance_class

# All tickers contains all of the cryptocurrencies and its prices. We need this list in the class argument.
# all_tickers list is created out of the class because the number of requests increases, so the error accurs. 
api_key = 'your api key'
api_secret = 'your secret key'

client = Client(api_key, api_secret)
all_tickers = client.get_all_tickers()

# Binance object is created
bnc = binance_class.binance_account(api_key,api_secret, all_tickers)
# balance method returns 2 output. first output is that all of the cryptos that we currently have.Second one includes all of the details of the balance. 
all_assets , df_balance = bnc.balance()
# order_history method returns all of the cryptos that is sold or bought at least one time.
# the method returns all BTC currencies as a defult. However, you can return the one that you want with crypto attribute.
# Important note cryptos should be written with its currency for example 'YFIBTC' or 'YFIUSDT' 
df_order_history = bnc.order_history()

df_order_history_YFII = bnc.order_history(crypto = ['YFIIBTC', 'YFIIUSDT']) 

# We used live_profit_loss method to retrieve current assests' profit and losses.
# Two input requires for this method. First is order history dataframe that we created by order_history method. Second is a list that includes the cryptos we currently have. We input all_assets list that is created by balance method, but you can input any crypto.
# Important note: The BNB returns as false 
live_profits = bnc.live_profit_loss(df_order_history , all_assets)  

live_profits_YFI = bnc.live_profit_loss(df_order_history , assets = ['YFI'])  

# Bitcoin price Visualization
bitcoin = bnc.prepare_data(interval = '1d', end_date = '2019-10-01')
bitcoin['close'].plot()

