from tests.tester import TestCasesIter, TestCases, TestCase

# Use for all tests

__all__ = [
    "TestCase",
    "TestCases",
    "TestCasesIter",
    "tids",
]


def tids(tcs: TestCases) -> list:
    """Return the ids of the TestCases"""
    return [tc.name for tc in tcs]
