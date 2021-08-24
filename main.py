import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import local_config
from broker import Broker


class Portfolio:
    def __init__(self):
        self.account = Broker()

        self.portfolio_symbols = []
        self.portfolio_quantities = []
        self.portfolio_value = []
        self.portfolio_value_total = []
        self.portfolio_days = []

        self.total_cost = 0

    def login(self, username, password):
        self.account.login(username, password)

        return self

    def logout(self):
        self.logout()

    def update(self):
        print('Updating portfolio...')
        th = self.account.get_transaction_history()

        self.total_cost = th['cost'].to_numpy().sum()

        first_transaction_date = th.iloc[[0]].index.item()
        self.portfolio_symbols = th['id'].unique().tolist()

        df = self.account.get_product_history(self.portfolio_symbols, first_transaction_date, datetime.datetime.now())

        self.portfolio_days = df.index

        # construct matrix that holds the quantity of each ticker on each day
        self.portfolio_quantities = np.zeros((len(df.index), len(self.portfolio_symbols)), dtype=int)

        # iterate through each day since the first transaction
        for i in range(0, len(df.index)):
            # we start the day with the same holdings as the day before
            if i != 0:
                self.portfolio_quantities[i] = self.portfolio_quantities[i - 1]

            # is there a transaction at this date?
            if df.index[i].strftime('%Y-%m-%d') in th.index:
                # get all transactions on this day
                transactions = th.loc[str(df.index[i].strftime('%Y-%m-%d'))]

                if isinstance(transactions, pd.DataFrame):
                    for index, row in transactions.iterrows():
                        self.portfolio_quantities[i][self.portfolio_symbols.index(row['id'])] = \
                            self.portfolio_quantities[i][self.portfolio_symbols.index(row['id'])] + row['quantity']
                else:
                    self.portfolio_quantities[i][self.portfolio_symbols.index(transactions['id'])] = \
                        self.portfolio_quantities[i][self.portfolio_symbols.index(transactions['id'])] + transactions[
                            'quantity']

        df_close = df.to_numpy()

        self.portfolio_value = np.multiply(df_close, self.portfolio_quantities)
        self.portfolio_value_total = self.portfolio_value.sum(axis=1)

    def get_sharpe(self):
        diff = self.portfolio_value_total[1:] - self.portfolio_value_total[:-1]
        daily_returns = diff / self.portfolio_value_total[1:] * 100

        return (252 ** 0.5) * (np.nanmean(daily_returns) / np.nanstd(daily_returns))

    def get_profit_loss(self):
        return ((self.portfolio_value_total[
                     len(self.portfolio_value_total) - 2] + self.total_cost) / -self.total_cost) * 100


if __name__ == '__main__':
    p = Portfolio().login(local_config.username, local_config.password)

    p.update()

    plt.plot(p.portfolio_days, p.portfolio_value_total)

    plt.show()

    print('Sharpe ratio : {:.2f}'.format(p.get_sharpe()))
    print('Portfolio gain : {:.2f}%'.format(p.get_profit_loss()))
