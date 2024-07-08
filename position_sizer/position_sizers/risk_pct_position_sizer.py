from data_provider.data_provider import DataProvider
from events.events import SignalEvent
from position_sizer.Properties.position_sizer_properties import RiskPctSizingProps
from ..interfaces.position_sizer_interface import IPositionSizer
import MetaTrader5 as mt5

class RiskPctPositionSizer(IPositionSizer):

    def __init__(self,properites:RiskPctSizingProps) -> None:
        self.risk_pct = properites.risk_pct

    def size_signal(self, signal_event: SignalEvent, data_provider: DataProvider) -> float:

        #Check if the risk is positive
        if self.risk_pct <= 0:
            print(f"ERROR (RiskPctPositionSizer): El porcentage de riesgo introducido {self.risk_pct} no es válido.")
            return 0.0
        #Check that the sl != 0
        if signal_event.sl  <= 0.0:
            print(f"ERROR (RiskPctPositionSizer): El valor del SL: {signal_event.sl} no es válido.")
            return 0.0
        
        #Access to the account info (To get the account currency)
        account_info = mt5.account_info()

        #Access to the symbol info (To calculate the risk)
        symbol_info = mt5.symbol_info(signal_event.symbol)

        if signal_event.target_order == "MARKET":
            #Get the estimated entry price
            last_tick = data_provider.get_latest_tick(signal_event.symbol)
            entry_price = last_tick['ask'] if signal_event.signal == "BUY" else last_tick['bid']
        
        #If it is a pending order (limit or stop)
        else:
            #We take the price of the signal_event itself
            entry_price = signal_event.target_price
        
        
