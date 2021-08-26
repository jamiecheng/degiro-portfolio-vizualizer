import getpass
from datetime import datetime
import matplotlib.pyplot as plt

from portfolio_visualizer import Broker, Portfolio


if __name__ == '__main__':
    session = Broker().login(input('Username: '), getpass.getpass())

    print('User logged in')

    p = Portfolio()

    p.update(session)

    print('Sharpe ratio : {:.2f}'.format(p.get_sharpe()))
    print('Portfolio gain : {:.2f}%'.format(p.get_profit_loss()))
    print(p.get_allocation())
    print(p.get_stocks_correlation(datetime(2010, 1, 1), datetime.now()))

    p.get_value_over_time().plot()

    plt.show()
