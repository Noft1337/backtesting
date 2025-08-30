import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Union, ClassVar

from utils import parse_interval, td_to_str, discard_datetime_by_interval
from .exceptions import IntervalNotSupported

INTERVALS_ALLOWED = ["1m", "5m", "10m", "30m", "1h", "1d", "7d", "30d", "1w", "4w"]
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
            Allowed intervals: 1m, 5m, 10m, 30m, 1h, 1d, 7d, 30d, 1w, 4w
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
        self._sched_i = 0
        self._sched_len = len(self.sched)
        self._sched_calc = True
        self._today_open: datetime
        self._today_close: datetime

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

    @property
    def today_open(self):
        if self._sched_calc:
            loc = self.sched.columns.get_loc(self._market_start)
            self._today_open = self.sched.iat[self._sched_i, loc].to_pydatetime()
        return self._today_open

    @property
    def today_close(self):
        if self._sched_calc:
            loc = self.sched.columns.get_loc(self._market_end)
            self._today_close = self.sched.iat[self._sched_i, loc].to_pydatetime()
        return self._today_close

    @property
    def today(self) -> datetime:
        """To be used only when not in intraday mode"""
        return self.sched.index[self._sched_i].to_pydatetime()

    def __iter__(self):
        return self

    def __next__(self) -> datetime:
        if self._sched_i == self._sched_len:
            raise StopIteration

        # If not intraday, open & close times shouldn't be a factor
        if not self.is_intraday:
            try:
                self.time = self.today
                return self.time
            finally:
                self._sched_i += 1

        # On intraday, we are iterating over the times within the day using
        # ``self.interval``. this requires to factor in the open & close times and
        # change them once we finish iterating over the current trading day.

        # NOTE: this is necessary because panda_market_calendars doesn't support
        # intraday frequencies
        if self._sched_calc:
            self.time = self.today_open

        try:
            return self.time
        finally:
            # On 1h chart, the last bar is only 30 mins
            if self._ival_str == "1h" and self.time == self.today_close - MINS_30:
                self.time += timedelta(minutes=30)
            else:
                self.time += self._ival_td
                # Reached close time, recalculate open & close time
                if self.time > self.today_close:
                    self._sched_calc = True
                    self._sched_i += 1
                else:
                    self._sched_calc = False
