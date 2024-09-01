from queue import Queue
import MetaTrader5 as mt5

from data_provider.data_provider import DataProvider
from events.events import SizingEvent,OrderEvent
from portfolio.portfolio import Portfolio
from .risks_managers.max_leverage_factor_risk_manager import MaxLeverageFactorRiskManager 
from .interfaces.risk_manager_interface import IRiskManager
from .properties.risk_manager_properties import BaseRiskProps, MaxLeverageFactorRiskProps
from utils.utils import Utils

class RiskManager(IRiskManager):

    def __init__(self,events_queue:Queue, data_provider:DataProvider,portfolio:Portfolio, risk_properties:BaseRiskProps) -> None:
        self.events_queue = events_queue
        self.DATA_PROVIDER = data_provider
        self.PORTFOLIO = portfolio

        self.risk_management_method = self._get_risk_management_method(risk_properties)

    def _get_risk_management_method(self,risk_props:BaseRiskProps) -> IRiskManager:

        if isinstance(risk_props,MaxLeverageFactorRiskProps):
            return MaxLeverageFactorRiskManager(risk_props)
        else:
            raise Exception(f"ERROR : Método de Risk Mgmt desconocido {risk_props}")


    def _compute_current_value_of_positions_in_acc_ccy(self) -> float:

        # Get all of the open positions by our strategy
        current_positions = self.PORTFOLIO.get_strategy_open_positions()

        # Calculate the value of the open positions
        total_value = 0.00
        for position in current_positions:
            total_value += self._compute_value_of_position_in_acc_ccy(position.symbol,position.volume,position.type)

        return total_value



    def _compute_value_of_position_in_acc_ccy(self,symbol:str,volume:float,position_type:int) -> float:

        symbol_info = mt5.symbol_info(symbol)

        # Operated Units on the symbol units(base current amount, barrels of oil, gold ounces)
        traded_units = volume * symbol_info.trade_contract_size

        # Units operated in symbol currency
        value_traded_in_profit_ccy = traded_units * self.DATA_PROVIDER.get_latest_tick(symbol)['bid']

        # Value of the operated units in account currency
        value_traded_in_account_ccy = Utils.conver_currency_amount_to_another_currency(value_traded_in_profit_ccy, symbol_info.currency_profit,mt5.account_info().currency)

        if position_type == mt5.ORDER_TYPE_SELL:
            return - value_traded_in_account_ccy
        else:
            return value_traded_in_account_ccy




    
    def _create_and_put_order_event(self,sizing_event:SizingEvent,volume:float) -> None:


        # Create the OrderEvent from the sizing_event and the volume
        order_event = OrderEvent(
                                symbol= sizing_event.symbol,
                                signal= sizing_event.signal,
                                target_order= sizing_event.target_order,
                                target_price= sizing_event.target_price,
                                magic_number= sizing_event.magic_number,
                                sl= sizing_event.sl,
                                tp= sizing_event.tp,
                                volume= volume
                                )

        # add the order event to the events queue
        self.events_queue.put(order_event)
        


    def asses_order(self, sizing_event: SizingEvent) -> None:

        # Gets the value of all of the positions openened in the strategy in the account currency
        current_position_value = self._compute_current_value_of_positions_in_acc_ccy()

        # Obtain the value of the new position, also in the account currency
        position_type = mt5.ORDER_TYPE_BUY if sizing_event.signal == 'BUY' else mt5.ORDER_TYPE_SELL

        new_position_value = self._compute_value_of_position_in_acc_ccy(sizing_event.symbol,sizing_event.volume,position_type)

        # We get the new volume of the operation we want to execute after passing though the risk manager
        new_volume = self.risk_management_method.asses_order(sizing_event,current_position_value,new_position_value)

        # Evaluate the new volume
        if new_volume > 0.0:
            # Add the order event to the queue
            self._create_and_put_order_event(sizing_event,new_volume)


