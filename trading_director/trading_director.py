import queue
import time
from typing import Dict,Callable

from notifications.notifications import NotificationService
from order_executor.order_executor import OrderExecutor
from position_sizer.position_sizer import PositionSizer
from risk_manager.risk_manager import RiskManager
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator
from data_provider.data_provider import DataProvider
from events.events import DataEvent, ExecutionEvent, OrderEvent, SignalEvent, SizingEvent,PlacedPendingOrderEvent
from utils.utils import Utils


class TradingDirector():

    def __init__(self,events_queue:queue.Queue, data_provider:DataProvider,
                signal_generator:ISignalGenerator, position_sizer:PositionSizer,
                risk_manager:RiskManager, order_executor:OrderExecutor, notification_service:NotificationService) -> None:

        self.events_queue = events_queue

        #Reference to the diferent modules
        self.DATA_PROVIDER = data_provider
        self.SIGNAL_GENERATOR = signal_generator
        self.POSITION_SIZER = position_sizer
        self.RISK_MANAGER = risk_manager
        self.ORDER_EXECUTOR = order_executor
        self.NOTIFICATIONS = notification_service

        #Trading Controller
        self.continue_trading:bool = True

        #Event hanlder creation
        self.event_handler:Dict[str,Callable] = {
            "DATA": self._handle_data_event,
            "SIGNAL": self._handle_signal_event,
            "SIZING": self._handle_sizing_event,
            "ORDER" : self._handle_order_event,
            "EXECUTION": self._handle_execution_event,
            "PENDING": self._handle_pending_order_event
        }


    def _handle_data_event(self,event:DataEvent):
        #It manages the DataEvent events
        print(f"{Utils.dateprint()} -  Recibido DATA EVENT de {event.symbol} - Último precio de cierre {event.data.close}")

        self.SIGNAL_GENERATOR.generate_signals(event)


    def _handle_signal_event(self,event:SignalEvent):
        #Process the SignalEvent
        print(f"{Utils.dateprint()} - Recibido SIGNAL EVENT {event.signal} para {event.symbol}")
        self.POSITION_SIZER.size_signal(event,self.DATA_PROVIDER)


    def _handle_sizing_event(self, event:SizingEvent):
        print(f"{Utils.dateprint()} - Recibido SIZING EVENT con volumen {event.volume} para {event.signal} en {event.symbol}")
        self.RISK_MANAGER.asses_order(event)


    def _handle_order_event(self,event:OrderEvent):
        print(f"{Utils.dateprint()} - Recibido ORDER EVENT con volumen {event.volume} para {event.signal} en {event.symbol}")
        self.ORDER_EXECUTOR.execute_order(event)


    def _handle_execution_event(self,event:ExecutionEvent):
        print(f"{Utils.dateprint()} - Recibido EXECUTION EVENT {event.signal} en {event.symbol}, con volumen {event.volume} al precio {event.fill_price}")
        self._process_execution_or_pending_events(event)


    def _handle_pending_order_event(self,event:PlacedPendingOrderEvent):
        print(f"{Utils.dateprint()} - Recibido PLACED PENDING ORDER EVENT con volumen {event.volume} para {event.signal} {event.target_order} en {event.symbol} al precio {event.target_price}")
        self._process_execution_or_pending_events(event)


    def _process_execution_or_pending_events(self,event:ExecutionEvent | PlacedPendingOrderEvent):

        if isinstance(event, ExecutionEvent):
            self.NOTIFICATIONS.send_notification(title=f"{event.symbol} - MARKET ORDER", message=f"Ejecutada MARKET ORDER {event.signal} en {event.symbol}, con volumen {event.volume} al precio {event.fill_price}")

        elif isinstance(event,PlacedPendingOrderEvent):
            self.NOTIFICATIONS.send_notification(title=f"{event.symbol} - PENDING PLACED", message=f"Colocada PENDING ORDER con volumen {event.volume} para {event.signal} {event.target_order} en {event.symbol} al precio {event.target_price}")
        
        else:
            pass

    def _handle_none_event(self,event):
        print(f"{Utils.dateprint()} - ERROR: Recibido evento nulo, terminando la ejecución del Framework")
        self.continue_trading = False

    def _handle_unkown_event(self,event):
        print(f"{Utils.dateprint()} - ERROR: Recibido evento desconocido, terminando la ejecución del Framework")
        self.continue_trading = False


    def execute(self) -> None:

        #Main loop defiinition
        while self.continue_trading:
            try:
                event = self.events_queue.get(block=False)     #Remember this is a FIFO queue

            except queue.Empty:
                self.DATA_PROVIDER.check_for_new_data()

            else:
                if event is not None:
                    handler = self.event_handler.get(event.event_type, self._handle_unkown_event)
                    handler(event)
                else:
                    self._handle_none_event(event)
            
            time.sleep(0.01)

        print(f"{Utils.dateprint()} - FIN")

