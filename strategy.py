from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ("maperiod", 20),
        ("devfactor", 2.0),
        ("macd_short", 24),
        ("macd_long", 52),
        ("macd_signal", 18),
        ("rsi_period", 14),
        ('printlog', False),
    )

    def __init__(self):
        # Guardar una referencia a la línea de "close" en la serie de datos[0]
        self.dataclose = self.datas[0].close
        
        # Para realizar un seguimiento de las órdenes pendientes y el precio/comisión de compra
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Indicadores a utilizar
        self.bollinger = bt.indicators.BollingerBands(
            self.dataclose, 
            period=self.params.maperiod, 
            devfactor=self.params.devfactor
        )
        
        self.rsi = bt.indicators.RelativeStrengthIndex(
            period=self.params.rsi_period
        )
        
        self.macd = bt.indicators.MACD(
            self.dataclose, 
            period_me1=self.params.macd_short, 
            period_me2=self.params.macd_long, 
            period_signal=self.params.macd_signal
        )

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])

        upper_band = self.bollinger.lines.top
        lower_band = self.bollinger.lines.bot
        macd_line = self.macd.lines.macd
        signal_line = self.macd.lines.signal

        if self.order:
            return

        bollinger_buy = self.dataclose[0] < lower_band
        bollinger_sell = self.dataclose[0] > upper_band
        rsi_buy = self.rsi[0] < 35
        rsi_sell = self.rsi[0] > 65
        macd_buy = macd_line > signal_line

        if not self.position:
            if (bollinger_buy and rsi_buy or bollinger_buy and macd_buy):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                cash_to_spend = self.broker.getvalue() * 0.9  # Obtener el saldo actual
                #print("CASH A GASTAR: ", cash_to_spend)
                size = int(cash_to_spend // self.dataclose[0])  # Calcular el tamaño basado en el precio de cierre
                self.order = self.buy(size=size)
        else:
            if (bollinger_sell and rsi_sell or bollinger_sell and (not macd_buy)):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell(size=self.position.size)


    def log(self, txt, dt=None, doprint=False):
            ''' Función de registro para esta estrategia '''
            if self.params.printlog or doprint:
                dt = dt or self.datas[0].datetime.date(0)
                print('%s, %s' % (dt.isoformat(), txt))

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
