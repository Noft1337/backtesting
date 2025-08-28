from tests.tester import Tester, TestCasesIter, TestCases, TestCase

# Use for all tests
T = Tester()

__all__ = [
    "T",
    "TestCase",
    "TestCases",
    "TestCasesIter",
    "tids",
]


def tids(tcs: TestCases) -> list:
    """Return the ids of the TestCases"""
    return [tc.name for tc in tcs]
