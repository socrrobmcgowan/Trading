import pandas as pd
import numpy as np
import pandas_datareader as web
import requests
import datetime
import time

is_long = False
is_short = False

today = datetime.date.today()
quote_start = datetime.time(8,30,0)
trading_start = datetime.time(8,30,0)
trading_end = datetime.time(14,57,0)
now = datetime.datetime.now().time()
now = datetime.datetime.now().time()

longs = []
shorts = []
long_closes = []
short_closes = []

symbol = 'SPY'


def get_data(symbol):
    data = web.robinhood.RobinhoodQuoteReader(symbol)
    curr_price = float(data.read().transpose()['last_trade_price'][symbol])
    df_new = pd.DataFrame({'Price':float(curr_price),'change':float(), 'gains' : float(), 'losses' : float(), 'rs': float(), 'rsi': float()}, index = [now])
    return df_new

def RSI(last_avg_gain, last_avg_loss):

    if df['change'][now] > 0:
        gain = df['change'][now]
        loss = float(0.0)
    elif df['change'][now] < 0:
        loss = abs(df['change'][now])
        gain = float(0.0)
    else:
        gain = float(0.0)
        loss = float(0.0)
    avg_gain = ((last_avg_gain*13)+gain)/14
    avg_loss = ((last_avg_loss*13)+loss)/14
    rs = avg_gain/avg_loss
    rsi = 100 - (100/(1.0+rs))

    return {'rsi' : rsi, 'gain' : gain, 'loss' : loss, 'last_price' : df['Price'][now]}
    


#BEFORE DATA COLLECTION
print('Program Started. Not Collecting Data Yet.')


now = datetime.datetime.now().time()
print(now)

while not now >= quote_start:
    time.sleep(0.50)
    now = datetime.datetime.now().time()

df = pd.DataFrame()

print(now)

print('Market has opened! Now Collecting First RSI Data.')



#COLLECING FIRST RSI DATA - 14 Minutes or 420, 1 minutue periods. 


   
first_14 = 15


while first_14 > 0 :

    second = datetime.datetime.now().second
    if second == 0  :
        now = datetime.datetime.now().time()
        df_new = get_data(symbol = symbol)
        df = pd.concat([df,df_new],axis = 0)
        df['change'] = df['Price'] - df['Price'].shift(1)
        
        if df['change'][now] > 0:
            df['gains'][now] = df['change'][now]
            df['losses'][now] = float(0.0)
        elif df['change'][now] < 0:
            df['losses'][now] = abs(df['change'][now])
            df['gains'][now] = float(0.0)
        else:
            df['gains'][now] = float(0.0)
            df['losses'][now] = float(0.0)

        df['ma_60'] = df['Price'].rolling(60).mean()
        df['ma_60_slope'] = df['ma_60']-df['ma_60'].shift(1)
        df['ma_30'] = df['Price'].rolling(30).mean()
        df['avg_gain'] = df['gains'].rolling(14).mean()
        df['avg_loss'] = df['losses'].rolling(14).mean()
        df['rs'][now] = df['avg_gain'][now]/df['avg_loss'][now]
        df['rsi'][now] = 100 - (100/(1+df['rs'][now]))
        df['rsi_ma'] = df['rsi'].rolling(30).mean()
        df['rsi_div'] = df['rsi_ma'] - df['rsi_ma'].shift(1)
        df['price_div'] = df['ma_30'] - df['ma_30'].shift(1)
        
        last_avg_gain = df['avg_gain'][now]
        last_avg_loss = df['avg_loss'][now]
        last_price = df['Price'][now]
        first_14 += -1
        time.sleep(0.92)
    else:
        time.sleep(0.92)
    
#ONCE TRADING STARTS

print('We have data for the 14 mins Let the trading begin!')


