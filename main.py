import getpass
from datetime import datetime
import matplotlib.pyplot as plt

from portfolio_visualizer.portfolio_visualizer import Broker, Portfolio


if __name__ == '__main__':
    session = Broker().login(input('Username: '), getpass.getpass())

    print('User logged in')

    p = Portfolio()

    p.update(session)

    print('Portfolio gain : {:.2f}%'.format(p.get_net_change()))
    print('Benchmark with VWRL {:.2f}%'.format(p.benchmark(4586985, session)))
    print('Sharpe ratio : {:.2f}'.format(p.get_sharpe()))
    print(p.get_allocation())

    p.get_value_over_time().plot()

    plt.matshow(p.get_stocks_correlation(datetime(2010, 1, 1), datetime.now()))

    plt.show()
