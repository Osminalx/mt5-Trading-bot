from typing import Protocol
from data_provider.data_provider import DataProvider
from events.events import DataEvent, SignalEvent
from order_executor.order_executor import OrderExecutor
from portfolio.portfolio import Portfolio


class ISignalGenerator(Protocol):

    def generate_signals(self,data_event:DataEvent,data_provider:DataProvider, portfolio:Portfolio,order_executor:OrderExecutor) -> SignalEvent | None:
        ...

    

