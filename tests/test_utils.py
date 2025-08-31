# pylint: disable=C0103,W0614,W0401
import pytest
from datetime import timedelta, datetime

from tests import *
from utils.funcs import parse_interval, td_to_str, discard_datetime_by_interval


_exc_msg_1 = "Allowed formats must have one of these units included: w,d,h,m,s"
tcs_parse_interval = TestCases(
    "parse_interval",
    [
        TestCase(i="1w", result=timedelta(days=7)),
        TestCase(i="2d", result=timedelta(days=2)),
        TestCase(i="3h", result=timedelta(hours=3)),
        TestCase(i="4m", result=timedelta(minutes=4)),
        TestCase(i="5s", result=timedelta(seconds=5)),
        TestCase(i="1w1d", result=timedelta(days=8)),
        TestCase(i="26h65m", result=timedelta(days=1, hours=3, minutes=5)),
        TestCase(
            i="1w1d1h1m1s", result=timedelta(days=8, hours=1, minutes=1, seconds=1)
        ),
        TestCase(i="1d1h1s", result=timedelta(days=1, hours=1, seconds=1)),
        # Exception cases
        TestCase(i="1q", raises=ValueError, exc_msg=_exc_msg_1),
        TestCase(i="1w1q", raises=ValueError, exc_msg=_exc_msg_1),
        TestCase(i="0.1w", raises=ValueError, exc_msg=_exc_msg_1),
        TestCase(i="1w0.1d", raises=ValueError, exc_msg=_exc_msg_1),
    ],
)


@pytest.mark.dependency(name="test_parse_interval")
@pytest.mark.parametrize("tc", tcs_parse_interval, ids=tids(tcs_parse_interval))
def test_parse_interval(tc: TestCasesIter):
    tc.case.run_test(parse_interval)


tcs_td_to_str = TestCases(
    "td_to_str",
    [
        TestCase(i=parse_interval("1d"), result="1d"),
        TestCase(i=parse_interval("4w"), result="4w"),
        TestCase(i=parse_interval("1d2h"), result="1d2h"),
        TestCase(i=parse_interval("30d"), result="4w2d"),
        TestCase(i=parse_interval("1w2d3h"), result="1w2d3h"),
        TestCase(i=parse_interval("1d26h"), result="2d2h"),
        TestCase(i=parse_interval("26h65m"), result="1d3h5m"),
        TestCase(i=parse_interval(f"{3600 * 25}s"), result="1d1h"),
    ],
)


@pytest.mark.dependency(depends=["test_parse_interval"])
@pytest.mark.parametrize("tc", tcs_td_to_str, ids=tids(tcs_td_to_str))
def test_td_to_str(tc: TestCasesIter):
    tc.case.run_test(td_to_str)


_ts = datetime.strptime("2001-01-01T16:30:05.123", "%Y-%m-%dT%H:%M:%S.%f")
tcs_discard_datetime_by_interval = TestCases(
    "",
    [
        TestCase(
            dt=_ts,
            i=timedelta(days=1),
            result=datetime.strptime("2001-01-01", "%Y-%m-%d"),
        ),
        TestCase(
            dt=_ts,
            i=timedelta(hours=1),
            result=datetime.strptime("2001-01-01T16", "%Y-%m-%dT%H"),
        ),
        TestCase(
            dt=_ts,
            i=timedelta(minutes=1),
            result=datetime.strptime("2001-01-01T16:30", "%Y-%m-%dT%H:%M"),
        ),
        TestCase(
            dt=_ts,
            i=timedelta(seconds=1),
            result=datetime.strptime("2001-01-01T16:30:05", "%Y-%m-%dT%H:%M:%S"),
        ),
        TestCase(
            dt=_ts,
            i=timedelta(microseconds=1),
            result=_ts,
        ),
        TestCase(dt=_ts, i=timedelta(-1), raises=ValueError),
    ],
)


# TODO: Figure why this skips the test
# @pytest.mark.dependency(depends=["test_td_to_str"])
@pytest.mark.parametrize(
    "tc", tcs_discard_datetime_by_interval, ids=tids(tcs_discard_datetime_by_interval)
)
def test_discard_datetime_by_interval(tc: TestCasesIter):
    tc.case.run_test(discard_datetime_by_interval)
