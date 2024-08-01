import queue
import time
from datetime import datetime
from typing import Dict,Callable

from position_sizer.position_sizer import PositionSizer
from risk_manager.risk_manager import RiskManager
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator
from data_provider.data_provider import DataProvider
from events.events import DataEvent, OrderEvent, SignalEvent, SizingEvent


class TradingDirector():

    def __init__(self,events_queue:queue.Queue, data_provider:DataProvider,signal_generator:ISignalGenerator, position_sizer:PositionSizer,risk_manager:RiskManager) -> None:

        self.events_queue = events_queue

        #Reference to the diferent modules
        self.DATA_PROVIDER = data_provider
        self.SIGNAL_GENERATOR = signal_generator
        self.POSITION_SIZER = position_sizer
        self.RISK_MANAGER = risk_manager

        #Trading Controller
        self.continue_trading:bool = True

        #Event hanlder creation
        self.event_handler:Dict[str,Callable] = {
            "DATA": self._handle_data_event,
            "SIGNAL": self._handle_signal_event,
            "SIZING": self._handle_sizing_event,
            "ORDER" : self._handle_order_event
        }

    def _dateprint(self) -> str:
        return datetime.now().strftime("%d/%m/%Y  %H:%M:%S.%f")[:-3]


    def _handle_data_event(self,event:DataEvent):
        #It manages the DataEvent events
        print(f"{self._dateprint()} -  Recibido DATA EVENT de {event.symbol} - Último precio de cierre {event.data.close}")

        self.SIGNAL_GENERATOR.generate_signals(event)


    def _handle_signal_event(self,event:SignalEvent):
        #Process the SignalEvent
        print(f"{self._dateprint()} - Recibido SIGNAL EVENT {event.signal} para {event.symbol}")
        self.POSITION_SIZER.size_signal(event,self.DATA_PROVIDER)


    def _handle_sizing_event(self, event:SizingEvent):
        print(f"{self._dateprint()} - Recibido SIZING EVENT con volumen {event.volume} para {event.signal} en {event.symbol}")
        self.RISK_MANAGER.asses_order(event)

    def _handle_order_event(self,event:OrderEvent):
        print(f"{self._dateprint()} - Recibido ORDER EVENT con volumen {event.volume} para {event.signal} en {event.symbol}")


    def execute(self) -> None:

        #Main loop defiinition
        while self.continue_trading:
            try:
                event = self.events_queue.get(block=False)     #Remember this is a FIFO queue

            except queue.Empty:
                self.DATA_PROVIDER.check_for_new_data()

            else:
                if event is not None:
                    handler = self.event_handler.get(event.event_type)
                    handler(event)
                else:
                    self.continue_trading = False
                    print("ERROR: Recibido evento nulo, terminando la ejecución del Framework")
            
            time.sleep(0.01)

        print("FIN")

