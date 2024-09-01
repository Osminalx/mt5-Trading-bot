from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import MetaTrader5 as mt5


# Create an static method to convert from one currency to another

class Utils():
    def __init__(self) -> None:
        pass

    @staticmethod
    def conver_currency_amount_to_another_currency(amount:float, from_ccy: str,to_ccy:str,) -> float:

        all_fx_symbol = ("AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY", "CHFJPY", "EURAUD", "EURCAD",
                    "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD",
                    "GBPUSD", "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "USDSEK", "USDNOK")
        
        # Capitalize currency
        from_ccy = from_ccy.upper()
        to_ccy = to_ccy.upper()
        if from_ccy == to_ccy:
            return amount

        #Search the symbol that relates our source currency to the destination currency (List comprehension)
        fx_symbol = [symbol for symbol in all_fx_symbol if from_ccy in symbol and to_ccy in symbol][0]
        fx_symbol_base = fx_symbol[:3]

        # Get the last data aviable from the fx_symbol
        try:
            tick = mt5.symbol_info_tick(fx_symbol)
            if tick is None:
                raise Exception(f"El símbolo {fx_symbol} no está disponible en la plataforma MT5. por favor, revísa los símbolos disponibles de tu broker")

        except Exception as e:
            print(f"No se pudo recuperar el último tick del símbolo {fx_symbol}. MT5 error {mt5.last_error()}, Exception {e}")
            return 0.0

        else:
            # Get the last aviable price of the symbol
            last_price =  tick.bid

            # Transform the source currency to the destinationi currency
            converted_amount = amount / last_price if fx_symbol_base == to_ccy else amount * last_price  
            return converted_amount

    @staticmethod
    def dateprint() -> str:
        # Asia/Nicosia time zone lets the framework operate for all of the days of the week, since almost all brokers use this timezone
        return datetime.now(ZoneInfo("Asia/Nicosia")).strftime("%d/%m/%Y  %H:%M:%S.%f")[:-3]