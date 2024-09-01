from events.events import SizingEvent
from risk_manager.interfaces.risk_manager_interface import IRiskManager
from risk_manager.properties.risk_manager_properties import MaxLeverageFactorRiskProps
import MetaTrader5 as mt5
import sys

from utils.utils import Utils


class MaxLeverageFactorRiskManager(IRiskManager):

    def __init__(self, properties: MaxLeverageFactorRiskProps) -> None:
        self.max_leverage_factor = properties.max_leverage_factor

    def _compute_leverage_factor(self,account_value_acc_ccy:float) -> float:

        account_equity =  mt5.account_info().equity

        if account_equity <= 0:
            return sys.float_info.max 
        else:
            return account_value_acc_ccy / account_equity

    def _check_expected_new_position_is_complaint_with_max_leverage_factor(self,sizing_event:SizingEvent,current_positions_value_acc_ccy:float,
                                                                        new_position_value_acc_ccy:float) -> bool:

        # Calculate the new expected account value if we execute in the new position
        new_account_value = current_positions_value_acc_ccy + new_position_value_acc_ccy

        # calculate the new account value if we execute the new position
        new_leverage_factor = self._compute_leverage_factor(new_account_value)

        # Check if the new leverage factor is grater than our max leverage factor 
        if abs(new_leverage_factor) <= self.max_leverage_factor:
            return True
        else:
            print(f"{Utils.dateprint()} - RISK MGMT: La posición objetivo {sizing_event.signal} {sizing_event.volume} implica un Leverage Factor de {abs(new_leverage_factor):.2f}, que supera el max. de {self.max_leverage_factor}")
            return False


    def asses_order(self, sizing_event: SizingEvent,current_positions_value_acc_ccy:float,new_position_value_acc_ccy:float) -> float:

        # This method will make the function of a "Night club doorman" -> let an operation pass or not

        if self._check_expected_new_position_is_complaint_with_max_leverage_factor(sizing_event,current_positions_value_acc_ccy,new_position_value_acc_ccy) :
            return sizing_event.volume
        else:
            return 0.00
