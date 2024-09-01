from events.events import DataEvent, SignalEvent
from data_provider.data_provider import DataProvider
from order_executor.order_executor import OrderExecutor
from portfolio.portfolio import Portfolio
from signal_generator.properties.signal_generator_properties import MACrossoverProps
from ..interfaces.signal_generator_interface import ISignalGenerator



class SignalMACrossover(ISignalGenerator):

    def __init__(self, properties: MACrossoverProps ) -> None:

        self.timeframe = properties.timeframe
        self.fast_period = properties.fast_period if properties.fast_period > 1 else 2
        self.slow_period = properties.slow_period if properties.slow_period > 2 else 3

        if self.fast_period>= self.slow_period:
            raise Exception(f"ERROR: El périodo rápido ({self.fast_ma}) es mayor al périodo lento ({self.slow_period}) para el cálculo de las medias móviles")


    def generate_signals(self, data_event: DataEvent,data_provider: DataProvider, portfolio:Portfolio, order_executor:OrderExecutor) -> SignalEvent:

        #Take the symbol of the event
        symbol = data_event.symbol


        #Get the needed data to calculate the mobile averages
        bars = data_provider.get_latests_closed_bars(symbol= symbol,timeframe= self.timeframe,num_bars= self.slow_period)

        # Get the positions opened in the strategy in the symbol we have the data provider
        open_positions = portfolio.get_number_of_strategy_open_positions_by_symbol(symbol)

        #Calculate the value of the indicators
        fast_ma = bars['close'][-self.fast_period:].mean()
        slow_ma = bars['close'].mean()

        #Detect a buy signal
        if open_positions['LONG'] == 0 and fast_ma > slow_ma:
            if open_positions['SHORT'] > 0:
                # We have buy signal, but we have a sell position. We should close it BEFORE opening the buy
                order_executor.close_strategy_short_positions_by_symbol(symbol)

            signal = "BUY"

        #Sell signal
        elif open_positions['SHORT'] == 0 and  slow_ma > fast_ma:
            if open_positions['LONG'] > 0:

                order_executor.close_strategy_long_positions_by_symbol(symbol)

            signal = "SELL"

        else:
            signal = ""

        #If we have a signal, we generate a Signal Event and append it to the Events queue
        if signal != "":
            
            signal_event = SignalEvent(symbol= symbol, 
                                        signal= signal,
                                        target_order= "MARKET",
                                        target_price= 0.0,
                                        magic_number= portfolio.magic,
                                        sl= 0.0,
                                        tp= 0.0)

            return signal_event




