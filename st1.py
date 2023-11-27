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
        ('long_period', 200),
        ("maperiod", 20),
        ("devfactor", 2.0),
        ("macd_short", 12),
        ("macd_long", 26),
        ("macd_signal", 9),
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

        # Para realizar un seguimiento de las órdenes pendientes y el precio/comisión de compra
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.short_wma = bt.indicators.WeightedMovingAverage(self.dataclose, period=self.params.short_period)
        self.long_wma = bt.indicators.WeightedMovingAverage(self.dataclose, period=self.params.long_period)

        self.bollinger = bt.indicators.BollingerBands(self.dataclose, period=self.params.maperiod, devfactor=self.params.devfactor)
        
        self.macd = bt.indicators.MACD(self.dataclose, period_me1=self.params.macd_short, period_me2=self.params.macd_long, period_signal=self.params.macd_signal)


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
        self.log('Close, %.2f' % self.dataclose[0])
        upper_band = self.bollinger.lines.bot
        lower_band = self.bollinger.lines.top
        macd_line = self.macd.lines.macd
        signal_line = self.macd.lines.signal
        if self.order:
            return

        if not self.position:
            if (
                self.short_wma[0] > self.long_wma[0] and
                self.dataclose[0] < lower_band and
                macd_line > signal_line
            ):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()

        else:
            if (
                self.short_wma[0] < self.long_wma[0] and
                self.dataclose[0] > upper_band and
                macd_line < signal_line 
            ):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()
    def stop(self):
        self.log('(Short WMA %2d, Long WMA %2d, maperiod %2d, devfactor %2d) Ending Value %.2f' %
                 (self.params.short_period, self.params.long_period, self.params.maperiod, self.params.devfactor,self.broker.getvalue()), doprint=True)

class MyAnalyzer(Analyzer):
    params = (
        ("short_period", 10),
        ("long_period", 100),
        ("maperiod", 50),
        ("devfactor", 2.0),
        ("macd_short", 12),
        ("macd_long", 26),
        ("macd_signal", 9),
    )

    def start(self):
        self.results = []

    def next(self):
        self.results.append(self.strategy.broker.getvalue())

    def stop(self):
        self.final_value = self.results[-1]

if __name__ == '__main__':
    # Crear un objeto cerebro de Backtrader
    cerebro = bt.Cerebro()

    # Agregar una estrategia al cerebro
    strats = cerebro.optstrategy(
        MyStrategy,
        short_period=range(45, 55),
        long_period=range(195, 225),
        maperiod=range(15, 25),
        devfactor=range(2, 3),
    )
    #cerebro.addstrategy(MyStrategy)
    
    # Crear un objeto de datos a partir del archivo CSV
    datapath = 'orcl-1995-2014.txt'
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2010, 1, 3),
        todate=datetime.datetime(2014, 12, 30),
        reverse=False
    )

    # Agregar el objeto de datos al cerebro
    cerebro.adddata(data)

    # Configurar el capital inicial
    cerebro.broker.set_cash(1000.0)

    # Agregar un sizer con tamaño fijo
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Configurar la comisión
    cerebro.broker.setcommission(commission=0.001)

    # Imprimir el saldo inicial
    print(f"Saldo Inicial: {cerebro.broker.getvalue()}")

    # Ejecutar el backtest
# Añadir el analizador personalizado
    cerebro.addanalyzer(MyAnalyzer)

    # Ejecutar la optimización
    results = cerebro.run(maxcpus=1)

    # Obtener los resultados de la optimización
    final_values = [a[0].analyzers.myanalyzer.final_value for a in results]

    # Obtener los parámetros correspondientes al mejor resultado
    best_params = results[final_values.index(max(final_values))][0].params
    # Imprimir el saldo final
    print(f"Saldo Final: {cerebro.broker.getvalue()}")

    print("Mejores parámetros:", best_params)

