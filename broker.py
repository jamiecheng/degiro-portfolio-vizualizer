import degiroapi
from datetime import datetime, timedelta
import local_config
import pandas as pd


class Broker:
    def __init__(self):
        self.degiro = degiroapi.DeGiro()

    def login(self, username, password):
        return self.degiro.login(username, password)

    def get_transactions(self, start, end):
        transactions = self.degiro.transactions(start, end)
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

        df = pd.DataFrame(transaction_list)

        return df.set_index('date')

    def get_product_history(self, product_ids, start_date, end_date):
        dfs = []

        for product_id in product_ids:
            res = self.degiro.real_time_price(product_id, degiroapi.Interval.Type.Max)

            # reformat the retarded data format
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

        return df.loc[start_date.strftime('%Y-%m-%d'): end_date.strftime('%Y-%m-%d')]

    def get_cash_funds(self):
        return self.degiro.getdata(degiroapi.Data.Type.CASHFUNDS)

    def logout(self):
        self.degiro.logout()


account = Broker()

print(account.login(local_config.username, local_config.password))

print(account.get_product_history([1157277, 1147582], datetime(2010, 1, 1), datetime.now()))

account.logout()
