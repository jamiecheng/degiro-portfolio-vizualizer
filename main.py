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
    th = account.get_transactions(datetime.datetime(1980, 1, 1), datetime.datetime.now())

    first_transaction_date = th.iloc[[0]].index.item()
    product_ids = th['id'].unique().tolist()

    print('retrieving stock data...')
    df = account.get_product_history(product_ids, first_transaction_date, datetime.datetime.now())

    # construct matrix that holds the quantity of each ticker on each day
    ticker_holdings = np.zeros((len(df.index), len(product_ids)), dtype=int)

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
                    ticker_holdings[i][product_ids.index(row['id'])] = \
                        ticker_holdings[i][product_ids.index(row['id'])] + row['quantity']
            else:
                ticker_holdings[i][product_ids.index(transactions['id'])] = \
                    ticker_holdings[i][product_ids.index(transactions['id'])] + transactions['quantity']

    print('calculating portfolio...')

    df_close = df.to_numpy()

    # vector of portfolio value on each day
    portfolio_history = np.zeros(len(df.index))

    for i in range(0, np.shape(ticker_holdings)[1]):
        portfolio_history = portfolio_history + (df_close[:, i] * ticker_holdings[:, i])

    plt.plot(df.index, portfolio_history.transpose())

    cr = (portfolio_history[len(portfolio_history) - 1] / portfolio_history[0]) * 100

    print('Cumulative return : {0}%'.format(cr))

    plt.show()

    account.logout()
