from typing import Protocol
from events.events import DataEvent


class ISignalGenerator(Protocol):

    def generate_signals(self,data_event:DataEvent) -> None:
        ...

    

