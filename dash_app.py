import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
from os import listdir, remove
import pickle
from time import sleep
import plotly.express as px
import math

from helper_functions import *
# this statement imports all functions from your helper_functions file!

# Run your helper function to clear out any io files left over from old runs
# 1:
check_for_and_del_io_files()

# Make a Dash app!
app = dash.Dash(__name__)

# Define the layout.
app.layout = html.Div([
    html.H1("Section 1: Fetch & Display historical data"),
    html.Div(
        [
        "Input Stock:",
        dcc.Input(id='currency-pair', type='text', value = 'AAPL'),
        ],
        style={'display': 'inline-block'}
    ),
    html.Button('Submit', id = 'submit-button', n_clicks = 0),
    html.Br(),
    html.Div(id='output-div0', children='Enter a currency code and press submit'),
    html.Div([
        dcc.Graph(id='candlestick-graph')
    ]),


    html.Br(),
    html.H1("Section 2: set parameter and backtest"),
    html.Div(
        [
        "Input Stock:",
        dcc.Input(id='stock2', type='text', value = 'AAPL')
        ],
        style={'display': 'inline-block'}
    ),
    html.Div(
        [
        "Input window:",
        dcc.Input(id='window2', type='number', value = 30)
        ],
        style={'display': 'inline-block'}
    ),
    html.Div(
        [
        "Input alpha:",
        dcc.Input(id='alpha2', type='number', value = 1)
        ],
        style={'display': 'inline-block'}
    ),

    html.Button('Submit', id = 'submitbutton2', n_clicks = 0),
    html.Br(),
    html.Div(id='output2'),
    html.Div(id='output21'),
    html.Div(id='outputopen'),
    html.Div(id='outputhigh'),
    html.Div(id='outputlow'),

    html.Div([
        dcc.Graph(id='graph2')
    ]),

    html.Br(),
    html.H1("Section 3: trade"),
    html.Div(id='output-div'),
    html.Div(
        [
            "Input window:",
            dcc.Input(id='window3', type='number', value=30),
            "Input alpha:",
            dcc.Input(id='alpha3', type='number', value=2),
            "Input stock:",
            dcc.Input(id='stock3', type='text', value='AAPL'),
            "Input amount",
            dcc.Input(id='trade-amount', type='number', value=100),
        ],
        style={'display': 'inline-block'}
    ),

    html.Button('Trade', id='trade-button', n_clicks=0),
    html.Br(),
    # html.Div(id='output-div3', children='Use'),
])


# Callback for what to do when submit-button is pressed
@app.callback(
    [ # there's more than one output here, so you have to use square brackets to pass it in as an array.
    Output('output-div0', 'children'),
    Output('candlestick-graph','figure')
    ],
    [Input('submit-button', 'n_clicks')],
    [State('currency-pair', 'value')]
)
def update_candlestick_graph(n_clicks, value): # n_clicks doesn't get used, we only include it for the dependency.
    # Now we're going to save the value of currency-input as a text file.
    print(value, n_clicks)
    with open('currency_pair.txt','w') as f:
        f.write(value)

    # Wait until ibkr_app runs the query and saves the historical prices csv
    while 'currency_pair_history.csv' not in listdir():
        sleep(1)
    sleep(3)

    # Read in the historical prices
    df = pd.read_csv('currency_pair_history.csv')
    # Remove the file 'currency_pair_history.csv'
    remove('currency_pair_history.csv')

    # Make the candlestick figure
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close']
            )
        ]
    )
    # Give the candlestick figure a title
    fig.update_layout(title=value)

    # Return your updated text to currency-output, and the figure to candlestick-graph outputs
    return ('Submitted query for ' + value), fig


@app.callback(
    [
    Output('output2', 'children'),
    Output('output21', 'children'),
    Output('outputopen', 'children'),
    Output('outputhigh', 'children'),
    Output('outputlow', 'children'),
    Output('graph2','figure')
    ],
    Input('submitbutton2', 'n_clicks'),
    State('stock2', 'value'),
    State('window2', 'value'),
    State('alpha2', 'value'),
    prevent_initial_call=True
)
def backtest(n_clicks, s2,w2,a2):
    print(n_clicks,s2,w2,a2)
    temp = np.array([s2,w2,a2])
    np.save('backtest.npy', temp)

    while 'backtestresult.npy' not in listdir():
        sleep(1)
    sleep(3)
    temp = np.load('backtestresult.npy',allow_pickle=True)
    a = temp[1]
    return1 = round(a[-1]/a[0] - 1,3)
    sharp = round((return1 - 0.02)/np.std(a),3)
    remove('backtestresult.npy')

    while 'price.npy' not in listdir():
        sleep(1)
    sleep(3)
    ttemp = np.load('price.npy', allow_pickle=True)
    price_open = ttemp[0]
    price_h = round(ttemp[1],3)
    price_l = round(ttemp[2],3)
    remove('price.npy')

    didi = {'date': temp[0], 'capital': temp[1]}
    fig = px.line(didi, 'date', 'capital')
    fig.update_layout(title='backtest')
    return ('return is ' + str(return1)),('sharp ratio is ', str(sharp)),('today open price is ' + str(price_open)),('BB high: ' + str(price_h)),('BB low: ' + str(price_l)),fig


# Callback for what to do when trade-button is pressed
@app.callback(
    Output('output-div', 'children'),
    Input('trade-button', 'n_clicks'),
    State('window3', 'value'),
    State('alpha3', 'value'),
    State('stock3', 'value'),
    State('trade-amount', 'value'),
    prevent_initial_call=True
)

def trade(n_clicks, window, alpha, trade_stock, trade_amt):
    # Make the message that we want to send back to trade-output
    msg = 'use '+str(trade_amt) + 'dollar to trade on '+str(trade_stock)
    # Make our trade_order object -- a DICTIONARY.

    trade_order = dict()
    trade_order['trade_money'] = trade_amt
    trade_order['trade_stock'] = trade_stock

    temp = np.array([trade_stock, window, alpha])
    np.save('getbands.npy', temp)
    # Dump trade_order as a pickle object to a file connection opened with write-in-binary ("wb") permission:
    f1 = open('trade_order.p','wb')
    pickle.dump(trade_order, f1)
    f1.close()

    # Return the message, which goes to the trade-output div's "children" attribute.
    return msg


# Run it!
if __name__ == '__main__':
    app.run_server(debug=True)
