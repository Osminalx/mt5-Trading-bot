from platform_connector.platform_connector import PlatformConnector 
from data_provider.data_provider import DataProvider
from trading_director.trading_director import TradingDirector
from signal_generator.signals.signal_ma_crossover import SignalMACrossover

from queue import Queue

if __name__ == "__main__":

    # Defition of necessary variables for the strategy
    symbols = ["EURUSD","USDJPY"]
    timeframe = '1min'
    slow_ma_period = 50
    fast_ma_period = 25

    #Creation of the principal evetn queue
    events_queue = Queue()

    #Creation of the principal modules of the framework
    CONNECT = PlatformConnector(symbol_list= symbols)

    DATA_PROVIDER =DataProvider(events_queue=events_queue,
                                symbol_list=symbols,
                                timeframe=timeframe)

    SIGNAL_GENERATOR = SignalMACrossover(events_queue=events_queue,
                                            data_provider=DATA_PROVIDER,
                                            timeframe= timeframe,
                                            fast_period= fast_ma_period,
                                            slow_period= slow_ma_period)


    #Trading director creation and main method execute
    TRADING_DIRECTOR = TradingDirector(events_queue=events_queue,
                                        data_provider=DATA_PROVIDER,
                                        signal_generator=SIGNAL_GENERATOR)
    TRADING_DIRECTOR.execute()




