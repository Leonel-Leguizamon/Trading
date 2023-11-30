from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import os

def create_data():
    # Obtén la ruta completa del archivo de datos
    datapath = os.path.join('datasets', 'orcl-1995-2014.txt')

    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(1995, 12, 30),
        todate=datetime.datetime(2000, 12, 30),
        reverse=False
    )

    return data
