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

            try:
                tsn = {
                    'date': date.strftime('%Y-%m-%d'),
                    'id': transaction['productId'],
                    'name': info['name'],
                    'ticker': info['symbol'],
                    'quantity': transaction['quantity'],
                    'cost': transaction['totalInBaseCurrency'],
                    'fee': transaction['feeInBaseCurrency'],
                    'conversion_rate': None
                }

                if 'fxRate' in transaction:
                    tsn['conversion_rate'] = transaction['fxRate']

                transaction_list.append(tsn)
            except KeyError:
                print('Transaction history key error')

        df = pd.DataFrame(transaction_list).set_index('date')

        return df

    def get_product_history(self, product_ids, start_date, end_date) -> pd.DataFrame:
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
        ret = self.degiro.getdata(degiroapi.Data.Type.CASHFUNDS)[0]

        ret = ret.split(' ')

        return float(ret[1])

    def get_portfolio_data(self):
        return self.degiro.getdata(degiroapi.Data.Type.PORTFOLIO, True)

    def logout(self):
        self.degiro.logout()


class Portfolio:
    def __init__(self):
        self.transaction_history_df = None
        self.portfolio_quantities_df = None
        self.stock_history_df = None
        self.cash_fund = None

    def update(self, session: Broker):
        print('Updating portfolio...')
        self.cash_fund = session.get_cash_funds()

        self.transaction_history_df = session.get_transaction_history()

        first_transaction_date = self.transaction_history_df.iloc[[0]].index.item()
        product_ids = self.transaction_history_df['id'].unique().tolist()
        fxrate = self.transaction_history_df.groupby('ticker', sort=False).mean()['conversion_rate'].fillna(
            1).to_numpy()

        hist = session.get_product_history(product_ids, first_transaction_date,
                                           datetime.now()).dropna()

        self.stock_history_df = hist.div(fxrate, axis=1)

        # construct matrix that holds the quantity of each ticker on each day
        portfolio_quantities = np.zeros((len(self.stock_history_df.index), len(product_ids)), dtype=int)

        # iterate through each day since the first transaction
        for i in range(0, len(self.stock_history_df.index)):
            # we start the day with the same holdings as the day before
            if i != 0:
                portfolio_quantities[i] = portfolio_quantities[i - 1]

            # is there a transaction at this date?
            if self.stock_history_df.index[i].strftime('%Y-%m-%d') in self.transaction_history_df.index:
                # get all transactions on this day
                transactions = self.transaction_history_df.loc[str(self.stock_history_df.index[i].strftime('%Y-%m-%d'))]

                if isinstance(transactions, pd.DataFrame):
                    for index, row in transactions.iterrows():
                        portfolio_quantities[i][product_ids.index(row['id'])] = \
                            portfolio_quantities[i][product_ids.index(row['id'])] + row['quantity']
                else:
                    portfolio_quantities[i][product_ids.index(transactions['id'])] = \
                        portfolio_quantities[i][product_ids.index(transactions['id'])] + transactions[
                            'quantity']

        self.portfolio_quantities_df = pd.DataFrame(data=portfolio_quantities,
                                                    index=self.stock_history_df.index,
                                                    columns=self.stock_history_df.columns.values)

        return self

    def get_symbols(self) -> list:
        return self.stock_history_df.columns.values

    def get_value_over_time(self) -> pd.Series:
        s = self.stock_history_df.multiply(self.portfolio_quantities_df).sum(axis=1)

        s.name = 'Portfolio'

        return s

    def get_sharpe(self) -> float:
        daily_return = self.get_value_over_time().pct_change(1)

        return (252 ** 0.5) * (daily_return.mean() / daily_return.std())

    def get_net_change(self) -> float:
        portfolio_total_value = \
            self.stock_history_df.multiply(self.portfolio_quantities_df).sum(axis=1).tail(1).iloc[0] + self.cash_fund

        total_cost = self.transaction_history_df['cost'].sum()

        return ((portfolio_total_value + total_cost) / -total_cost) * 100

    def get_allocation(self) -> pd.DataFrame:
        current_holding = self.stock_history_df.multiply(self.portfolio_quantities_df).tail(1)

        current_holding['EUR'] = self.cash_fund

        current_holding = current_holding.apply(lambda x: x / x.sum(), axis=1) * 100

        return current_holding.loc[:, (current_holding != 0).any(axis=0)]

    def get_stocks_correlation(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        df = self.stock_history_df.loc[start_date:end_date]

        return df.corr()

    def get_account_value(self) -> float:
        return self.stock_history_df.multiply(self.portfolio_quantities_df).sum(axis=1).tail(1).iloc[0] + self.cash_fund

    def benchmark(self, product_id: int, session: Broker) -> float:
        pdf = self.get_value_over_time()
        df = session.get_product_history([product_id], pdf.index[0], pdf.index[len(pdf.index) - 1]).iloc[:, 0]

        daily_return_df = df.pct_change(1) * 100

        return self.get_net_change() - daily_return_df.sum()
