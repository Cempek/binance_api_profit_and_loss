from datetime import datetime
import pandas as pd
from binance.client import Client 
import re


class binance_account(Client):
    '''
    
    Important not: Binance limitted to 1200 requests per minute, so if you run all of them together, you can face some errors.
    This class has 4 functions which are prepare_data, balance, order_history, and live_profit_loss.
    prepare_data : This function is created to retrieve the historical cryptocurrency price with its high, low, close prices, and its volumes in the dataframe.
    balance : This function returns all the cryptocurrencies with its current balances.
    order_history : This function returns all of your trade history that you make with BTC with your profits and your losses in percentage, BTC and USD. If you don't input any argument, it will return all cryptos that you sell or buy with BTC.
    ** order_history method will return just transactions that you made with BTC because of request limitation per minute. However, instead, you can input the list that includes the ones you make with USDT or ETH.
    live_profit_loss = This function returns your current assets' profits losses. You can input the assets that are retrieved by balance method or you can just input the list of cryptocurrencies that you want to learn you average cost and its current profit and losses. 
    
    attrubutes:
        api_key : your api key from the binance
        api_secret : your api secret from the binance
        all_tickers : all the cryptocurrencies in Bianance. For example: 'YFIUSD', 'YFIUSDT' ,'QSPBTC' 
    '''
    
    def __init__(self, api_key, api_secret, all_tickers):
        
        self.client = Client(api_key,api_secret)
        self.all_tickers = all_tickers
        self.all_tickers_keys = [i['symbol'] for i in self.all_tickers]
    
    # Get historical data
    def prepare_data(self,coin = 'BTCUSDT',interval = '1d', beginning_date = '2020-01-01 00:01:00', end_date = 'now'):    
        # time intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    

        if end_date== 'now':
            end_date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        else:
            pass

        raw_historical = self.client.get_historical_klines(coin, interval, beginning_date,end_date)
          
        df_coin = pd.DataFrame(raw_historical, columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quate_asset_volume', 'no_trades', 'base_asset_volume', 'quote_asset_volume', 'ignore'])
        
        df_coin['date'] = df_coin['date'].apply(lambda x: datetime.strftime(datetime.fromtimestamp(x/1000), '%Y-%m-%d %H:%M:%S') )
        df_coin['close_time'] = df_coin['close_time'].apply(lambda x: datetime.strftime(datetime.fromtimestamp(x/1000), '%Y-%m-%d %H:%M:%S'))
        df_coin['date'] = pd.to_datetime(df_coin['date'])
        df_coin['close_time'] = pd.to_datetime(df_coin['close_time'])
        
        df_coin[['open', 'high', 'low', 'close','volume', 'quate_asset_volume','base_asset_volume','quote_asset_volume','ignore']] = df_coin[['open', 'high', 'low', 'close','volume', 'quate_asset_volume','base_asset_volume','quote_asset_volume','ignore']].astype(float)
    
        df_coin.set_index('date', inplace = True)
        df_coin.index = pd.DatetimeIndex(df_coin.index)
        return df_coin

    # Balance Detail 
    def balance(self):
        df_balance = {'crypto' : [] , 'free' : [], 'locked' : [], 'total' : [], 'price_in_BTC' : [] , 'total_in_BTC' : [] , 'total_in_USD' : []}
        df_balance = pd.DataFrame(df_balance)
        balance_detail = self.client.get_account()['balances']
        idx = 0
        for asset in balance_detail: 
            df_balance.loc[idx,'crypto'] = asset['asset']
            df_balance.loc[idx, 'free'] = float(asset['free'])
            df_balance.loc[idx, 'locked'] = float(asset['locked'])
            df_balance.loc[idx, 'total'] = float(asset['free']) + float(asset['locked'])
            if asset['asset'] == 'BTC':
                df_balance.loc[idx, 'price_in_BTC'] = float(asset['free']) + float(asset['locked'])
            elif asset['asset'] + 'BTC' in self.all_tickers_keys:
                df_balance.loc[idx, 'price_in_BTC'] = float(self.client.get_symbol_ticker(symbol = str(asset['asset']) + 'BTC')['price'])
            else:
                df_balance.loc[idx, 'price_in_BTC'] = 0
            if df_balance.loc[idx, 'total'] > 0:
                if asset['asset'] == 'BTC':      
                    df_balance.loc[idx, 'total_in_BTC'] = float(asset['free']) + float(asset['locked'])
                    df_balance.loc[idx, 'total_in_USD'] = df_balance.loc[idx, 'total_in_BTC'] * float(self.client.get_symbol_ticker(symbol = 'BTCUSDT')['price'])
                else:
                    df_balance.loc[idx, 'total_in_BTC'] = (float(asset['free']) + float(asset['locked'])) * float(self.client.get_symbol_ticker(symbol = asset['asset'] + 'BTC')['price'])
                    df_balance.loc[idx, 'total_in_USD'] = df_balance.loc[idx, 'total_in_BTC'] * float(self.client.get_symbol_ticker(symbol = 'BTCUSDT')['price'])
            else:
                df_balance.loc[idx, 'total_in_BTC'] = 0
                df_balance.loc[idx, 'total_in_USD'] = 0 
            idx +=1
        all_assets =list( df_balance[df_balance['total'] > 0]['crypto'])
        return all_assets, df_balance
    
    
    # Profit - Loss 
    def order_history(self , crypto = 'all' ):
        
        df_profit_loss = {'order_id' : [0] ,'timestamp' : [0], 'date' : [0], 'crypto' : [''], 'status' : [''], 'price' : [0], 'quantity': [0],'total_quantity' : [0], 'average_cost' : [0] , 'profit_loss_percent' :[0], 'profit_loss_BTC': [0] , 'profit_loss_USD' : [0], 'profit_loss_USD2' : [0], 'total_$_paid' : [0]}
        df_profit_loss = pd.DataFrame(df_profit_loss)
        historical_assets = []
        # All the cryptos that has exchanges with BTC    
        if crypto == 'all':
            BTC_assets = []
            for i in self.all_tickers_keys:
                result = re.findall(r'\BBTC', i)
                if len(result) == 1:
                    BTC_assets.append(i)
            
            # We try to find all the cryptocurrencies that we sell or buy with BTC at least one time.
            for i in BTC_assets:
                if len(self.client.get_all_orders(symbol = i)) > 0:
                    historical_assets.append(i)
        # It you input the cryptocurrencies that you buy or sell with USD, BTC, ETH or another currency, it will copy the list and find all balances.
        else:
            historical_assets = crypto.copy()
    
        idx = 1
        for asset in historical_assets:
            current_asset_history = self.client.get_all_orders(symbol = asset)
            for order in current_asset_history:
                if order['status'] == 'FILLED':
                    df_profit_loss.loc[idx, 'order_id'] = int(order['orderId'])
                    df_profit_loss.loc[idx, 'timestamp'] = int(order['time'] )
                    df_profit_loss.loc[idx, 'date'] = datetime.fromtimestamp(order['time'] / 1000) 
                    df_profit_loss.loc[idx, 'crypto'] = order['symbol']
                    order_time = datetime.strftime(df_profit_loss.loc[idx, 'date'], "%Y-%m-%d %H:%M")
                    btc_price = float(self.client.get_historical_klines('BTCUSDT',self.client.KLINE_INTERVAL_1MINUTE , order_time, order_time)[0][4])
                    if order['side'] == 'BUY':
                        if df_profit_loss.loc[idx-1, 'total_quantity'] == 0:
                            df_profit_loss.loc[idx, 'price'] = float(order['price'])
                            df_profit_loss.loc[idx, 'quantity'] = float(order['origQty'])
                            df_profit_loss.loc[idx, 'total_quantity'] = float(order['origQty'])
                            df_profit_loss.loc[idx, 'total_$_paid'] = -(df_profit_loss.loc[idx, 'quantity'] * df_profit_loss.loc[idx, 'price'] * btc_price)
                            df_profit_loss.loc[idx, 'average_cost'] = float(order['price']) 
                            df_profit_loss.loc[idx, 'status'] = order['side']
                            df_profit_loss.loc[idx, 'profit_loss_percent'] = 0
                            df_profit_loss.loc[idx, 'profit_loss_BTC'] = 0
                            df_profit_loss.loc[idx, 'profit_loss_USD'] = 0 
                            df_profit_loss.loc[idx, 'profit_loss_USD2'] =0
                            
                        elif df_profit_loss.loc[idx-1, 'total_quantity'] > 0:
                            df_profit_loss.loc[idx, 'price'] = float(order['price'])
                            df_profit_loss.loc[idx, 'quantity'] = float(order['origQty'])
                            df_profit_loss.loc[idx, 'total_quantity'] = (df_profit_loss.loc[idx-1, 'total_quantity'] + float(order['origQty'])) 
                            df_profit_loss.loc[idx, 'total_$_paid'] =  (df_profit_loss.loc[idx -1, 'total_$_paid'] - ( df_profit_loss.loc[idx, 'quantity'] * df_profit_loss.loc[idx, 'price'] * btc_price))
                            df_profit_loss.loc[idx, 'average_cost'] = ((float(order['price']) * float(order['origQty'])) + (df_profit_loss.loc[idx-1, 'total_quantity'] * df_profit_loss.loc[idx-1, 'average_cost'])) / (df_profit_loss.loc[idx-1, 'total_quantity'] + float(order['origQty']))                    
                            df_profit_loss.loc[idx, 'status'] = order['side']                    
                            df_profit_loss.loc[idx, 'profit_loss_percent'] = 0
                            df_profit_loss.loc[idx, 'profit_loss_BTC'] = 0
                            df_profit_loss.loc[idx, 'profit_loss_USD'] = 0
                            df_profit_loss.loc[idx, 'profit_loss_USD2'] =0
                            
                    if order['side'] == 'SELL':
                        if df_profit_loss.loc[idx-1, 'total_quantity'] == 0:
                            df_profit_loss.loc[idx, 'price'] = float(order['price'])
                            df_profit_loss.loc[idx, 'quantity'] = float(order['origQty'])
                            df_profit_loss.loc[idx, 'total_quantity'] = float(order['origQty'])
                            df_profit_loss.loc[idx, 'average_cost'] = float(order['price']) 
                            df_profit_loss.loc[idx, 'status'] = order['side']
                            df_profit_loss.loc[idx, 'profit_loss_percent'] = (df_profit_loss.loc[idx,'price'] - df_profit_loss.loc[idx-1, 'average_cost'])  / df_profit_loss.loc[idx,'price'] * 100
                            df_profit_loss.loc[idx, 'profit_loss_BTC'] = df_profit_loss.loc[idx,'price'] * df_profit_loss.loc[idx, 'quantity']
                            df_profit_loss.loc[idx, 'profit_loss_USD'] = (df_profit_loss.loc[idx,'price'] - df_profit_loss.loc[idx-1, 'average_cost']) * df_profit_loss.loc[idx, 'quantity'] * btc_price 
                        elif df_profit_loss.loc[idx-1, 'total_quantity'] > 0:
                            df_profit_loss.loc[idx, 'price'] = float(order['price'])
                            df_profit_loss.loc[idx, 'quantity'] = float(order['origQty'])
                            df_profit_loss.loc[idx, 'total_quantity'] = (df_profit_loss.loc[idx-1, 'total_quantity'] - float(order['origQty'])) 
                           
                            if df_profit_loss.loc[idx, 'total_quantity'] == 0:
                                df_profit_loss.loc[idx, 'average_cost'] = 0
                                df_profit_loss.loc[idx, 'profit_loss_USD2'] = df_profit_loss.loc[idx - 1 , 'total_$_paid'] + ( df_profit_loss.loc[idx, 'quantity']* df_profit_loss.loc[idx, 'price'] * btc_price)
                                df_profit_loss.loc[idx, 'total_$_paid'] = 0
                            else:    
                                df_profit_loss.loc[idx, 'average_cost'] = df_profit_loss.loc[idx-1,'average_cost'] 
                                df_profit_loss.loc[idx, 'profit_loss_USD2'] =0
                                df_profit_loss.loc[idx, 'total_$_paid'] = df_profit_loss.loc[idx - 1 , 'total_$_paid'] + ( df_profit_loss.loc[idx, 'quantity'] * df_profit_loss.loc[idx, 'price'] * btc_price)
                            df_profit_loss.loc[idx, 'status'] = order['side']                    
                            df_profit_loss.loc[idx, 'profit_loss_percent'] =  (df_profit_loss.loc[idx,'price'] - df_profit_loss.loc[idx-1, 'average_cost'])  / df_profit_loss.loc[idx,'price'] * 100
                            df_profit_loss.loc[idx, 'profit_loss_BTC'] =  df_profit_loss.loc[idx,'price'] * df_profit_loss.loc[idx, 'quantity']
                            df_profit_loss.loc[idx, 'profit_loss_USD'] = (df_profit_loss.loc[idx,'price'] - df_profit_loss.loc[idx-1, 'average_cost']) * df_profit_loss.loc[idx, 'quantity'] * btc_price
                    idx +=1
                    
            df_profit_loss.loc[idx] = list(pd.Series( {'order_id' : 0.0 ,'timestamp' : 0, 'date' : 0.0, 'crypto' :'', 'price' : 0.0, 'quantity': 0.0,'total_quantity' : 0.0, 'average_cost' : 0.0, 'status' : '' , 'profit_loss_percent' :0.0, 'profit_loss_BTC': 0.0 , 'profit_loss_USD' : 0.0,'profit_loss_USD2' : [0], 'total_$_paid' : [0]}))
            idx += 1
        df_profit_loss = df_profit_loss[df_profit_loss['order_id'] != 0].reset_index(drop = True)
        return df_profit_loss
                    
    
    
    def live_profit_loss(self, order_history ,assets):
    
        current_assets_profit_loss = { 'crypto' : [],'order_date' : [], 'order_cost' :[], 'current_date': [], 'current_price' : [] , 'quantity' : [], 'profit_loss_%' :[],'profit_loss_$':[], 'total_USD': []}
        current_assets_profit_loss = pd.DataFrame(current_assets_profit_loss)
        recent_transactions_timestamps = list(order_history.groupby('crypto')['timestamp'].max())
        
        current_assets_average_costs = order_history[(order_history['timestamp'].isin(recent_transactions_timestamps))].reset_index(drop= True)
        idx = 0
        for asset in assets:
            if str(asset) + 'BTC' in (list(current_assets_average_costs['crypto'])):

                current_assets_profit_loss.loc[idx, 'current_date'] = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
                order_date = pd.to_datetime(current_assets_average_costs[current_assets_average_costs['crypto'] == str(asset) + 'BTC'].loc[:,'date' ].reset_index(drop = True)[0])
                current_assets_profit_loss.loc[idx, 'order_date'] = datetime.strftime(order_date, '%Y-%m-%d %H:%M')
                current_assets_profit_loss.loc[idx,'crypto'] = asset
                current_assets_profit_loss.loc[idx,'order_cost'] = float( current_assets_average_costs[current_assets_average_costs['crypto'] == str(asset) + 'BTC'].loc[:,'average_cost' ])
                current_assets_profit_loss.loc[idx , 'current_price'] = float(self.client.get_symbol_ticker(symbol = asset + 'BTC')['price'])
                current_assets_profit_loss.loc[idx, 'quantity'] = float(current_assets_average_costs[current_assets_average_costs['crypto'] == str(asset)+ 'BTC'].loc[:,'total_quantity'])
                current_assets_profit_loss.loc[idx, 'profit_loss_%'] = (current_assets_profit_loss.loc[idx, 'current_price'] - current_assets_profit_loss.loc[idx , 'order_cost'] ) / current_assets_profit_loss.loc[idx, 'order_cost'] * 100
                current_assets_profit_loss.loc[idx, 'profit_loss_$'] = (current_assets_profit_loss.loc[idx, 'current_price'] * current_assets_profit_loss.loc[idx, 'quantity'] * float(self.client.get_symbol_ticker(symbol = 'BTCUSDT')['price'])) - (current_assets_profit_loss.loc[idx, 'order_cost'] * current_assets_profit_loss.loc[idx, 'quantity'] * float(self.client.get_historical_klines('BTCUSDT',self.client.KLINE_INTERVAL_1MINUTE , current_assets_profit_loss.loc[idx, 'order_date'], current_assets_profit_loss.loc[idx, 'order_date'])[0][4]))
                current_assets_profit_loss.loc[idx, 'total_USD'] = current_assets_profit_loss.loc[idx, 'current_price'] * current_assets_profit_loss.loc[idx, 'quantity'] *  float(self.client.get_symbol_ticker(symbol = 'BTCUSDT')['price'])
                idx +=1
                
    
            else:
                print('{} cannot be retrieved.'.format(asset))
        return current_assets_profit_loss


