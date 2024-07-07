from enum import Enum
from pydantic import BaseModel
import pandas as pd


#Definition of the different type of events

class EventType(str,Enum):
    DATA = "DATA"
    SIGNAL = "SIGNAL"
    SIZING = "SIZING"

class SignalType(str,Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str,Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class BaseEvent(BaseModel):
    event_type:EventType
    
    class Config:
        arbitrary_types_allowed = True



class DataEvent(BaseEvent):
    event_type: EventType = EventType.DATA
    symbol:str
    data: pd.Series



class SignalEvent(BaseEvent):
    event_type:EventType = EventType.SIGNAL
    symbol:str
    signal:SignalType
    target_order: OrderType
    target_price:float
    magic_number:int
    sl:float
    tp: float


class SizingEvent(BaseEvent):
    event_type: EventType = EventType.SIZING
    symbol:str
    signal:SignalType
    target_order: OrderType
    target_price:float
    magic_number:int
    sl:float
    tp: float
    volume: float 