from data_provider.data_provider import DataProvider
from events.events import DataEvent
from .properties.signal_generator_properties import BaseSignalProps, MACrossoverProps
from .interfaces.signal_generator_interface import ISignalGenerator
from .signals.signal_ma_crossover import SignalMACrossover
from portfolio.portfolio import Portfolio
from order_executor.order_executor import OrderExecutor

from queue import Queue


class SignalGenerator(ISignalGenerator):
    
    def __init__(self, events_queue: Queue, data_provider:DataProvider, portfolio:Portfolio, order_executor:OrderExecutor,signal_properties: BaseSignalProps) -> None:

        self.events_queue = events_queue
        self.DATA_PROVIDER = data_provider
        self.PORTFOLIO = portfolio
        self.ORDER_EXECUTOR = order_executor

        self.signal_generator_method = self._get_signal_generator_method(signal_properties)


    def _get_signal_generator_method(self,signal_props:BaseSignalProps) -> ISignalGenerator:

        if isinstance(signal_props,MACrossoverProps):
            return SignalMACrossover(signal_props)
        # If you want to add more signal generators, you will need to add as most of elifs as signal generators
        else:
            raise Exception(f"ERROR: método de sizing desconocido: {signal_props}")

    
    def generate_signals(self, data_event: DataEvent) -> None:

        # Get the signal event using the right entrance logic
        signal_event = self.signal_generator_method.generate_signals(data_event,self.DATA_PROVIDER,self.PORTFOLIO,self.ORDER_EXECUTOR)

        # Check if signal_event is None and add it to the queue in case it isn't
        if signal_event is not None:
            self.events_queue.put(signal_event)