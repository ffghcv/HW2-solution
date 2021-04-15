from ib_insync import *
from os import listdir, remove
from time import sleep
import pickle
from datetime import date, time, datetime, timedelta
import math
from ta.momentum import *
from ta.volatility import BollingerBands
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import pandas as pd

# 演示时不要用家里的WiFi，一定要用手机热点，不然从TWS更新数据很慢

# Define your variables here ###########################################################################################
sampling_rate = 1 # How often, in seconds, to check for inputs from Dash?
# For TWS Paper account, default port is 7497
# For IBG Paper account, default port is 4002
port = 7497
# choose your master id. Mine is 10645. You can use whatever you want, just set it in API Settings within TWS or IBG.
master_client_id = 8923
# choose your dedicated id just for orders. I picked 1111.id
orders_client_id = 1111
# account number: you'll need to fill in yourself. The below is one of my paper trader account numbers.
acc_number = 'DU3524612'

########################################################################################################################

# Run your helper function to clear out any io files left over from old runs
from helper_functions import *
check_for_and_del_io_files()

# Create an IB app; i.e., an instance of the IB() class from the ib_insync package
ib = IB()

# Connect your app to a running instance of IBG or TWS
ib.connect(host='127.0.0.1', port=port, clientId=master_client_id)

# Make sure you're connected -- stay in this while loop until ib.isConnected() is True.
while not ib.isConnected():
    sleep(.01)

# If connected, script proceeds and prints a success message.
print('Connection Successful!')
def get_data(contract, history, freq, side, endDate=''):
    bar = ib.reqHistoricalData(
        contract,
        endDateTime=endDate,
        durationStr=history,
        barSizeSetting=freq,
        whatToShow=side,
        useRTH=True,
        formatDate=1)
    df = util.df(bar)
    return df

def take_strategy(ticker1, parameter_window, parameter_alpha):
    """
    获得策略的函数
    :param ticker1:股票代码
    :param parameter_window:
    :param parameter_alpha:
    :return: BB策略表格
    """
    history = '4 Y'
    freq = '1 day'
    side = 'Trades'  # last trade, or ASK, or Bid
    endDate = ''

    contract1 = Contract(symbol=ticker1, secType='STK', exchange='SMART', currency='USD')
    ib.qualifyContracts(contract1)
    df1 = get_data(contract1, history, freq, side, endDate)

    df1['bb_h'] = BollingerBands(df1.open, window=parameter_window, window_dev=parameter_alpha).bollinger_hband()
    df1['bb_l'] = BollingerBands(df1.open, window=parameter_window, window_dev=parameter_alpha).bollinger_lband()
    df1['bb_m'] = BollingerBands(df1.open, window=parameter_window, window_dev=parameter_alpha).bollinger_mavg()
    return df1

