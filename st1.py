from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import os.path
import sys
import backtrader as bt
from backtrader import Analyzer

# Crear una estrategia personalizada
class MyStrategy(bt.Strategy):
    params = (
        ('short_period', 50),
        ('long_period', 150),
        ("maperiod", 20),
        ("devfactor", 2.0),
        ("macd_short", 24),
        ("macd_long", 52),
        ("macd_signal", 18),
        ("rsi_period", 14),
        ("obv_period", 20),
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Función de registro para esta estrategia '''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Guardar una referencia a la línea de "close" en la serie de datos[0]
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume
        # Para realizar un seguimiento de las órdenes pendientes y el precio/comisión de compra
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.short_wma = bt.indicators.WeightedMovingAverage(self.dataclose, period=self.params.short_period)
        self.long_wma = bt.indicators.WeightedMovingAverage(self.dataclose, period=self.params.long_period)

        self.obv = 0
        
        self.bollinger = bt.indicators.BollingerBands(self.dataclose, period=self.params.maperiod, devfactor=self.params.devfactor)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
        #self.macd = bt.indicators.MACD(self.dataclose, period_me1=self.params.macd_short, period_me2=self.params.macd_long, period_signal=self.params.macd_signal)


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Venta
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.dataclose[0] > self.dataclose[-1]:
            self.obv += self.datavolume[0]
        elif self.dataclose[0] < self.dataclose[-1]:
            self.obv -= self.datavolume[0]

        self.log('Close, %.2f' % self.dataclose[0])
        upper_band = self.bollinger.lines.top
        lower_band = self.bollinger.lines.bot
        #macd_line = self.macd.lines.macd
        #signal_line = self.macd.lines.signal
        rsi_v = self.rsi[0]
        if self.order:
            return

        if not self.position:
            if (
                self.short_wma[0] > self.long_wma[0] and
                self.obv > 0 or
                self.dataclose[0] < lower_band and
                rsi_v < 30 
            ):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()

        else:
            if (
                self.short_wma[0] < self.long_wma[0] and
                self.obv < 0 or
                self.dataclose[0] > upper_band and
                rsi_v > 70
            ):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()

    def stop(self):
        self.log('(Short WMA %2d, Long WMA %2d, maperiod %2d, devfactor %2d) Ending Value %.2f' %
                 (self.params.short_period, self.params.long_period, self.params.maperiod, self.params.devfactor,self.broker.getvalue()), doprint=True)

if __name__ == '__main__':
    # Crear un objeto cerebro de Backtrader
    cerebro = bt.Cerebro()

    # Agregar una estrategia al cerebro
    cerebro.addstrategy(MyStrategy)
    
    # Crear un objeto de datos a partir del archivo CSV
    datapath = 'orcl-1995-2014.txt'
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(1995, 12, 30),
        todate=datetime.datetime(2014, 12, 30),
        reverse=False
    )

    # Agregar el objeto de datos al cerebro
    cerebro.adddata(data)

    # Configurar el capital inicial
    cerebro.broker.set_cash(1000.0)

    # Agregar un sizer con tamaño fijo
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # Configurar la comisión
    cerebro.broker.setcommission(commission=0.001)

    # Imprimir el saldo inicial
    print(f"Saldo Inicial: {cerebro.broker.getvalue()}")

    # Ejecutar
    results = cerebro.run()
    # Imprimir el saldo final
    print(f"Saldo Final: {cerebro.broker.getvalue()}")
    cerebro.plot()

    

