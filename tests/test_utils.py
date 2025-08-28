# pylint: disable=C0103,W0614,W0401
import pytest
from datetime import timedelta

from tests import *
from utils.funcs import parse_interval


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


@pytest.mark.parametrize(
    "tc", tcs_parse_interval, ids=[t.name for t in tcs_parse_interval]
)
def test_parse_interval(tc: TestCasesIter):
    T.run_test_case(parse_interval, tc.case)