def backtest(df1, start_time, end_time, r2):
    """
    现在的back test的函数，
    输入：df1, start_time, end_time, r2；其中df1是策略价格，start_time, end_time是回测时间；r2是资金控制比例（百分数）；
    输出：
        captial plot资金图矩阵，一个numpy矩阵，第一行是时间，第二行是每日资金量;
        calendar ledgar:【完成】
        trade blotter:【需要增加的部分】

    在backtest中， 首字母小写为每日变量， 首字母大写为储存变量。
    """
    #startDate = date(date.today().year - 1, date.today().month, date.today().day)
    #endDate = date.today()
    #ratio = 0.4

    startDate = start_time
    endDate = end_time
    ratio = int(r2)/100

    df = df1[(df1.date >= startDate) & ((df1.date <= endDate))]
    df.index = range(df.count()[0])
    print('合计回测天数：', len(df))

    Total_Length = len(df)

    sum_IVVopen = df['open']
    sum_IVVclose = df['close']
    sum_Cash = np.zeros(Total_Length)
    sum_Pos = np.zeros(Total_Length) #股票数，position
    sum_StockValue = np.zeros(Total_Length)
    # total value = cash + stock value

    pos = 0 #股票数，position
    cash = 100000 #现金金额
    share = 0 #股票对应的金额
    capital = cash + share
    res = []

    id = 0
    action = []
    ID = []
    created = []
    price = []
    size = []
    type = []
    statue = []
    POS = []

    i = 0
    for index, row in df.iterrows():
        if row['open'] <= row['bb_l']:
            if cash >= capital * ratio:
                amount = capital * ratio / row['open']
                size.append(amount)
                pos += amount
                cash -= capital * ratio
                id += 1
                action.append('BUY')
                created.append(row['date'])
                ID.append(id)
                price.append(row['open'])
                type.append('MKT')
                statue.append('Filled')
                if pos > 0:
                    POS.append('L')
                else:
                    POS.append('S')
            elif cash == 0:
                pass
            else:
                amount = cash / row['open']
                size.append(amount)
                pos += amount
                cash = 0
                id += 1
                action.append('BUY')
                created.append(row['date'])
                ID.append(id)
                price.append(row['open'])
                type.append('MKT')
                statue.append('Filled')
                if pos > 0:
                    POS.append('L')
                else:
                    POS.append('S')
        elif row['open'] >= row['bb_h']:
            if share >= capital * ratio:
                amount = capital * ratio / row['open']
                size.append(amount)
                pos -= amount
                cash += capital * ratio
                id += 1
                action.append('SELL')
                created.append(row['date'])
                ID.append(id)
                price.append(row['open'])
                type.append('MKT')
                statue.append('Filled')
                if pos > 0:
                    POS.append('L')
                else:
                    POS.append('S')
            elif share == 0:
                pass
            else:
                pos = 0
                cash += share
                amount = share / row['open']
                id += 1
                size.append(amount)
                action.append('SELL')
                created.append(row['date'])
                ID.append(id)
                price.append(row['open'])
                type.append('MKT')
                statue.append('Filled')
                if pos > 0:
                    POS.append('L')
                else:
                    POS.append('S')


        share = pos * row['open']
        capital = cash + share
        res.append(capital)

        sum_Cash[i] = cash
        sum_Pos[i] = pos
        sum_StockValue[i] = share
        i += 1

    sum_Total_Value = sum_Cash + sum_StockValue
    captial_plot = np.array([df.date, res])

    calendar_ledger = np.array([df.date, sum_IVVopen, sum_IVVclose, sum_Cash, sum_Pos, sum_StockValue, sum_Total_Value]).T
    calendar_ledger = pd.DataFrame(calendar_ledger)
    calendar_ledger.columns = ['date', 'IVVopen', 'IVVclose', 'Cash', 'Position', 'StockValue', 'Total_Value']

    ID = np.array(ID)
    POS = np.array(POS)
    created = np.array(created)
    action = np.array(action)
    size = np.array(size)
    price = np.array(price)
    type = np.array(type)
    statue = np.array(statue)

    blotter = np.array([ID, POS, created, action, size, price, type, statue]).T
    blotter
    blotter = pd.DataFrame(blotter)
    blotter.columns = ['ID', 'Position', 'Created', 'Action', 'Size', 'Order price', 'Type', 'Statue']

    return captial_plot, calendar_ledger, blotter


def convert_str_to_datetime(sd2):
    """
    将dash中获得的时间转为datetime
    """
    a1 = sd2[0:4]
    a2 = sd2[5:7]
    a3 = sd2[8:10]
    return(date(int(a1),int(a2), int(a3)))

