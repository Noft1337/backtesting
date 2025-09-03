import pandas as pd
from collections.abc import Generator
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Union, ClassVar, cast

from ..config import TIME_FMT_DAY
from . import Bar
from ..utils import parse_interval, td_to_str, discard_datetime_by_interval
from ..exceptions import IntervalNotSupported

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
        self.sched = Clock.nyse.schedule(
            tz=self.tz,
            start_date=self.start.strftime(TIME_FMT_DAY),
            end_date=self.end.strftime(TIME_FMT_DAY),
            start=market_start,
            end=market_end,
        )
        self.days = self.sched.index
        self.mkt_opens = self.sched.market_open
        self.mkt_close = self.sched.market_close
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

    def _generate_intraday_bars(self) -> Generator[Bar, None, None]:
        """Generates bars for intraday intervals."""
        for day_open, day_close in zip(self.mkt_opens, self.mkt_close):
            bar_open = day_open
            while bar_open < day_close:
                bar_close = min(bar_open + self._ival_td, day_close)
                yield Bar(bar_open, bar_close)
                bar_open += self._ival_td

    def _generate_daily_bars(self) -> Generator[Bar, None, None]:
        """Generates bars for daily intervals."""
        for day_open, day_close in zip(self.mkt_opens, self.mkt_close):
            yield Bar(day_open, day_close)

    def _generate_weekly_bars(self) -> Generator[Bar, None, None]:
        """Generates bars for weekly intervals using pandas."""
        idx = cast(pd.DatetimeIndex, self.sched.index)
        weekly_groups = self.sched.groupby(
            [idx.isocalendar().year, idx.isocalendar().week]
        )

        for _, week_df in weekly_groups:
            week_open = week_df["market_open"].iloc[0]
            week_close = week_df["market_close"].iloc[-1]
            yield Bar(week_open, week_close)

    def generate_bars(self) -> Generator[Bar, None, None]:
        """
        Dispatcher method: calls the correct generator based on the interval.
        XXX: In the future, maybe move this to models.price_bar / utils ?
        """
        if self.is_intraday:
            yield from self._generate_intraday_bars()
        elif self._ival_td == timedelta(days=1):
            yield from self._generate_daily_bars()
        elif self._ival_td >= timedelta(days=7):  # Or weeks=1
            yield from self._generate_weekly_bars()

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
