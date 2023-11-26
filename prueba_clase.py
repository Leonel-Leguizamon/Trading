import math
import time

from arquants import Strategy
from arquants import Order


class CompraVentaMEP(Strategy):

    def __init__(self, accion='compra', monto=1000, monto_maximo=500, tipo_cambio=900):
        self.accion = accion
        self.monto = monto
        self.monto_maximo = monto_maximo
        self.tipo_cambio = tipo_cambio
        self.operado = 0
        self.ordenes_ars = dict()
        self.ordenes_usd = dict()

    def next(self):
        self.log('next')
        restante = self.monto - self.operado
        self.log('restante {}'.format(restante))
        if restante > 0:
            monto_min = min(restante, self.monto_maximo)
            if self.accion == 'compra':
                self.log('modo compra')
                precio_ars = self.data0.offer_px[0] if not math.isnan(self.data0.offer_px[0]) else None
                precio_usd = self.data1.bid_px[0] if not math.isnan(self.data1.bid_px[0]) else None

                self.log('precio_ars {} precio_usd {}'.format(precio_ars, precio_usd))
                if precio_ars and precio_usd:
                    tam_ars = self.data0.offer_qty[0]
                    tam_usd = self.data1.bid_qty[0]
                    tam_monto = monto_min / precio_usd
                    self.log('tam_ars {} tam_usd {} tam_monto {}'.format(tam_ars, tam_usd, tam_monto))
                    tam_orden = math.floor(min(tam_ars, tam_usd, tam_monto))
                    tc_mercado = precio_ars / precio_usd
                    self.log('tc_mercado {} tipo_cambio {}'.format(tc_mercado, self.tipo_cambio))
                    if tc_mercado <= self.tipo_cambio:
                        orden_ars = self.buy(data=self.data0, price=precio_ars, size=tam_orden, exectype=Order.Limit, send=False)
                        orden_usd = self.sell(data=self.data1, price=precio_usd, size=tam_orden, exectype=Order.Limit, send=False)
                        self.log('Se enviaron las ordenes con id {} y {}'.format(orden_ars.m_orderId, orden_usd.m_orderId))
                        self.ordenes_ars[orden_ars.m_orderId] = orden_ars
                        self.ordenes_usd[orden_usd.m_orderId] = orden_usd
                        self.sendOrders([orden_ars, orden_usd])
                        time.sleep(2)
            else: # modo venta
                precio_ars = self.data0.bid_px[0]
                precio_usd = self.data1.offer_px[0]
                tam_ars = self.data0.bid_qty[0]
                tam_usd = self.data1.offer_qty[0]
                tam_monto = monto_min / precio_usd

                tam_orden = math.floor(min(tam_ars, tam_usd, tam_monto))

                if tam_orden < 0:
                    self.log('tamaño 0')
                    return

                tc_mercado = precio_ars / precio_usd
                self.log('tc_mercado {}'.format(tc_mercado))
                if tc_mercado >= self.tipo_cambio:
                    order_ars = self.sell(data=self.data0, price=precio_ars, size=tam_orden, exectype=Order.Limit, send=False)
                    order_usd = self.buy(data=self.data1, price=precio_usd, size=tam_orden, exectype=Order.Limit, send=False)
                    self.ordenes_ars[order_ars.m_orderId] = order_ars
                    self.ordenes_usd[order_usd.m_orderId] = order_usd

                    self.sendOrders([order_ars, order_usd])
                    time.sleep(2)
        else:
            self.log('Se completo el monto')
            self.pause()

    def notify_order(self, order):
        if order.status is Order.Completed:
            self.log('Se completo la orden de id: {} [{}@{}]'.format(order.m_orderId, abs(order.size), order.price))
            if order.m_orderId in self.ordenes_usd.keys():
                self.operado += abs(order.size * order.price / order.data.price_size)
                self.log('OPERADO: {} - RESTANTE: {}'.format(self.operado, self.monto - self.operado))

        if order.status is Order.Accepted:
            self.log('Se acepto la orden de id: {} [{}@{}]'.format(order.m_orderId, abs(order.size), order.price))
            self.cancel(order)

        if order.status is Order.Partial:
            self.log('La orden de id: {} [{}@{}] se opero parcialmente. Cancelando restante..'.format(order.m_orderId,
                                                                                                      abs(order.size),
                                                                                                      order.price))

        if order.status in (Order.Canceled, Order.Cancelled):
            self.log('Se cancelo la orden de id: {} [{}@{}]'.format(order.m_orderId, abs(order.size), order.price))

        if order.status is Order.Rejected:
            self.log('Se rechazo la orden de id: {} [{}@{}]'.format(order.m_orderId, abs(order.size), order.price))
