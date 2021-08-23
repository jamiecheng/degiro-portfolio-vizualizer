import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import local_config
from broker import Broker

if __name__ == '__main__':
    account = Broker()
    #
    print(account.login(local_config.username, local_config.password))

    print('retrieving transaction history...')
    th = account.get_transactions(datetime.datetime(1980, 1, 1), datetime.datetime.now())

    total_cost = th['cost'].to_numpy().sum()

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

    gain = ((portfolio_history[len(portfolio_history) - 1] + total_cost) / -total_cost) * 100

    print('Portfolio gain : {:.2f}%'.format(gain))

    diff = portfolio_history[1:] - portfolio_history[:-1]
    daily_returns = diff / portfolio_history[1:] * 100

    sharpe = (252**0.5) * (daily_returns.mean() / daily_returns.std())

    print('Sharpe ratio : {:.2f}'.format(sharpe))

    plt.show()

    account.logout()
