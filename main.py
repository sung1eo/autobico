import configparser
from datetime import date
import datetime
import pyupbit
import numpy as np

config = configparser.ConfigParser()
config.read(r"config/config.ini")

access_key = config['DEFAULT']['ACCESS_KEY'] 
secret_key = config['DEFAULT']['SECRET_KEY'] 

#print(access_key)
#print(secret_key)
#print(pyupbit.get_tickers(fiat="KRW"))

ticker_BTC = "KRW-BTC" #비트코인
ticker_ETC = "KRW-ETC" #이더리움 클래식
ticker_QTUM = "KRW-QTUM" #퀀텀
ticker_EOS = "KRW-EOS" #EOS

# #print(pyupbit.get_current_price(ticker_BTC))
# upbit = pyupbit.Upbit(access_key, secret_key)
# coin_volume = 0.13
# krw = 10000

# print(upbit.get_balances())
# # upbit.sell_market_order(ticker_ETC, coin_volume*0.9995)
# # print(upbit.get_balances())

# def get_order_uuid(ticker):
#     orders = upbit.get_order(ticker, state="done")
#     print(orders)
#     uuid = orders['uuid']
#     return uuid

# get_order_uuid(ticker_ETC)
#upbit.buy_market_order(ticker_ETC, krw*0.9995)
#coin_volume = upbit.get_order(get_order_uuid(ticker=ticker_ETC))['volume']
#print(coin_volume)

#df = pyupbit.get_ohlcv(ticker_ETC, interval = 'minutes240', count=200)

# df = pyupbit.get_ohlcv(ticker_ETC, interval = 'minutes30', count=800)

# if df.index[-1].minute != 30:
#   df = df.iloc[:-1] # 시간 정각은 제외한다

# c = [-1-(i*8) for i in range(0,100)]
# df = df.iloc[c] # 4시간 간격으로 자름


# df['range'] = (df['high'] - df['low']) * 0.5
# df['target'] = df['open'] + df['range'].shift(1)

# df['ror'] = np.where(df['high'] > df['target'], df['close'] / df['target'],1)

# ror = df['ror'].cumprod()[-2]
# print("누적수익률:", ror, sep=' ')

# fee = 0.0032
# df['ror_fee'] = np.where(df['high'] > df['target'], df['close'] / df['target'] - fee, 1)

# ror_fee = df['ror_fee'].cumprod()[-2] # 하나 윗 컬럼
  
# df['hpr'] = df['ror'].cumprod()
# df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100

# print("MDD(%): ", df['dd'].max())
# print("누적수익률(fee고려):", ror_fee, sep=' ')

#print(df.tail(10))
#print(df.head(10))


def get_ror(k, ticker):
  #df = pyupbit.get_ohlcv(ticker, interval = 'minutes240', count=200)
  df = pyupbit.get_ohlcv(ticker, interval = 'minutes30', count=800)

  if df.index[-1].minute != 30:
    df = df.iloc[:-1] # 시간 정각은 제외한다
  
  c = [-1-(i*8) for i in range(0,100)]
  df = df.iloc[c] # 4시간 간격으로 자름

  df['range'] = (df['high'] - df['low']) * k
  df['target'] = df['open'] + df['range'].shift(1) 

  fee = 0.0032
  df['ror'] = np.where(df['high'] > df['target'],df['close'] / df['target'] - fee, 1)
  ror = df['ror'].cumprod()[-2]

  df['hpr'] = df['ror'].cumprod()
  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100

  print("MDD(%): ", df['dd'].max())
  #print("누적수익률(fee고려):", ror, sep=' ')
  
  #print(df.tail(10))
  #print(df.head(10))

  return ror


# for k in np.arange(0.1, 1.0, 0.1):
#   ror = get_ror(k, ticker_ETC)
#   print("누적수익률(fee고려) ==> k:{:.1}: {}".format(k,ror))

#   r_list.append(ror)

upbit = pyupbit.Upbit(access_key, secret_key)
balances = upbit.get_balances()
print(balances)

tickers = [ticker_BTC, ticker_ETC, ticker_QTUM, ticker_EOS]
t_list = []
for ticker in tickers:
  print('코인 이름:{}'.format(ticker))
  r_list = []
  for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k, ticker)
    print("누적수익률(fee고려) ==> k:{:.1}: {}".format(k,ror))

    r_list.append(ror)
  t_list.append(r_list)