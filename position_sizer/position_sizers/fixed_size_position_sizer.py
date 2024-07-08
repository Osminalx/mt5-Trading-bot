from data_provider.data_provider import DataProvider
from events.events import SignalEvent
from position_sizer.Properties.position_sizer_properties import FixedSizingProps
from ..interfaces.position_sizer_interface import IPositionSizer

class FixedSizePositionSIzer(IPositionSizer):

    def __init__(self,properites:FixedSizingProps) -> None:

        self.fixed_volume = properites.volume

    def size_signal(self, signal_event: SignalEvent, data_provider: DataProvider) -> float:
        #Return the size of a fixed position
        
        if self.fixed_volume >= 0.0:
            return self.fixed_volume
        else:
            return 0.0
