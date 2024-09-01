from data_provider.data_provider import DataProvider
from events.events import SignalEvent
from position_sizer.properties.position_sizer_properties import RiskPctSizingProps
from ..interfaces.position_sizer_interface import IPositionSizer
import MetaTrader5 as mt5
from utils.utils import Utils

class RiskPctPositionSizer(IPositionSizer):

    def __init__(self,properites:RiskPctSizingProps) -> None:
        self.risk_pct = properites.risk_pct

    def size_signal(self, signal_event: SignalEvent, data_provider: DataProvider) -> float:

        #Check if the risk is positive
        if self.risk_pct <= 0:
            print(f"{Utils.dateprint()} - ERROR (RiskPctPositionSizer): El porcentage de riesgo introducido {self.risk_pct} no es válido.")
            return 0.0
        #Check that the sl != 0
        if signal_event.sl  <= 0.0:
            print(f"{Utils.dateprint()} - ERROR (RiskPctPositionSizer): El valor del SL: {signal_event.sl} no es válido.")
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

        #Get the values needed for the calculus
        equity = account_info.equity
        volume_step = symbol_info.volume_step             #Minimal volume change  
        tick_size = symbol_info.trade_tick_size           #minimal price change
        account_ccy = account_info.currency    
        symbol_profit_ccy = symbol_info.currency_profit
        contract_size = symbol_info.trade_contract_size   # Contract size (example: 1 standard lot)

        # Aux calculations
        tick_value_profit_ccy = contract_size * tick_size            # Quantity gained or lost for each lot & and each tick

        #transform the tick value in the profit ccy of the symbol to the ccy of our account
        tick_value_account_ccy = Utils.conver_currency_amount_to_another_currency(tick_value_profit_ccy,symbol_profit_ccy,account_ccy) 

        # Calculate the size of the position
        try:

            price_distance_in_integer_ticksizes = int(abs(entry_price - signal_event.sl) / tick_size)

            monetary_risk = equity * self.risk_pct

            volume = monetary_risk / (price_distance_in_integer_ticksizes *  tick_value_account_ccy)
            volume = round(volume / volume_step) * volume_step
        except Exception as e:
            print(f"{Utils.dateprint()} - ERROR: Problema al calcular el tamaño de la posición en función del riesgo. Excepción: {e} ")
            return 0.0

        return volume



