import degiroapi
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class Broker:
    def __init__(self):
        self.degiro = degiroapi.DeGiro()

    def login(self, username, password):
        self.degiro.login(username, password)

        return self

    def get_transaction_history(self):
        transactions = self.degiro.transactions(datetime(1980, 1, 1), datetime.now())
        transaction_list = []

        for transaction in transactions:
            info = self.degiro.product_info(transaction['productId'])
            date = datetime.strptime(transaction['date'], '%Y-%m-%dT%H:%M:%S%z')

            tsn = {
                'date': date.strftime('%Y-%m-%d'),
                'id': transaction['productId'],
                'name': info['name'],
                'ticker': info['symbol'],
                'quantity': transaction['quantity'],
                'cost': transaction['totalInBaseCurrency'],
                'fee': transaction['feeInBaseCurrency']
            }

            transaction_list.append(tsn)

        df = pd.DataFrame(transaction_list).set_index('date')

        return df

    def get_product_history(self, product_ids, start_date, end_date):
        dfs = []

        for product_id in product_ids:
            res = self.degiro.real_time_price(product_id, degiroapi.Interval.Type.Max)

            # reformat degiro's retarded data format
            start = datetime.strptime(res[1]['times'][0:len(res[1]['times']) - 4], '%Y-%m-%d')

            stock_data = []
            for price in res[1]['data']:
                data = {
                    'date': start + timedelta(days=price[0]),
                    res[0]['data']['alfa']: price[1]
                }

                stock_data.append(data)

            df = pd.DataFrame(stock_data).set_index('date')

            dfs.append(df)

        df = pd.concat(dfs, axis=1, join='outer')

        return df.loc[start_date: end_date]

    def get_cash_funds(self):
        return self.degiro.getdata(degiroapi.Data.Type.CASHFUNDS)

    def get_portfolio_data(self):
        return self.degiro.getdata(degiroapi.Data.Type.PORTFOLIO, True)

    def logout(self):
        self.degiro.logout()


class Portfolio:
    def __init__(self):
        self.portfolio_symbols = []
        self.portfolio_quantities = []
        self.portfolio_value = []
        self.portfolio_value_total = []
        self.portfolio_days = []
        self.total_cost = 0

    def update(self, sess: Broker):
        print('Updating portfolio...')
        th = sess.get_transaction_history()

        self.total_cost = th['cost'].to_numpy().sum()

        first_transaction_date = th.iloc[[0]].index.item()
        product_ids = th['id'].unique().tolist()
        self.portfolio_symbols = th['ticker'].unique().tolist()

        df = sess.get_product_history(product_ids, first_transaction_date, datetime.now())

        self.portfolio_days = df.index

        # construct matrix that holds the quantity of each ticker on each day
        self.portfolio_quantities = np.zeros((len(df.index), len(product_ids)), dtype=int)

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
                        self.portfolio_quantities[i][product_ids.index(row['id'])] = \
                            self.portfolio_quantities[i][product_ids.index(row['id'])] + row['quantity']
                else:
                    self.portfolio_quantities[i][product_ids.index(transactions['id'])] = \
                        self.portfolio_quantities[i][product_ids.index(transactions['id'])] + transactions[
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

    def get_allocation(self):
        return self.portfolio_value[len(self.portfolio_value) - 2] / \
               self.portfolio_value[len(self.portfolio_value) - 2].sum(axis=0) * 100
