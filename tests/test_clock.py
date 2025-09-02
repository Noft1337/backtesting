# pylint: disable=C0103,W0614,W0401
import pytest
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

from tests import *
from tests.utils import get_datetime
from consts import TIME_FMT_DAY
from clock import Clock
from models import Bar
from clock.exceptions import IntervalNotSupported


_start = datetime(year=2001, month=11, day=1)
tcs_clock_interval = TestCases(
    "test_clock_interval",
    [
        TestCase(interval="1m", start=_start),
        TestCase(interval=timedelta(minutes=1), start=_start),
        TestCase(interval="5m", start=_start),
        TestCase(interval=timedelta(minutes=5), start=_start),
        TestCase(interval="10m", start=_start),
        TestCase(interval=timedelta(minutes=10), start=_start),
        TestCase(interval="1h", start=_start),
        TestCase(interval=timedelta(hours=1), start=_start),
        TestCase(interval="1d", start=_start),
        TestCase(interval=timedelta(days=1), start=_start),
        TestCase(interval="7d", start=_start),
        TestCase(interval=timedelta(days=7), start=_start),
        TestCase(interval="1w", start=_start),
        # Exception cases
        TestCase(interval="invalid", start=_start, raises=ValueError),
        TestCase(interval="3d", start=_start, raises=IntervalNotSupported),
        TestCase(interval=timedelta(days=4), start=_start, raises=IntervalNotSupported),
    ],
)


@pytest.mark.parametrize("tcs", tcs_clock_interval, ids=tids(tcs_clock_interval))
def test_clock_interval(tcs: TestCasesIter):
    """Test that only the expected timedeltas are indeed accepted by ``Clock``"""
    tcs.case.run_test(Clock)


# Defines the time range for one year (Jan 1, 2024, to Jan 1, 2025)
_time_range_1yr = {
    "start": datetime.strptime("2024", "%Y"),
    "end": datetime.strptime("2025", "%Y"),
}

# Defines the time range for one month (April 1 to May 1, 2025)
_time_range_1mo = {
    "start": datetime.strptime("2025-04", "%Y-%m"),
    "end": datetime.strptime("2025-05", "%Y-%m"),
}

# Defines the time range for one week in April
_time_range_1wk = {
    "start": datetime.strptime("2025-04-07", TIME_FMT_DAY),
    "end": datetime.strptime("2025-04-11", TIME_FMT_DAY),
}

# Defines the time range for a single day in April
_time_range_1d = {
    "start": datetime.strptime("2025-04-07", TIME_FMT_DAY),
    "end": datetime.strptime("2025-04-07", TIME_FMT_DAY),
}


def _dt(s: str) -> datetime:
    """helper that returns a datetime with tz"""
    _tz = ZoneInfo("America/New_York")
    fmt = "%Y-%m-%dT%H:%M"
    return get_datetime(s, fmt, _tz)


def _get_intraday_min_bars(i: int):
    """helper function to test_clock_iterator to create minute bars list"""
    if 60 % i != 0:
        raise ValueError("Can only get intraday for intervals that fit in 60")
    ret = []
    day = _time_range_1d["start"].strftime(TIME_FMT_DAY)
    for m in range(30, 60, i):  # Get first 30 mins
        opn = _dt(f"{day}T09:{m:02}")
        clz = _dt(f"{day}T{'09' if m != (60 - i) else '10'}:{(m + i) % 60:02}")
        ret.append(Bar(opn, clz))
    for h in range(10, 16):
        for m in range(0, 60, i):  # Get rest of the day
            opn = _dt(f"{day}T{h:02}:{m:02}")
            clz = _dt(f"{day}T{h if m != (60 - i) else h + 1}:{(m + i) % 60:02}")
            ret.append(Bar(opn, clz))

    return ret


# I pass raises=None & exc_msg=None because of Pylint is unhappy with the **kwargs
tcs_clock_iters = TestCases(
    "test_clock_iterator",
    [
        TestCase(
            "test_1w_bars",
            case=Case.ITERATOR,
            interval="1w",
            result=[
                Bar(_dt("2025-04-01T09:30"), _dt("2025-04-04T16:00")),  # Mid week
                Bar(_dt("2025-04-07T09:30"), _dt("2025-04-11T16:00")),
                Bar(_dt("2025-04-14T09:30"), _dt("2025-04-17T16:00")),  # Good Friday
                Bar(_dt("2025-04-21T09:30"), _dt("2025-04-25T16:00")),
                Bar(_dt("2025-04-28T09:30"), _dt("2025-05-01T16:00")),  # Ends mid week
            ],
            raises=None,
            exc_msg=None,
            **_time_range_1mo,
        ),
        TestCase(
            "test_1d_bars",
            case=Case.ITERATOR,
            interval="1d",
            result=[
                Bar(_dt(f"2025-04-{i:02}T09:30"), _dt(f"2025-04-{i:02}T16:00"))
                for i in range(7, 12)
            ],
            raises=None,
            exc_msg=None,
            **_time_range_1wk,
        ),
        # Intraday cases
        TestCase(
            "test_1m_bars",
            interval="1m",
            case=Case.ITERATOR,
            result=_get_intraday_min_bars(1),
            raises=None,
            exc_msg=None,
            **_time_range_1d,
        ),
        TestCase(
            "test_5m_bars",
            interval="5m",
            case=Case.ITERATOR,
            result=_get_intraday_min_bars(5),
            raises=None,
            exc_msg=None,
            **_time_range_1d,
        ),
        TestCase(
            "test_10m_bars",
            interval="10m",
            case=Case.ITERATOR,
            result=_get_intraday_min_bars(10),
            raises=None,
            exc_msg=None,
            **_time_range_1d,
        ),
        TestCase(
            "test_1h_bars",
            case=Case.ITERATOR,
            interval="1h",
            result=[
                Bar(_dt(f"2025-04-07T{i:02}:30"), _dt(f"2025-04-07T{i+1:02}:30"))
                for i in range(9, 15)
            ]
            + [Bar(_dt("2025-04-07T15:30"), _dt("2025-04-07T16:00"))],
            raises=None,
            exc_msg=None,
            **_time_range_1d,
        ),
    ],
)


@pytest.mark.parametrize("tcs", tcs_clock_iters, ids=tids(tcs_clock_iters))
def test_clock_iterator(tcs: TestCasesIter):
    iterator = Clock(**tcs.case.meta)
    tcs.case.run_test(iterator)
