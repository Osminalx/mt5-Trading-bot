import MetaTrader5 as mt5
import os
from dotenv import load_dotenv, find_dotenv

from utils.utils import Utils


class PlatformConnector():
    def __init__(self,symbol_list:list) -> None:
        # we search for the .env file and we load its values
        load_dotenv(find_dotenv())

        # Initialization of the platform 
        self._initialize_platform()

        #Account type comprobation
        self._live_account_warning()

        #Print the account info
        self._print_account_info()

        #Algorithmic trading comprobation
        self._check_algo_trading_enabled()

        #Add the symbols to the MarketWatch
        self._add_symbols_to_marketwatch(symbol_list)




    
    def _initialize_platform(self) -> None:
        """
        Initializes of the MT5 platform.

        Raises:
            Exception: If there is any Error while initializing the Platform

        Returns:
            None
        """
        if mt5.initialize(
            path= os.getenv("MT5_PATH"),
            login = int(os.getenv("MT5_LOGIN")),
            password = os.getenv("MT5_PASSWORD"),
            server = os.getenv("MT5_SERVER"),
            timeout = int(os.getenv("MT5_TIMEOUT")),
            portable = eval(os.getenv("MT5_PORTABLE"))
        ):
            print("La plataforma MT5 se a lanzado con exito!!!")
        else:
            raise Exception(f"Ha occurido un error al inicializar la plataforma MT5: {mt5.last_error()}")
    
    def _live_account_warning(self) -> None:
        account_info = mt5.account_info()

        # Check the type of account that was launched 
        if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("Tipo de cuenta: DEMO")
        elif account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:
            if not input("ALERTA! Cuenta de tipo REAL detectada. Capital en riesgo. ¿Deseas continuar? (y/n): ").lower() == "y":
                mt5.shutdown()
                raise Exception("Usuario ha decidido DETENER el programa.")
        else:
            print("Tipo de cuenta: CONCURSO")
        
    def _check_algo_trading_enabled(self)-> None:
        #Check if the algorithmic trading is activated
        if not mt5.terminal_info().trade_allowed:
            raise Exception("El trading algoritmico esta desactivado, por favor activalo MANUALMENTE")
        
    def _add_symbols_to_marketwatch(self,symbols: list)->None:
        #1) Check if the symbol is visible on the MarketWatch
        #2) if it isn't, we will add it
        for symbol in symbols:
            if mt5.symbol_info(symbol) is None:
                print(f"{Utils.dateprint()} - No se ha podido agregar el símbolo {symbol} al MarketWatch: {mt5.last_error()}")
                continue

            if not mt5.symbol_info(symbol).visible:
                if not mt5.symbol_select(symbol, True):
                    print(f"{Utils.dateprint()} - No se ha podido agregar el símbolo {symbol} al MarketWatch: {mt5.last_error()}")
                else:
                    print(f"{Utils.dateprint()} - El símbolo {symbol} se agregó con éxito!")
            else:
                print(f"{Utils.dateprint()} - El símbolo {symbol} ya estaba en el MarketWatch")
    def _print_account_info(self)->None:
        #Get an object of type "AccountInfo"
        account_info = mt5.account_info()._asdict()

        print(f"{Utils.dateprint()} - +-------- Información de la cuenta --------")
        print(f"{Utils.dateprint()} - | - ID de cuenta: {account_info['login']}")
        print(f"{Utils.dateprint()} - | - Nombre del Trader: {account_info['name']}")
        print(f"{Utils.dateprint()} - | - Broker: {account_info['company']}")
        print(f"{Utils.dateprint()} - | - Servidor: {account_info['server']}")
        print(f"{Utils.dateprint()} - | - Apalancamiento: {account_info['leverage']}")
        print(f"{Utils.dateprint()} - | - Divisa de la cuenta: {account_info['currency']}")
        print(f"{Utils.dateprint()} - | - Balance de la cuenta: {account_info['balance']}")
        print(f"{Utils.dateprint()} - +------------------------------------------")
