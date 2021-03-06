# -*- coding: utf-8 -*-

import time
import pyupbit
import numpy as np
import datetime
import configparser
import logging
from pytz import timezone

config = configparser.ConfigParser()
config.read(r"config/config.ini")

access_key = config['DEFAULT']['ACCESS_KEY'] 
secret_key = config['DEFAULT']['SECRET_KEY'] 

KST = timezone('Asia/Seoul')

# 타겟 금액 계산
def get_target_price(ticker, k):
    #print('Reset target price')
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=9) 
    
    latest_time = df.index[-1]
    if latest_time.minute != 30:
        df = df.iloc[:-1]

    last = df.iloc[-8] # 12시간 전
    now = df.iloc[-1]

    #print(df)

    now_open = now['open'] # 현재기준 가장 최근시간
    last_high = last['high'] # 4시간 전 최저가
    last_low = last['low'] # 4시간 전 최저가
    target = now_open + (last_high - last_low) * k
    return target

# 시작 시간 계산
def get_start_time(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=2)
    if df.index[-1].minute != 30:
      df = df.iloc[:-1] # 시간 정각은 제외한다
    start_time = df.index[-1]
    logger.info('start_time={}'.format(start_time))
    #print(start_time)
    return start_time

# 1440분(30분*40회) 이동평균선 계산
def get_ma15(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=48)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

# 내 잔고조회 (Coin 갯수)
def get_balance(ticker):
    balances = upbit.get_balances()
    #print(balances)
    for b in balances:
        if b['currency'] == ticker[ticker.index('-')+1:]:
            if b['balance'] is not None:
                return float(b['balance']), float(b['avg_buy_price'])
            else:
                return 0
    return 0

# # 주문의 uuid 조회
# def get_order_uuid(ticker):
#     orders = upbit.get_order(ticker)
#     uuid = orders['uuid']
#     return uuid

# 현재 구매 가능한 가격 조회
def get_current_price(ticker):
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

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

    #print("MDD(%): ", df['dd'].max())
    #print("누적수익률(fee고려):", ror, sep=' ')
    
    #print(df.tail(10))
    #print(df.head(10))

    return ror

def find_k(ticker):
    r_list = []
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(k, ticker)
        r_list.append(ror)
    #print(r_list)
    k = (int(r_list.index(max(r_list)))+1)/10
    logger.info('k_value={}'.format(k))
    return k


logger = logging.getLogger()

logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# log를 파일에 출력
file_handler = logging.FileHandler('my.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

upbit = pyupbit.Upbit(access_key, secret_key)
logger.info("autotrade start")

ticker_BTC = "KRW-BTC" #비트코인
ticker_ETC = "KRW-ETC" #이더리움 클래식
ticker_QTUM = "KRW-QTUM" #퀀텀
ticker_EOS = "KRW-EOS" #이오스
ticker_KRW = "KRW-KRW" #원화

# 자동매매 시작

today_ticker = ticker_ETC
k_value = find_k(ticker=today_ticker)
start_time = get_start_time(ticker=today_ticker) # 지금시간 기준 30분 전이어야 함.

while True:
    try:
        now = datetime.datetime.now(KST) #지금시간... 16시 1분
        end_time = start_time + datetime.timedelta(hours=4)
        start_time, end_time = start_time.replace(tzinfo=KST), end_time.replace(tzinfo=KST)
        logger.info(start_time, end_time)
        # 4시간
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(ticker=today_ticker, k=k_value)
            ma15 = get_ma15(ticker=today_ticker)
            current_price = get_current_price(ticker=today_ticker)
            logger.info('구매 목표가:{}//이동 평균선:{:.1f}//현재 금액:{}'.format(target_price, ma15, current_price))
            if target_price < current_price and ma15 < current_price:
                logger.info('Meet the condition - buy')
                #logger.info('구매 목표가:{}//이동 평균선(60시간):{:.1f}//현재 금액:{}'.format(target_price, ma15, current_price))
                krw = get_balance(ticker_KRW)
                if krw > 5000:
                    try: 
                        upbit.buy_market_order(today_ticker, krw*0.9995) # 수수료 0.9995
                        logger.info('EVENT:구매 완료')
                    except Exception as e:
                        logger.info(e)
        else:
            coin_volume, avg_buy_price = get_balance(today_ticker)
            current_price = get_current_price(ticker=today_ticker)
            if coin_volume > 0.00008 and avg_buy_price < current_price:
                try: 
                    upbit.sell_market_order(today_ticker, coin_volume*0.9995)
                    logger.info('EVENT:판매 완료, 코인 갯수:',coin_volume)
                except Exception as e:
                    logger.info(e)
            k_value = find_k(ticker=today_ticker)
            start_time = get_start_time(ticker=today_ticker) # 지금시간 기준 30분 전이어야 함.

        time.sleep(3)
    except Exception as e:
        logger.info(e)
        time.sleep(3)