from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Union

from utils import parse_interval, td_to_str, discard_datetime_by_interval
from .exceptions import IntervalNotSupported

INTERVALS_ALLOWED = ["1m", "5m", "10m", "30m", "1h", "1d", "7d", "30d", "1w", "4w"]
INTERVALS_ALLOWED_TD = [parse_interval(i) for i in INTERVALS_ALLOWED]
INTERVALS_REPR = ", ".join(INTERVALS_ALLOWED)


@dataclass
class Clock:
    """This class mimics a global clock for the backtesting environment. Each time a
    position will be initiated and/or a security's data will be checked, the time that
    will be used will be provided by this class

    To use this class, it allows to iterate over it. When iterated, the ``start`` time
    will be updated by ``interval`` for each iteration, storing the current time in
    ``self.time``

    Args:
        start(datetime): the "epoch" of the clock, since when this clock provides time
            data
        ival(Union[str, timedelta]): the time interval that the clock is able to support
            as of now, only 1 interval is allowed.
            Allowed intervals: 1m, 5m, 10m, 30m, 1h, 1d, 7d, 30d, 1w, 4w
    """

    start: datetime
    end: datetime = datetime.now()
    interval: Union[str, timedelta] = "1d"

    time: datetime = field(init=False)
    _ival_str: str = field(default_factory=str, init=False)
    _ival_td: timedelta = field(default_factory=timedelta, init=False)

    def __post_init__(self):
        self._parse_interval()
        self.time = self.start
        # Discard useless fields to be able to stop iterating
        self.end = discard_datetime_by_interval(self.end, self._ival_td)

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

    def __iter__(self):
        return self

    def __next__(self) -> datetime:
        if self.time > self.end:
            raise StopIteration
        try:
            return self.time
        finally:
            self.time += self._ival_td
