import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Union, ClassVar

from models import Bar
from utils import parse_interval, td_to_str, discard_datetime_by_interval
from .exceptions import IntervalNotSupported

INTERVALS_ALLOWED = ["1m", "5m", "10m", "30m", "1h", "1d", "7d", "1w"]
INTERVALS_ALLOWED_TD = [parse_interval(i) for i in INTERVALS_ALLOWED]
INTERVALS_REPR = ", ".join(INTERVALS_ALLOWED)

MCAL_TIME_FMT = "%Y-%m-%d"
SCHEDULE_TIME_FMT = "%Y-%m-%d %H:%M:%S"
MINS_30 = timedelta(minutes=30)


# pylint: disable=R0902
@dataclass
class Clock:
    """This class mimics a global clock for the backtesting environment. Each time a
    position will be initiated and/or a security's data will be checked, the time that
    will be used will be provided by this class

    To use this class, it allows to iterate over it. When iterated, the ``start`` time
    will be updated by ``interval`` for each iteration, storing the current time in
    ``self.time``

    This class uses the US Equities calendar on NY timezone. This can not be modified

    Args:
        start(datetime): the "epoch" of the clock, since when this clock provides time
            data
        end(datetime): The end of the date range. Default is now
        interval(Union[str, timedelta]): the time interval that the clock is able to
            support. as of now, only 1 interval is allowed.
            Allowed intervals: 1m, 5m, 10m, 30m, 1h, 1d, 7d, 1w
        extended(bool): enable pre & post market times. Default is False
    """

    start: datetime
    end: datetime = datetime.now()
    interval: Union[str, timedelta] = "1d"
    extended: bool = False

    time: datetime = field(init=False)
    _ival_str: str = field(default_factory=str, init=False)
    _ival_td: timedelta = field(default_factory=timedelta, init=False)

    # Calendar Class attributes
    tz: ClassVar[str] = "America/New_York"
    calendar: ClassVar[str] = "NYSE"
    nyse: ClassVar[mcal.MarketCalendar] = mcal.get_calendar(calendar)

    def __post_init__(self):
        self._parse_interval()
        self.time = self.start
        # Discard useless fields to be able to stop iterating
        self.end = discard_datetime_by_interval(self.end, self._ival_td)
        self.is_intraday = self._ival_td < timedelta(days=1)

        # Set up a schedule of the trading sessions
        self._market_start = "pre" if self.extended else "market_open"
        self._market_end = "post" if self.extended else "market_close"
        self.sched = Clock.nyse.schedule(
            tz=self.tz,
            start_date=self.start.strftime(MCAL_TIME_FMT),
            end_date=self.end.strftime(MCAL_TIME_FMT),
            start=self._market_start,
            end=self._market_end,
        )
        if self._ival_td < timedelta(days=1):
            self.range = mcal.date_range(self.sched, frequency=self._ival_str)
        else:
            self.range = mcal.date_range(self.sched, frequency="1d")
        self._range_i = 0
        self._range_len = len(self.range)
        self._sched_calc = True

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

    def _cmp_bars(self, cell: str, ts: Union[pd.Timestamp, datetime]) -> bool:
        """Compares if a timestamp matches against a specific cell for the same day"""
        day = ts.date().strftime(MCAL_TIME_FMT)  # format it to str repr
        v = self.sched.at[day, cell]

        return ts == v

    def _is_first_bar_of_day(self, ts: Union[pd.Timestamp, datetime]) -> bool:
        return self._cmp_bars(self._market_start, ts)

    def _is_last_bar_of_day(self, ts: Union[pd.Timestamp, datetime]) -> bool:
        return self._cmp_bars(self._market_end, ts)

    def __iter__(self):
        return self

    def __next__(self) -> Bar:
        """Iterates over the date range that has been generated upon instance
        initialization

        Note:
            This returns the CLOSE time of the bar!!

        todo: return Tuple of open & close of each bar. probably will be needed
        """
        if self._range_i == self._range_len:
            raise StopIteration

        try:
            # the timestamps are always the CLOSE timestamps, we need to calculate the
            # OPEN timestamp independently
            close_ts = self.range[self._range_i]
            bar_close = close_ts.to_pydatetime()
            if self._is_first_bar_of_day(bar_close - self._ival_td):
                # If it's the first bar of the day, we can't use the previous timestamp
                # as the bar's OPEN time
                bar_open = bar_close - self._ival_td
            else:
                # If it isn't the first bar, use the last bar's CLOSE Timestamp as this
                # one's OPEN Timestamp
                open_ts = self.range[self._range_i - 1]
                bar_open = open_ts.to_pydatetime()

            return Bar(bar_open, bar_close)
        finally:
            self._range_i += 1
