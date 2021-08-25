import getpass

import matplotlib.pyplot as plt

from portfolio_visualizer import Broker, Portfolio

if __name__ == '__main__':
    session = Broker().login(input('Username: '), getpass.getpass())

    print('User logged in')

    p = Portfolio()

    p.update(session)

    print('Sharpe ratio : {:.2f}'.format(p.get_sharpe()))
    print('Portfolio gain : {:.2f}%'.format(p.get_profit_loss()))
    print('Allocation : {0}'.format(p.get_allocation()))
    print('Symbols : {0}'.format(p.get_symbols()))
    print('Correlation : {0}'.format(p.get_stocks_correlation()))

    plt.plot(p.portfolio_days, p.portfolio_value_total)
    plt.show()

    plt.matshow(p.get_stocks_correlation())
    plt.show()