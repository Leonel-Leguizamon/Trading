from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import backtrader as bt
from strategy import MyStrategy
from data import create_data

def run_strategy():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MyStrategy)

    data = create_data()

    cerebro.adddata(data)

    cerebro.broker.set_cash(1000.0)
    cerebro.broker.setcommission(commission=0.001)

    print(f"Saldo Inicial: {cerebro.broker.getvalue()}")

    cerebro.run()

    print(f"Saldo Final: {cerebro.broker.getvalue()}")
    cerebro.plot()

if __name__ == '__main__':
    run_strategy()
