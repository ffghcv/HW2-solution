import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
from os import listdir, remove
import pickle
from time import sleep
import plotly.express as px
import math
from datetime import date, timedelta

from helper_functions import *
# this statement imports all functions from your helper_functions file!

# Run your helper function to clear out any io files left over from old runs
# 1:
check_for_and_del_io_files()

# Make a Dash app!
app = dash.Dash(__name__)

# Define the layout.
app.layout = html.Div([
    html.H1(
        'Bollinger Bands Trading Strategy',
        style={'display': 'block', 'text-align': 'center'}
    ),
    html.H1('Section 1: Strategy'),
    html.H2('Description'),
    html.Div([
        html.P('This app explores the Bollinger Bands (BB) strategy that works as follows:'),
        html.P('Backtest:'),
        html.Ol([
            html.Li([
                "While the market is not open, retrieve the past N days' worth of market data " + \
                "for the particular stock:",
                html.Ul([
                    html.Li("daily open, high, low, & close prices, volume, average price, barCount"),
                ])
            ]),
            html.Li([
                'Given the parameters: time window [m] days, multiples of standard deviation [alpha],' + \
                'calculate the upper and lower bands through the open prices record in' + \
                'a dataframe:',
                html.Ul([
                    html.Li('Upper band: average price for m days + alpha * standard deviation for m days'),
                    html.Li('Lower band: average price for m days - alpha * standard deviation for m days'),
                ]),
            ]),
            html.Li(
                'Repeat 2. calculating the moving average and std.dev of historical open prices ' + \
                'to create a FEATURES dataframe containing historical value of upper and lower bands ' + \
                'during the specified time period.'
            ),
            html.Li([
                "Compare today's stock open price to the upper and lower bands based on the last m days' " + \
                "historical prices: ",
                html.Ul([
                    html.Li('Submit a market order to BUY if the open price is less than the value of ' + \
                            'lower band which is considered oversold'),
                    html.Li('Submit a market order to SELL if the open price is greater than the value of ' + \
                            'upper band which is considered overbought'),
                ]),
            ]),
        ]),
        html.P('Live trading:'),
        html.Ol([
            html.Li([
                "Repeat 1.& 2., and compare today's stock open price to the upper and lower bands based " + \
                "on the last m days' historical prices: ",
                html.Ul([
                    html.Li('Submit a market order to BUY if the open price is less than the value of ' + \
                            'lower band which is considered oversold"'),
                    html.Li('Submit a market order to SELL if the open price is greater than the value of ' + \
                            'upper band which is considered overbought"'),
                    html.Li(
                        'Otherwise, Submit two limit orders to BUY at lower band price and SELL at upper band price' + \
                        'which will be canceled if unfilled in the next trade'),
                ]),
            ]),
        ]),
        html.P('Typical values used:'),
        html.Ul([
            html.Li('short term: 10 day moving average, bands at 1.5 standard deviations. ' + \
                    '(The SMA +/- 1.5 times the standard dev. )'),
            html.Li('Medium term: 20 day moving average, bands at 2 standard deviations. '),
            html.Li('Long term: 50 day moving average, bands at 2.5 standard deviations.'),
        ]),
    ]),
    html.Div([
        html.H2('Data Note & Disclaimer'),
        html.P(
            'This Dash app makes use of TWS to request the latest historical data and write into the ' + \
            '.csv files in the directory \'stock_history.csv\'. These initial data ' + \
            'can be also downloaded from Google Finance and other publicly available information on ' + \
            'the Internet. Always know and obey your data stewardship obligations!'
        ),
        html.H2('Parameters'),
        html.Ol([
            html.Li(
                "Time window m: number of days employed in moving averages for averaging interval. "
            ),
            html.Li(
                'Alpha: multiples of standard deviation ' + \
                '(e.g., The SMA +/- alpha times the standard dev.) which determines ' + \
                'the distance of the band.'
            ),
            html.Li(
                'Ratio (percent): the ratio of capital for each trade order. '
            ),
            html.Li(
                'date_range: Date range over which to perform the backtest.'
            )
        ]),
    ]),

    html.H1("Section 2: Fetch & Display historical data"),
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
    html.H1("Section 3: Set parameter and backtest"),
    html.Td(
        dcc.DatePickerRange(
            id='timerange2',
            min_date_allowed=date(2018, 1, 1),
            max_date_allowed=date.today(),
            initial_visible_month=date.today(),
            start_date=date(2020, 4, 14),
            end_date=date(2021, 4, 14)
        )
    ),
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
    html.Div(
        [
        "Input ratio(percent):",
        dcc.Input(id='ratio2', type='number', value = 25)
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

    html.Div(
            dash_table.DataTable(
                id='calendar_ledger',
                fixed_rows={'headers': True},
                style_cell={'textAlign': 'center'},
                style_table={'height': '300px', 'overflowY': 'auto'}
            ),
            style={'display': 'inline-block', 'width': '45%'}
    ),
    html.Div(
        dash_table.DataTable(
            id='blotter',
            fixed_rows={'headers': True},
            style_cell={'textAlign': 'center'},
            style_table={'height': '300px', 'overflowY': 'auto'}
        ),
        style={'display': 'inline-block', 'width': '45%'}
    ),

    html.Br(),
    html.H1("Section 4: Live trade"),
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
    html.Br(),
    html.Br(),
    # html.Div(id='output-div3', children='Use'),
])


# Callback for what to do when submit-button is pressed
@app.callback(
    [ # there's more than one output here, so you have to use square brackets to pass it in as an array.
    Output('output-div0', 'children'),
    Output('candlestick-graph', 'figure')
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
    Output('graph2', 'figure'),
    Output('calendar_ledger', 'data'),
    Output('calendar_ledger', 'columns'),
    Output('blotter', 'data'),
    Output('blotter', 'columns'),
    #Output('feature', 'data'),
    #Output('feature', 'columns')
    ],
    Input('submitbutton2', 'n_clicks'),
    State('timerange2', 'start_date'),
    State('timerange2', 'end_date'),
    State('stock2', 'value'),
    State('window2', 'value'),
    State('alpha2', 'value'),
    State('ratio2', 'value'),
    prevent_initial_call=True
)
def backtest(n_clicks, sd2, ed2, s2, w2, a2, r2):
    print(n_clicks, sd2, ed2, s2, w2, a2, r2)
    temp = np.array([sd2, ed2, s2, w2, a2, r2])
    np.save('backtest.npy', temp)

    while 'backtestresult.npy' not in listdir():
        sleep(1)
    sleep(3)
    temp = np.load('backtestresult.npy', allow_pickle=True)
    a = temp[1]
    return1 = round(a[-1]/a[0] - 1,3)
    sharp = round((return1 - 0.02)/np.std(a),3)
    remove('backtestresult.npy')

    while 'calendar_ledger.csv' not in listdir():
        sleep(1)
    sleep(3)
    calendar_ledger = pd.read_csv('calendar_ledger.csv')
    calendar_ledger_columns = [{"name": i, "id": i} for i in calendar_ledger.columns]
    calendar_ledger = calendar_ledger.to_dict('records')

    while 'blotter.csv' not in listdir():
        sleep(1)
    sleep(3)
    blotter = pd.read_csv('blotter.csv')
    blotter_columns = [{"name": i, "id": i} for i in blotter.columns]
    blotter = blotter.to_dict('records')

    '''
    while 'feature.csv' not in listdir():
        sleep(1)
    sleep(3)
    feature = pd.read_csv('feature.csv')
    feature_columns = [{"name": i, "id": i} for i in feature.columns]
    feature = feature.to_dict('records')
    '''
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

    return ('return is ' + str(return1)), ('sharp ratio is ', str(sharp)),\
           ('today open price is ' + str(price_open)), ('BB high: ' + str(price_h)), ('BB low: ' + str(price_l)),\
           fig, calendar_ledger, calendar_ledger_columns, blotter, blotter_columns


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
