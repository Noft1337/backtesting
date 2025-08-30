# pylint: disable=C0103,W0614,W0401
import pytest
from datetime import timedelta, datetime

from tests import *
from clock import Clock
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
        TestCase(interval="30d", start=_start),
        TestCase(interval=timedelta(days=30), start=_start),
        TestCase(interval="1w", start=_start),
        TestCase(interval="4w", start=_start),
        TestCase(interval=timedelta(days=28), start=_start),
        # Exception cases
        TestCase(interval="invalid", start=_start, raises=ValueError),
        TestCase(interval="3d", start=_start, raises=IntervalNotSupported),
        TestCase(interval=timedelta(days=4), start=_start, raises=IntervalNotSupported),
    ],
)


@pytest.mark.parametrize("tcs", tcs_clock_interval, ids=tids(tcs_clock_interval))
def test_clock_interval(tcs: TestCasesIter):
    """Test that only the expected timedeltas are indeed accepted by ``Clock``"""
    T.run_test_case(Clock, tcs.case)


# todo: test clock iteration
# [X] - intraday
# [ ] - 1 hour
# [ ] - 1 day
# [ ] - 1 week
# [ ] - 4 week
