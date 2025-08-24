from typing import Optional
from pandas import DataFrame
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class PriceAction:
    data: DataFrame
    start: datetime
    end: datetime
    chunk: Optional[timedelta]
