import degiroapi
from datetime import datetime
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
                'name': info['name'],
                'ticker': info['symbol'],
                'quantity': transaction['quantity'],
                'cost': transaction['totalInBaseCurrency'],
                'fee': transaction['feeInBaseCurrency']
            }

            transaction_list.append(tsn)

        df = pd.DataFrame(transaction_list)

        return df.set_index('date')

    def get_cash_funds(self):
        cashfunds = self.degiro.getdata(degiroapi.Data.Type.CASHFUNDS)
        print(cashfunds)

    def logout(self):
        self.degiro.logout()

