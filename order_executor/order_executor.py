from queue import Queue
import MetaTrader5 as mt5
import time
from datetime import datetime

import pandas as pd

from events.events import ExecutionEvent, OrderEvent, SignalType,PlacedPendingOrderEvent
from portfolio.portfolio import Portfolio
from utils.utils import Utils




class OrderExecutor():

    def __init__(self,events_queue: Queue,portfolio:Portfolio,) -> None:

        self.events_queue = events_queue
        self.PORTFOLIO = portfolio

    
    # Evaluate the type of order that wants to be executed, and call the right method
    def execute_order(self,order_event:OrderEvent) -> None:

        if order_event.target_order == "MARKET":
            # Calling the method that executes market orders
            self._execute_market_order(order_event)
        else:
            # Calling the method that adds pending orders
            self._send_pending_order(order_event)

    def _execute_market_order(self,order_event:OrderEvent) -> None:

        # Chek if the order is a buy or a sell
        if order_event.signal == "BUY":
            # Buy Order
            order_type = mt5.ORDER_TYPE_BUY
        elif order_event.signal == "SELL":
            # Sell Order
            order_type = mt5.ORDER_TYPE_SELL
        else:
            raise Exception(f"ORD EXEC: La señal {order_event.signal} no es válida")

        # Market order request creation
        market_order_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            "sl": order_event.sl,
            "tp": order_event.tp,
            "type": order_type,
            "deviation": 0,
            "magic":order_event.magic_number,
            "comment": "FWK Market Order",
            "type_filling": mt5.ORDER_FILLING_IOC, #! Este puede ser necesario cambiarlo dependiendo de el broker
            "price": mt5.symbol_info(order_event.symbol).bid #! Puede ser necesario cambiarlo, es para funcionar en DEMO
        }

        # Send the trade request in order to be executed
        result = mt5.order_send(market_order_request)

        # Verify the result of the order execution
        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Market Order {order_event.signal} para {order_event.symbol} de {order_event.volume} lotes ejecutada correctamente")
            # Generate the execution event and add it to the queue 
            self._create_and_put_execution_event(result)
        else:
            # Send an error message
            print(f"{Utils.dateprint()} - Ha habido un error al ejecutar la Market order {order_event.signal} para {order_event.symbol}: {result.comment}")


    def _check_execution_status(self, order_result) -> bool:

        if order_result.retcode == mt5.TRADE_RETCODE_DONE:
            # Everything fine
            return True
        elif order_result.retcode == mt5.TRADE_RETCODE_DONE_PARTIAL:
            return True
        else:
            return False

    def _send_pending_order(self,order_event:OrderEvent) -> None:
        
        # Check if the order has a STOP or LIMIT type 
        if order_event.target_order == 'STOP':
            order_type = mt5.ORDER_TYPE_BUY_STOP if order_event.signal == "BUY" else mt5.ORDER_TYPE_SELL_STOP
        elif order_event.target_order == "LIMIT":
            order_type = mt5.ORDER_TYPE_BUY_LIMIT if order_event.signal == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
        else:
            raise Exception(f"ORD EXEC: La orden pendiente objetivo {order_event.target_order} no es válida ")

        # Pending order request creation
        pending_order_request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            "sl": order_event.sl,
            "tp": order_event.tp,
            "type": order_type,
            "deviation": 0,
            "magic":order_event.magic_number,
            "comment": "FWK pnding Order",
            "type_filling": mt5.ORDER_FILLING_IOC, #! Este puede ser necesario cambiarlo dependiendo de el broker
            "type_time": mt5.ORDER_TIME_GTC,
            "price": order_event.target_price #! Puede ser necesario cambiarlo, es para funcionar en DEMO
        }

        # Send the trade request to colocate 
        result = mt5.order_send(pending_order_request)
        

        # Verify the result of the order execution
        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Pending Order {order_event.signal} {order_event.target_order} para {order_event.symbol} de {order_event.volume} lotes colocada en {order_event.target_price} correctamente")
            # create & put the right event to the queue
            self._create_and_put_placed_pending_order_event(order_event)
        else:
            # Send an error message
            print(f"{Utils.dateprint()} - Ha habido un error al colocar la orden pendiente {order_event.signal} {order_event.target_order} para {order_event.symbol}: {result.comment}")


    def cancel_pending_order_by_ticket(self,ticket:int) -> None:

        # Access to the pending order of interest
        order = mt5.orders_get(ticket=ticket)[0]

        # Verify that the position exists
        if order is None:
            print(f"{Utils.dateprint()} - ORD EXEC: No existe ninguna orden pendiente con el ticket {ticket}")
            return
        
        # Create the trade request to close the position
        cancel_request ={
            'action': mt5.TRADE_ACTION_REMOVE,
            'order': order.ticket,
            'symbol': order.symbol,
            'volume': order.volume,
        }

        # send the cancel of the request
        result = mt5.order_send(cancel_request)

        # Verify the result of the order cancelation 
        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Orden pendiente con ticket {ticket} en {order.symbol} y volumen {order.volume_initial} se ha cancelado correctamente")
            # create & put the right event to the queue
            self._create_and_put_execution_event(result)
        else:
            # Send an error message
            print(f"{Utils.dateprint()} - Ha habido un error al cerrar la posición {ticket} en {order.symbol} con volumen {order.volume_initial}: {result.comment}")


    def close_position_by_ticket(self,ticket: int) -> None:

        # Access to the position of interest
        position = mt5.positions_get(ticket=ticket)[0]

        # Verify that the position exists
        if position is None:
            print(f"{Utils.dateprint()} - ORD EXEC: No existe ninguna posisión con el ticket {ticket}")
            return
        
        # Create the trade request to close the position
        close_request ={
            'action': mt5.TRADE_ACTION_DEAL,
            'position': position.ticket,
            'symbol': position.symbol,
            'volume': position.volume,
            'type': mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
            'type_filling': mt5.ORDER_FILLING_IOC #! cambiar por si acaso a  IOC
        }

        # send the close_request
        result = mt5.order_send(close_request)

        # Verify the result of the order execution
        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Posición con ticket {ticket} en {position.symbol} y volumen {position.volume} se ha cerrado correctamente")
            # create & put the right event to the queue
            self._create_and_put_execution_event(result)
        else:
            # Send an error message
            print(f"{Utils.dateprint()} - Ha habido un error al cerrar la posición {ticket} en {position.symbol} con volumen {position.volume}: {result.comment}")


    def close_strategy_long_positions_by_symbol(self,symbol:str) -> None:

        # Acceed to all of the open positions in our strategy
        positions = self.PORTFOLIO.get_strategy_open_positions()

        # Filter positions by symbol,direction
        for position in positions:
            if position.symbol == symbol and position.type == mt5.ORDER_TYPE_BUY:
                
                self.close_position_by_ticket(position.ticket)



    def close_strategy_short_positions_by_symbol(self,symbol:str) -> None:

        # Acceed to all of the open positions in our strategy
        positions = self.PORTFOLIO.get_strategy_open_positions()

        # Filter positions by symbol,direction
        for position in positions:
            if position.symbol == symbol and position.type == mt5.ORDER_TYPE_SELL:
                
                self.close_position_by_ticket(position.ticket)



    def _create_and_put_placed_pending_order_event(self,order_event:OrderEvent)->None:

        # placed_pending_order_event creation
        placed_pending_order_event = PlacedPendingOrderEvent(   
                                                                symbol=order_event.symbol,
                                                                signal= order_event.signal,
                                                                target_order=order_event.target_order,
                                                                target_price = order_event.target_price,
                                                                magic_number = order_event.magic_number,
                                                                sl = order_event.sl,
                                                                tp = order_event.tp,
                                                                volume = order_event.volume)
        
        # Add it to the events queue
        self.events_queue.put(placed_pending_order_event)

    

    def _create_and_put_execution_event(self, order_result) -> None:
        """
        Creates an execution event based on the order result and puts it into the events queue.
    
        Args:
            order_result (OrderResult): The result of the order execution.
    
        Returns:
            None
        """

        # Get the result deal information using the POSITION of the deal that it belongs to (instead of the ticket of the deal itself)
        # Because in LIVE the result of the deal is 0 if we check it inmediately
        #deal = mt5.history_deals_get(ticket=order_result.deal)[0]
        deal = None

        # fill_time simulation using the actual moment
        fill_time = datetime.now()

        # We define a short loop, so the server can take its time to generate the deal, we define a maximum of 5 attempts
        for _ in range(5):
            # Wait 0.5 secs
            time.sleep(0.5)
            try:
                deal = mt5.history_deals_get(position=order_result.order)[0]
                # Using position instead of the ticket
            except IndexError:
                deal = None
            
            if not deal:
                # If we don't get the deal, we save fill_time as "now" to get an aprox 
                fill_time = datetime.now()
                continue
            else:
                break

        # If after the loop we haven't got the deal, we show an error message

        if not deal:
            print(f"{Utils.dateprint()} - {Utils.dateprint()} - ORD EXEC: No se ha podido obtener el deal de la ejecución de la orden {order_result.order}, aunque probablemente haya sido ejecutada.")

        # Execution event creation
        execution_event = ExecutionEvent(symbol=order_result.request.symbol,
                                    signal=SignalType.BUY if order_result.request.type == mt5.DEAL_TYPE_BUY else SignalType.SELL,
                                    fill_price=order_result.price,
                                    fill_time=fill_time if not deal else pd.to_datetime(deal.time_msc, unit='ms'),
                                    volume=order_result.request.volume)
        
        # Add the Execution event to the queue
        self.events_queue.put(execution_event)
