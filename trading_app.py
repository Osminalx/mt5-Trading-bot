from platform_connector.platform_connector import PlatformConnector 
from data_provider.data_provider import DataProvider
from trading_director.trading_director import TradingDirector
from signal_generator.signals.signal_ma_crossover import SignalMACrossover
from position_sizer.position_sizer import PositionSizer
from position_sizer.properties.position_sizer_properties import MinSizingProps, FixedSizingProps
from portfolio.portfolio import Portfolio
from risk_manager.risk_manager import RiskManager
from risk_manager.properties.risk_manager_properties import MaxLeverageFactorRiskProps

from queue import Queue

if __name__ == "__main__":

    # Defition of necessary variables for the strategy
    symbols = ["EURUSD","USDJPY"]
    timeframe = '1min'
    magic_number = 12345
    slow_ma_period = 50
    fast_ma_period = 25

    #Creation of the principal evetn queue
    events_queue = Queue()

    #Creation of the principal modules of the framework
    CONNECT = PlatformConnector(symbol_list= symbols)

    DATA_PROVIDER =DataProvider(events_queue=events_queue,
                                symbol_list=symbols,
                                timeframe=timeframe)


    PORTFOLIO = Portfolio(magic_number= magic_number)

    SIGNAL_GENERATOR = SignalMACrossover(events_queue=events_queue,
                                            data_provider=DATA_PROVIDER,
                                            portfolio= PORTFOLIO,
                                            timeframe= timeframe,
                                            fast_period= fast_ma_period,
                                            slow_period= slow_ma_period)

    POSITION_SIZER =PositionSizer(events_queue=events_queue,
                                    data_provider= DATA_PROVIDER,
                                    sizing_properties= FixedSizingProps(volume=0.02))


    RISK_MANAGER = RiskManager( events_queue= events_queue,
                                data_provider= DATA_PROVIDER,
                                portfolio= PORTFOLIO,
                                risk_properties= MaxLeverageFactorRiskProps(max_leverage_factor=5.0)
    )

    #Trading director creation and main method execute
    TRADING_DIRECTOR = TradingDirector(events_queue=events_queue,
                                        data_provider=DATA_PROVIDER,
                                        signal_generator=SIGNAL_GENERATOR,
                                        position_sizer= POSITION_SIZER,
                                        risk_manager= RISK_MANAGER,
                                        )
    TRADING_DIRECTOR.execute()