while now < trading_end :

    second = datetime.datetime.now().second # every minute tick to record RSI and bullish/bearish indicator using minute data
    if second == 0  :
        now = datetime.datetime.now().time()
        df_new = get_data(symbol = symbol)
        df = pd.concat([df,df_new])
        df['change'] = df['Price'] - df['Price'].shift(1)
        curr_price = df['Price'][now]
    
        rsi_d = RSI(last_avg_gain = last_avg_gain, last_avg_loss = last_avg_loss)

        df['gains'][now] = rsi_d['gain']
        df['losses'][now] = rsi_d['loss']
        df['avg_gain'] = df['gains'].rolling(14).mean()
        df['avg_loss'] = abs(df['losses'].rolling(14).mean())
        df['ma_60'] = df['Price'].rolling(window = 60).mean()
        df['ma_60_slope'] = df['ma_60']-df['ma_60'].shift(1)
        df['ma_30'] = df['Price'].rolling(30).mean()
        df['rsi'][now] = rsi_d['rsi']
        df['rsi_ma'] = df['rsi'].rolling(30).mean()
        df['rsi_div'] = df['rsi'] - df['rsi'].shift(8)
        df['price_div'] = df['Price'] - df['Price'].shift(8)   
        
        
        last_avg_gain = df['avg_gain'][now]
        last_avg_loss = df['avg_loss'][now]
        last_price = df['Price'][now]

    else:               # for intra minute action
        df_s = get_data(symbol = symbol)
        curr_price = df_s['Price'][now]
        change = df_s['Price'][now] - df['Price'][now]
        if change > 0 :
            gain = float(change)
            loss = float(0.0)
        elif change < 0 :
            loss = abs(float(change))
            gain = float(0.0)
        else:
            gain = float(0.0)
            loss = float(0.0)
        avg_gain = ((last_avg_gain*13)+gain)/14
        avg_loss = ((last_avg_loss*13)+loss)/14
        rs = avg_gain/avg_loss
        rsi = 100 - (100/(1.0+rs))
        rsi_ma = (rsi + (df['rsi_ma'][now]*29))/30
        rsi_div = rsi - df['rsi'].shift(8)[now]
        ma_30 = (curr_price + (df['ma_30'][now]*29))/30
        price_div = curr_price - df['Price'].shift(8)[now]

        
        if rsi < 30 and price_div < 0 and rsi_div > 0 and not is_long and not is_short:
            print('Open Long Position in ' + symbol+' @ ' + str(curr_price))
            long_enter = float(curr_price)
            long_stop = float(curr_price - 0.10)
            longs.append((now, curr_price))
            is_long = True
            long_stops = []
            long_stops.append(long_stop)
        elif rsi > 70 and price_div > 0 and rsi_div < 0 and not is_long and not is_short:
            print('Open Short Position in ' + symbol+' @ ' + str(curr_price))
            short_enter = float(curr_price)
            short_stop = float(curr_price + 0.10)
            shorts.append((now, curr_price))
            is_short = True
            short_stops = []
            short_stops.append(short_stop)

    if df['rsi'][now] < 30 and df['price_div'][now] < 0 and df['rsi_div'][now] > 0 and not is_long and not is_short:
        print('Open Long Position in ' + symbol+' @ ' + str(curr_price))
        long_enter = float(curr_price)
        long_stop = float(curr_price - 0.10)
        longs.append((now, curr_price))
        is_long = True
        long_stops = []
        long_stops.append(long_stop)
    elif df['rsi'][now] > 70 and df['price_div'][now] > 0 and df['rsi_div'][now] < 0 and not is_long and not is_short:
        print('Open Short Position in ' + symbol+' @ ' + str(curr_price))
        short_enter = float(curr_price)
        short_stop = float(curr_price + 0.10)
        shorts.append((now, curr_price))
        is_short = True
        short_stops = []
        short_stops.append(short_stop)
    elif is_long and curr_price <= long_stop :
        print('Close Long ' +symbol+' Position @ ' + str(curr_price))
        long_closes.append((now, curr_price))
        is_long = False
    elif is_long and (curr_price - long_enter) > 0.10 :
        if len(long_stops) == 1:
            long_stop += float((curr_price - long_enter)+0.05)
            long_stops.append(long_stop)
            print('moving stop up to ' + str(long_stop))
        else:
            long_stop += float(curr_price - long_enter)
            long_stops.append(long_stop)
            print('moving stop up to ' + str(long_stop))
        long_enter += float(curr_price - long_enter)
    elif is_short and (curr_price - short_enter) < -0.10:
        if len(short_stops) == 1:
            short_stop += float((curr_price - short_enter)-0.05)
            short_stops.append(short_stop)
            print('moving stop down to ' + str(short_stop))
        else :
            short_stop += float(curr_price - short_enter)
            short_stops.append(short_stop)
            print('moving stop down to ' + str(short_stop))
        short_enter += float(curr_price - short_enter)
    elif is_short and curr_price >= short_stop:
        print('Close Short ' +symbol+' Position @ ' + str(curr_price))
        short_closes.append((now, curr_price))
        is_short = False

    time.sleep(0.79)

if is_long:
    print('Closing Long Position for End of Day')
    is_long = False
    long_closes.append((now, df['Price'][now]))

elif is_short:
    print('Closing Short Position for End of Day')
    is_short = False
    short_closes.append((now, df['Price'][now]))
else:
    print('Done Trading for Today')

df.to_csv('/Users/robbiemcgowan/Documents/trading_data/trading_data_df_'+str(today)+'.csv')
long_df = pd.DataFrame(longs, columns = ['Time','Price'])
long_df.set_index('Time' , inplace = True)
short_df = pd.DataFrame(shorts, columns = ['Time','Price'])
short_df.set_index('Time' , inplace = True)
long_closes_df = pd.DataFrame(long_closes, columns = ['Time','Price'])
long_closes_df.set_index('Time' , inplace = True)
short_closes_df = pd.DataFrame(short_closes, columns = ['Time','Price'])
short_closes_df.set_index('Time' , inplace = True)
long_df.to_csv('/Users/robbiemcgowan/Documents/trading_data/longs_'+str(today)+'.csv')
short_df.to_csv('/Users/robbiemcgowan/Documents/trading_data/shorts_'+str(today)+'.csv')
long_closes_df.to_csv('/Users/robbiemcgowan/Documents/trading_data/long_closes_'+str(today)+'.csv')
short_closes_df.to_csv('/Users/robbiemcgowan/Documents/trading_data/short_closes_'+str(today)+'.csv')
