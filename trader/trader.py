from datetime import datetime, timedelta
from pydantic import BaseModel
from dataclasses import dataclass
from methods import Method


@dataclass
class Trader(BaseModel):
    ticker: str
    start: datetime
    end: datetime
    interval: timedelta

    def __post_init__(self):
        pass

    def register(self, methods: Method):
        pass
