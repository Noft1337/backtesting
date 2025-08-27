import pytest
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional, Any, NamedTuple, Union


class TestCase:
    """A single TestCase for TestCases, receives all the needed information about
    an unknown function's runtime behavior, and serves the caller with it.
    By 'caller' I mean the software that has called this object. Assuming it's either
    ``TestCases`` or ``Tester``

    """

    def __init__(
        self,
        result: Optional[Any],
        raises: Optional[type[Exception]],
        exc_msg: Optional[str],
        **kwargs,
    ):
        self.kw = kwargs
        self.result = result
        self.is_result = result is not None
        self.exc = raises
        self.is_exc = raises is not None
        self.exc_msg = exc_msg
        self.is_exc_msg = exc_msg is not None

    def verify(self, res: Optional[Any], exc: Optional[Any], exc_msg: Optional[str]):
        """Verifies that a tested function's output is as expected
        NOTE: maybe deleted in the future due to pytest having similar functions
        """
        if res:
            assert self.result is not None, "No Result was expected"
            assert self.result == exc, "Returned result doesn't match"
        if exc:
            assert self.exc is not None, "No Exception was suppossed to be raised"
            assert (
                self.exc == exc
            ), f"Expected the exception: {type(self.exc)} but got {type(exc)}"
        if exc_msg:
            assert (
                self.exc is not None and exc is not None
            ), "Exception message was provided but no Exception ?"
            assert re.match(
                exc_msg, str(exc)
            ), f'Expression: "{exc_msg}" is not in {type(exc)}, got {exc} instead'


class TestCasesIter(NamedTuple):
    name: str
    case: TestCase


@dataclass
class TestCases:
    """Helper class that produces test cases with unknown kwargs and attaches
    a name to each test to help identify which test is ran.
    To use this class for testing, iterating over it is needed. When iterated, it
    allows to test each case alone

    Args:
        name(str): the name prefix of the test
        cases(list[dict]): a list of kwargs that will be passed to the test
    """

    name: str
    cases: list[Union[TestCase, dict]]

    i: int = field(default_factory=int, init=False)

    def _parse_test_case(self, tcase: dict) -> TestCase:
        """Creates a new ``TestCase`` object using a dictionary, this is done by first
        converting ``tcase`` into a default dict that returns `None` when a key is
        missing and that way saves the need to verify wether optional arguments are
        present. Then it deletes these arguments to not pass them twice and tcase is
        then passed as the ``kwargs`` that ``TestCase`` requires
        """
        tcase = defaultdict(lambda: None, tcase)
        tc_kwargs = {
            "result": tcase["result"],
            "raises": tcase["raises"],
            "exc_msg": tcase["exc_msg"],
        }
        del tcase["result"]
        del tcase["raises"]
        del tcase["exc_msg"]
        return TestCase(**tc_kwargs, **tcase)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self) -> TestCasesIter:
        try:
            name = f"{self.name}_{self.i}"
            cur_case = self.cases[self.i]
            if isinstance(cur_case, TestCase):
                return TestCasesIter(name, cur_case)
            return TestCasesIter(name, self._parse_test_case(cur_case))
        finally:
            self.i += 1


# TODO: find a way to name each test
class Tester:
    """Helper class that runs a function and tests if its behavior based on logic that
    is defined and provided by ``TestCases``
    """

    def _run_with_except(self, f: Callable, tcr: TestCase):
        assert tcr.exc is not None
        with pytest.raises(tcr.exc, match=tcr.exc_msg):
            f(**tcr.kw)

    def run_tests(self, f: Callable, tcs: TestCases):
        """Runs a function ``f`` for each ``TestCase`` in ``TestCases`` and verifies its
        behavior. Checkes if the expected result is returned, if the right Exception is
        raised and also, if present, if the raised Exception contains a certian string
        """
        for t in tcs:
            tcase = t.case
            if tcase.exc is not None:
                self._run_with_except(f, tcase)
            else:
                res = f(**tcase.kw)
                if res != tcase.result:
                    pytest.fail(f"Expected result: {tcase.result} but got: {res}")
