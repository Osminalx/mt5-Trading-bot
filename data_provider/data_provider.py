import MetaTrader5 as mt5
import pandas as pd
from typing import Dict
from datetime import datetime
from events.events import DataEvent
from queue import Queue 


class DataProvider():
    
    def __init__(self,events_queue:Queue,symbol_list:list,timeframe:str) -> None:
        
        self.events_queue = events_queue

        self.symbols:list = symbol_list
        self.timeframe:str = timeframe

        #we create a dict to save the datetime of the last bar we have seen for each symbol
        self.last_bar_datetime:Dict[str,datetime] = {symbol: datetime.min for symbol in self.symbols}

    def _map_timeframes(self,timeframe:str)-> int:
        timeframe_mapping = {
            '1min': mt5.TIMEFRAME_M1,
            '2min': mt5.TIMEFRAME_M2,                        
            '3min': mt5.TIMEFRAME_M3,                        
            '4min': mt5.TIMEFRAME_M4,                        
            '5min': mt5.TIMEFRAME_M5,                        
            '6min': mt5.TIMEFRAME_M6,                        
            '10min': mt5.TIMEFRAME_M10,                       
            '12min': mt5.TIMEFRAME_M12,
            '15min': mt5.TIMEFRAME_M15,
            '20min': mt5.TIMEFRAME_M20,                       
            '30min': mt5.TIMEFRAME_M30,                       
            '1h': mt5.TIMEFRAME_H1,                          
            '2h': mt5.TIMEFRAME_H2,                          
            '3h': mt5.TIMEFRAME_H3,                          
            '4h': mt5.TIMEFRAME_H4,                          
            '6h': mt5.TIMEFRAME_H6,                          
            '8h': mt5.TIMEFRAME_H8,                          
            '12h': mt5.TIMEFRAME_H12,
            '1d': mt5.TIMEFRAME_D1,                       
            '1w': mt5.TIMEFRAME_W1,                       
            '1M': mt5.TIMEFRAME_MN1,                       
        }

        try:
            return timeframe_mapping[timeframe]
        except:
            print(f"Timeframe {timeframe} no es válido. ")


    def get_latest_closed_bar(self, symbol:str,timeframe:str)-> pd.Series:
        #Define the right parameters
        tf = self._map_timeframes(timeframe) 
        from_position = 1
        num_bars = 1
        
        #Get the data from the last bar
        try:
            bars_np_array = mt5.copy_rates_from_pos(symbol,tf,from_position,num_bars)
            if bars_np_array is None:
                print(f"El símbolo {symbol} no existe o no se han podido recuperar sus datos")
                #Return an empty Series
                return pd.Series()

            bars = pd.DataFrame(bars_np_array)
            #Convert the 'time' column into Datetime and we convert it into the indices
            bars['time'] = pd.to_datetime(bars['time'], unit= 's')
            bars.set_index('time', inplace= True)

            #Change of the column names and reorganize them  
            bars.rename(columns={'tick_volume':'tickvol','real_volume':'vol'}, inplace=True)
            bars = bars[['open','high','low','close','tickvol','vol','spread']]
            

        except Exception as e:
            print(f"No se han podido capturar los datos de la última vela de {symbol} {timeframe}. MT5 Error: {mt5.last_error()}, exception: {e}")

        else:
            #If the DF is empty we return an empty Series
            if bars.empty:
                return pd.Series()
            else:
                return bars.iloc[-1]
    
    def get_latests_closed_bars(self, symbol:str,timeframe:str, num_bars: int = 1)->pd.DataFrame:
        #Define the right parameters
        tf = self._map_timeframes(timeframe) 
        from_position = 0
        bars_count = num_bars if num_bars > 0 else 1


        #Get the data from the latests bars
        try:
            bars_np_array = mt5.copy_rates_from_pos(symbol,tf,from_position,bars_count)
            if bars_np_array is None:
                print(f"El símbolo {symbol} no existe o no se han podido recuperar sus datos")
                #Return an empty DF
                return pd.DataFrame()

            bars = pd.DataFrame(bars_np_array)
            #Convert the 'time' column into Datetime and we convert it into the indices
            bars['time'] = pd.to_datetime(bars['time'], unit= 's')
            bars.set_index('time', inplace= True)

            #Change of the column names and reorganize them  
            bars.rename(columns={'tick_volume':'tickvol','real_volume':'vol'}, inplace=True)
            bars = bars[['open','high','low','close','tickvol','vol','spread']]
        
        except Exception as e:
            print(f"No se han podido capturar los datos de la última vela de {symbol} {timeframe}. MT5 Error: {mt5.last_error()}, exception: {e}")
        
        else:
            #If everything is OK, we return the DF with all of the bars
            return bars

    def get_latest_tick(self,symbol:str)-> dict:
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                print(f"No se ha podido recuperar el último tick de {symbol}. MT5 Error: {mt5.last_error()} exception: {e}")
                return {}

        except Exception as e:
            print(f"Algo no ha ido bien al recuperar el último tick de {symbol}.  MT5 Error: {mt5.last_error()} exception: {e}")

        else:
            return tick._as_dict()
    
    def check_for_new_data(self)->None:
        # 1) check if there is new data
        for symbol in self.symbols:
            #Access to its latests aviable data
            latest_bar = self.get_latest_closed_bar(symbol,self.timeframe)

            if latest_bar is None:
                continue

            #2)if new data, create new DataEvent and add it to the event queue
            if not latest_bar.empty and latest_bar.name > self.last_bar_datetime[symbol]:
                #update the last bar 
                self.last_bar_datetime[symbol] = latest_bar.name

                #Creation of DataEvent 
                data_event = DataEvent(symbol=symbol, data= latest_bar)

                #add DataEvent to the Event queue
                self.events_queue.put(data_event)




