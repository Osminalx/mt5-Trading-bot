from typing import Protocol

from events.events import SizingEvent


class IRiskManager(Protocol):
    
    def asses_order(self,sizing_event:SizingEvent) -> float | None :
        ...