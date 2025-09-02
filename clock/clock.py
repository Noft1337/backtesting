import pandas as pd
from collections.abc import Generator
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Union, ClassVar

from consts import TIME_FMT_DAY
from models import Bar
from utils import parse_interval, td_to_str, discard_datetime_by_interval
from .exceptions import IntervalNotSupported

INTERVALS_ALLOWED = ["1m", "5m", "10m", "30m", "1h", "1d", "7d", "1w"]
INTERVALS_ALLOWED_TD = [parse_interval(i) for i in INTERVALS_ALLOWED]
INTERVALS_REPR = ", ".join(INTERVALS_ALLOWED)

SCHEDULE_TIME_FMT = "%Y-%m-%d %H:%M:%S"


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
        market_start = "pre" if self.extended else "market_open"
        market_end = "post" if self.extended else "market_close"
        sched = Clock.nyse.schedule(
            tz=self.tz,
            start_date=self.start.strftime(TIME_FMT_DAY),
            end_date=self.end.strftime(TIME_FMT_DAY),
            start=market_start,
            end=market_end,
        )
        self.days = sched.index
        self.mkt_opens = sched.market_open
        self.mkt_close = sched.market_close
        self._iterator: Generator[Bar, None, None]

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

    def is_first_day(self, d: pd.Timestamp):
        """Check if the date is the last day in range"""
        return d.date() == self.mkt_opens.iloc[0].date()

    def is_last_day(self, d: pd.Timestamp):
        """Check if the date is the last day in range"""
        return d.date() == self.mkt_close.iloc[-1].date()

    def are_same_week(self, t1: pd.Timestamp, t2: pd.Timestamp):
        """Checks if two date objects fall within the same ISO week."""
        return t1.isocalendar()[:2] == t2.isocalendar()[:2]

    # todo: move all the bar functionality to models.price_bar
    def generate_bars(self) -> Generator[Bar, None, None]:
        """Generates the Bars Generator that copmutes the current bar on runtime"""
        i = -1
        week_start = self.mkt_opens.iloc[0]
        for day_open, day_close in zip(self.mkt_opens, self.mkt_close):
            i += 1

            # Yield bars within the day
            if self.is_intraday:
                bar_open = day_open
                while bar_open < day_close:
                    # Use day_close if the calculated bar_close is higher
                    bar_close = min(bar_open + self._ival_td, day_close)
                    yield Bar(bar_open, bar_close)
                    bar_open += self._ival_td

            # For daily bars, yield a single bar for the whole day
            elif self._ival_td == timedelta(days=1):
                yield Bar(day_open, day_close)

            # For weekly bars, calculate the week start & finish
            elif self._ival_td == timedelta(days=7):
                if self.are_same_week(week_start, day_open):
                    # if range ends, use this as the close of the Bar
                    if self.is_last_day(day_close):
                        yield Bar(week_start, day_close)
                    continue
                # Week close is the last day before entering a different week
                previous_day = self.mkt_close.iloc[i - 1]
                yield Bar(week_start, previous_day)
                week_start = day_open

    def __iter__(self):
        """Iterate over the entire time range using the specified interval"""
        self._iterator = self.generate_bars()
        return self

    # pylint: disable=W0706
    def __next__(self):
        """dummy function that iterates over the iterator that was created by the
        ``__iter__()`` function.

        Important to make this class to be classified as an Iterator object
        """
        try:
            return next(self._iterator)
        except StopIteration:
            raise
