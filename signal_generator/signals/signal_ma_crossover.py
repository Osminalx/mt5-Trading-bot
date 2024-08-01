from events.events import DataEvent, SignalEvent
from data_provider.data_provider import DataProvider
from portfolio.portfolio import Portfolio
from ..interfaces.signal_generator_interface import ISignalGenerator

import pandas as pd
from queue import Queue



class SignalMACrossover(ISignalGenerator):

    def __init__(self,events_queue:Queue,data_provider:DataProvider,portfolio:Portfolio,fast_period:int,slow_period:int,timeframe:str) -> None:

        self.events_queue = events_queue

        self.DATA_PROVIDER = data_provider
        self.PORTFOLIO =  portfolio

        self.timeframe = timeframe
        self.fast_period = fast_period if fast_period > 1 else 2
        self.slow_period = slow_period if slow_period > 2 else 3

        if self.fast_period>= slow_period:
            raise Exception(f"ERROR: El périodo rápido ({self.fast_ma}) es mayor al périodo lento ({self.slow_period}) para el cálculo de las medias móviles")


    def _create_and_put_signal_event(self,symbol:str,signal:str,target_order:str,target_price:float,magic_number:int,sl:float,tp:float) -> None:

        #Create a signal Event
        signal_event = SignalEvent(symbol= symbol, 
                                    signal= signal,
                                    target_order= target_order,
                                    target_price= target_price,
                                    magic_number= magic_number,
                                    sl= sl,
                                    tp= tp)

        #Add the SignalEvent to the Events queue
        self.events_queue.put(signal_event)
    

    def generate_signals(self, data_event: DataEvent) -> None:

        #Take the symbol of the event
        symbol = data_event.symbol


        #Get the needed data to calculate the mobile averages
        bars = self.DATA_PROVIDER.get_latests_closed_bars(symbol= symbol,timeframe= self.timeframe,num_bars= self.slow_period)

        # Get the positions opened in the strategy in the symbol we have the data provider
        open_positions =self.PORTFOLIO.get_number_of_strategy_open_positions_by_symbol(symbol)

        #Calculate the value of the indicators
        fast_ma = bars['close'][-self.fast_period:].mean()
        slow_ma = bars['close'].mean()

        #Detect a buy signal
        if open_positions['LONG'] == 0 and fast_ma > slow_ma:
            signal = "BUY"

        #Sell signal
        elif open_positions['SHORT'] == 0 and  slow_ma > fast_ma:
            signal = "SELL"

        else:
            signal = ""

        #If we have a signal, we generate a Signal Event and append it to the Events queue
        if signal != "":
            self._create_and_put_signal_event(  symbol= symbol,
                                                signal= signal,
                                                target_order= "MARKET",
                                                target_price= 0.0,
                                                magic_number= self.PORTFOLIO.magic,
                                                sl= 0.0,
                                                tp= 0.0
                                                )




