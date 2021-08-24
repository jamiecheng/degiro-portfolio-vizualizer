import json

import degiroapi
from datetime import datetime, timedelta
import pandas as pd
import sqlite3


class Broker:
    def __init__(self):
        self.degiro = degiroapi.DeGiro()

        self.conn = sqlite3.connect("account_cache.db")

    def login(self, username, password):
        return self.degiro.login(username, password)

    def get_transaction_history(self):
        if self.__db_check_if_table_exists('transaction_history'):
            date = self.__db_get_last_update_date('transaction_history')

            if date < datetime.now().strftime('%Y-%m-%d'):
                return self.__update_transaction_history()
            else:
                print('cache is up to date')
                df = pd.read_sql('SELECT * FROM transaction_history', self.conn,
                                 parse_dates={"date": "%Y-%m-%d"}).set_index('date')

                return df
        else:
            print('db not found, retrieving data')
            return self.__update_transaction_history()

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

    def __update_transaction_history(self):
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

        df.to_sql('transaction_history', self.conn, if_exists='replace')

        self.__db_set_last_update_date('transaction_history', datetime.now())

        return df

    def __db_check_if_table_exists(self, name):
        c = self.conn.cursor()
        c.execute('SELECT COUNT(name) FROM sqlite_master WHERE type=\'table\' AND name=\'' + name + '\'')
        if c.fetchone()[0] == 1:
            c.close()
            return True

        c.close()
        return False

    def __db_get_last_update_date(self, name):
        with open('db.stats', 'r') as file:
            data = json.load(file)

            return data[name]

    def __db_set_last_update_date(self, name, date):
        data = {}

        with open('db.stats', 'w+') as file:
            if len(file.read()) > 0:
                data = json.load(file)

            data[name] = date.strftime('%Y-%m-%d')

            json.dump(data, file)
