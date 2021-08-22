from pandas_datareader import data
from pandas_datareader.yahoo.headers import DEFAULT_HEADERS
import matplotlib.pyplot as plt
import pandas as pd
import requests_cache
import local_config
from broker import Broker
import datetime
import numpy as np

if __name__ == '__main__':
    account = Broker()
    #
    print(account.login(local_config.username, local_config.password))

    print('retrieving transaction history...')
    th = account.get_transactions(datetime.datetime(2020, 1, 1), datetime.datetime.now())

    first_transaction_date = th.iloc[[0]].index.item()
    tickers = th['ticker'].unique().tolist()

    print('retrieving stock data...')
    session = requests_cache.CachedSession(cache_name='cache', backend='sqlite',
                                           expire_after=datetime.timedelta(days=3))

    session.headers = DEFAULT_HEADERS

    # User pandas_reader.data.DataReader to load the desired data. As simple as that.
    df = data.DataReader(tickers, 'yahoo', first_transaction_date, datetime.datetime.now(), session=session)

    # construct matrix that holds the quantity of each ticker on each day
    ticker_holdings = np.zeros((len(df.index), len(tickers)), dtype=int)

    # iterate through each day since the first transaction
    for i in range(0, len(df.index)):
        # we start the day with the same holdings as the day before
        if i != 0:
            ticker_holdings[i] = ticker_holdings[i - 1]

        # is there a transaction at this date?
        if df.index[i].strftime('%Y-%m-%d') in th.index:
            # get all transactions on this day
            transactions = th.loc[str(df.index[i].strftime('%Y-%m-%d'))]

            if isinstance(transactions, pd.DataFrame):
                for index, row in transactions.iterrows():
                    ticker_holdings[i][tickers.index(row['ticker'])] = \
                        ticker_holdings[i][tickers.index(row['ticker'])] + row['quantity']
            else:
                ticker_holdings[i][tickers.index(transactions['ticker'])] = \
                    ticker_holdings[i][tickers.index(transactions['ticker'])] + transactions['quantity']

    print('calculating portfolio...')

    df_close = df['Adj Close'].to_numpy()

    # vector of portfolio value on each day
    portfolio_history = np.zeros((len(tickers), 1))

    for i in range(0, np.shape(ticker_holdings)[1]):
        portfolio_history = portfolio_history + (df_close[:, i] * ticker_holdings[:, i])

    plt.plot(df.index, portfolio_history.transpose())

    plt.show()

    account.logout()
