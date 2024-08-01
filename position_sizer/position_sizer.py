from data_provider.data_provider import DataProvider
from events.events import SignalEvent,SizingEvent
from .interfaces.position_sizer_interface import IPositionSizer
from .properties.position_sizer_properties  import BaseSizerProps, MinSizingProps, FixedSizingProps, RiskPctSizingProps
from .position_sizers.min_size_position_sizer import MinSizePositionSizer
from .position_sizers.fixed_size_position_sizer import FixedSizePositionSIzer
from .position_sizers.risk_pct_position_sizer import RiskPctPositionSizer
from queue import Queue
import MetaTrader5 as mt5


class PositionSizer(IPositionSizer):

    def __init__(self,events_queue:Queue, data_provider:DataProvider ,sizing_properties:BaseSizerProps) -> None:
        self.events_queue = events_queue
        self.DATA_PROVIDER = data_provider
        self.position_sizer_method = self._get_position_sizing_method(sizing_properties)




    def _create_and_put_sizing_event(self,signal_event:SignalEvent,volume:float) -> None:
        
        # Create the sizingEvent from the signal_event and the volume
        sizing_event = SizingEvent(
                                symbol= signal_event.symbol,
                                signal= signal_event.signal,
                                target_order= signal_event.target_order,
                                target_price= signal_event.target_price,
                                magic_number= signal_event.magic_number,
                                sl= signal_event.sl,
                                tp= signal_event.tp,
                                volume= volume
                                )

        # add the sizing event to the events queue
        self.events_queue.put(sizing_event)




    def  _get_position_sizing_method(self,sizing_props: BaseSizerProps) -> IPositionSizer:
        """
        Returns an instance of the appropiate position sizer in function of the object of properties recieved
        """

        if isinstance(sizing_props, MinSizingProps):
            return MinSizePositionSizer()
        
        elif isinstance(sizing_props, FixedSizingProps):
            return FixedSizePositionSIzer(properites= sizing_props)
        
        elif isinstance(sizing_props, RiskPctSizingProps):
            return RiskPctPositionSizer(properites= sizing_props)
        
        else:
            raise Exception(f"ERROR: Método de sizing desconocido: {sizing_props} ")





    def size_signal(self, signal_event: SignalEvent, data_provider: DataProvider) -> None:

        # Get the right volume with the sizing method
        volume = self.position_sizer_method.size_signal(signal_event,self.DATA_PROVIDER)

        #security control
        if volume < mt5.symbol_info(signal_event.symbol).volume_min:
            print(f"ERROR: El volumen {volume} es menor al volumen mínimo admitido por el símbolo {signal_event.symbol}")
            return

        # Create and put the sizing event into the events queue
        self._create_and_put_sizing_event(signal_event, volume)