# Main while loop of the app. Stay in this loop until the app is stopped by the user.
while True:
    # If the app finds a file named 'currency_pair.txt' in the current directory, enter this code block.
    if 'currency_pair.txt' in listdir():
        # Code goes here...
        with open('currency_pair.txt', 'r') as f:
            curr = f.read()
        remove('currency_pair.txt')
        # Note that here, if you wanted to make inputs for endDateTime, durationStr, barSizeSetting, etc within the Dash
        #   app, then you could save a dictionary as a pickle and import it here like we do below for the order.
        contract1 = Contract(symbol=curr, secType='STK', exchange='SMART', currency='USD')
        ib.qualifyContracts(contract1)

        history = '3 Y'
        freq = '1 day'
        side = 'Trades'
        endDate = ''

        df1 = get_data(contract1, history, freq, side, endDate)

        df1.to_csv('currency_pair_history.csv')

        # pass -- not return -- because this function doesn't return a value. It's called for what it does. In computer
        #   science, we say that it's called for its 'side effects'.
        pass

    if 'backtest.npy' in listdir():
        temp = np.load('backtest.npy')
        remove('backtest.npy')
        sd2, ed2, s2, w2, a2, r2 = temp
        print(temp)
        a = take_strategy(s2, int(w2), int(a2))
        start_time = convert_str_to_datetime(sd2)
        end_time = convert_str_to_datetime(ed2)

        captial_plot, calendar_ledger, blotter = backtest(a, start_time, end_time, r2)

        np.save('backtestresult.npy', captial_plot)

        calendar_ledger.to_csv('calendar_ledger.csv', sep=',')

        blotter.to_csv('blotter.csv', sep=',')

        b = np.array(a)
        price_open = b[-1,1]
        price_h = b[-1,-3]
        price_l = b[-1,-2]
        temp = np.array([price_open, price_h, price_l])
        np.save('price.npy', temp)
        pass

    # If there's a file named trade_order.p in listdir(), then enter the loop below.
    if 'trade_order.p' in listdir():
        # Check everyday, and cancel the limit orders unfilled yesterday
        ib.reqGlobalCancel()

        f1 = open('trade_order.p', 'rb')
        trd_order = pickle.load(f1)
        f1.close()

        temp = np.load('getbands.npy')
        remove('getbands.npy')
        s3, w3, a3 = temp

        a = take_strategy(s3, int(w3), int(a3))
        b = np.array(a)
        price_open = b[-1, 1]
        price_h = round(b[-1, -3],2)
        price_l = round(b[-1, -2],2)

        contract = Contract(symbol=trd_order['trade_stock'], secType='STK', exchange='SMART', currency='USD')

        if price_open <= price_l:
            order = MarketOrder('BUY', trd_order['trade_money'])
            order.account = acc_number
            ib_orders = IB()
            ib_orders.connect(host='127.0.0.1', port=port, clientId=orders_client_id)
            new_order = ib_orders.placeOrder(contract, order)
            while not new_order.orderStatus.status == 'Filled':
                ib_orders.sleep(0)
            print('buy')

        elif price_open >= price_h:
            order = MarketOrder('SELL', trd_order['trade_money'])
            order.account = acc_number
            ib_orders = IB()
            ib_orders.connect(host='127.0.0.1', port=port, clientId=orders_client_id)
            new_order = ib_orders.placeOrder(contract, order)
            while not new_order.orderStatus.status == 'Filled':
                ib_orders.sleep(0)
            print('sell')

        else:
            order1 = LimitOrder('BUY', trd_order['trade_money'], price_l)
            order1.account = acc_number
            order2 = LimitOrder('SELL', trd_order['trade_money'], price_h)
            order2.account = acc_number
            ib_orders = IB()
            ib_orders.connect(host='127.0.0.1', port=port, clientId=orders_client_id)
            new_order1 = ib_orders.placeOrder(contract, order1)
            ib_orders.sleep(1)
            new_order2 = ib_orders.placeOrder(contract, order2)
            ib_orders.sleep(1)
            print('Place two limit orders')

        # your code goes here
        remove('trade_order.p')
        #print(new_order)
        ib_orders.disconnect()

        # pass: same reason as above.
        pass

    # sleep, for the while loop.
    ib.sleep(sampling_rate)
