from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Union

from utils import parse_interval, td_to_str
from .exceptions import IntervalNotSupported

INTERVALS_ALLOWED = ["1m", "5m", "10m", "30m", "1h", "1d", "7d", "30d", "1w", "4w"]
INTERVALS_ALLOWED_TD = [parse_interval(i) for i in INTERVALS_ALLOWED]
INTERVALS_REPR = ", ".join(INTERVALS_ALLOWED)


@dataclass
class Clock:
    interval: Union[str, timedelta]
    start: datetime

    _ival_str: str = field(default_factory=str, init=False)
    _ival_td: timedelta = field(default_factory=timedelta, init=False)

    def __post_init__(self):
        self._parse_interval()

    def _parse_interval(self):
        if isinstance(self.interval, str):
            self._ival_str = self.interval
            self._ival_td = parse_interval(self.interval)
        else:
            self._ival_td = self.interval
            self._ival_str = td_to_str(self.interval)
        if self._ival_td not in INTERVALS_ALLOWED_TD:
            raise IntervalNotSupported(
                f"Interval: {self._ival_str} not supported, "
                f"supported intervals are: {INTERVALS_REPR}"
            )
