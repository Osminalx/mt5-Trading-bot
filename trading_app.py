from platform_connector.platform_connector import PlatformConnector 
from data_provider.data_provider import DataProvider
from trading_director.trading_director import TradingDirector
from signal_generator.signal_generator import SignalGenerator
from signal_generator.properties.signal_generator_properties import MACrossoverProps
from position_sizer.position_sizer import PositionSizer
from position_sizer.properties.position_sizer_properties import MinSizingProps, FixedSizingProps
from portfolio.portfolio import Portfolio
from risk_manager.risk_manager import RiskManager
from risk_manager.properties.risk_manager_properties import MaxLeverageFactorRiskProps
from order_executor.order_executor import OrderExecutor
from notifications.notifications import NotificationService,TelegramNotificationProperties

import os
from dotenv import load_dotenv,find_dotenv

from queue import Queue

if __name__ == "__main__":

    # Defition of necessary variables for the strategy
    symbols = ["EURUSD","USDJPY"]
    timeframe = '5min'
    magic_number = 12345
    slow_ma_period = 10
    fast_ma_period = 5

    #Creation of the principal evetn queue
    events_queue = Queue()

    # .env search and values charge
    load_dotenv(find_dotenv())

    #Creation of the principal modules of the framework
    CONNECT = PlatformConnector(symbol_list= symbols)

    DATA_PROVIDER =DataProvider(events_queue=events_queue,
                                symbol_list=symbols,
                                timeframe=timeframe)


    PORTFOLIO = Portfolio(magic_number= magic_number)

    ORDER_EXECUTOR = OrderExecutor( events_queue=events_queue,
                                    portfolio=PORTFOLIO)


    SIGNAL_GENERATOR = SignalGenerator(events_queue=events_queue,
                                        data_provider = DATA_PROVIDER,
                                        portfolio = PORTFOLIO,
                                        order_executor = ORDER_EXECUTOR,
                                        signal_properties = MACrossoverProps(timeframe=timeframe,fast_period=fast_ma_period,slow_period=slow_ma_period))

    POSITION_SIZER =PositionSizer(events_queue=events_queue,
                                    data_provider= DATA_PROVIDER,
                                    sizing_properties= FixedSizingProps(volume=0.02))


    RISK_MANAGER = RiskManager( events_queue= events_queue,
                                data_provider= DATA_PROVIDER,
                                portfolio= PORTFOLIO,
                                risk_properties= MaxLeverageFactorRiskProps(max_leverage_factor=5.0)
    )

    NOTIFICATIONS = NotificationService(
        properties= TelegramNotificationProperties(
            token=os.getenv("BOT_TOKEN"),
            chat_id=os.getenv("GROUP_CHAT_ID"),
        )
    )


    #Trading director creation and main method execute
    TRADING_DIRECTOR = TradingDirector(events_queue=events_queue,
                                        data_provider=DATA_PROVIDER,
                                        signal_generator=SIGNAL_GENERATOR,
                                        position_sizer= POSITION_SIZER,
                                        risk_manager= RISK_MANAGER,
                                        order_executor=ORDER_EXECUTOR,
                                        notification_service=NOTIFICATIONS
                                        )
    TRADING_DIRECTOR.execute()




