import pytest
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union, NamedTuple, Optional, Any


class Case(Enum):
    """Enumerator object to define a type of a TestCase

    Attributes:
        SIMPLE: a simple case of runing a function and comparing its return value
        RAISES: an Exception should be raised
        ITERATOR: The object is an iterator, verify its iterations
        CLASS(Not Implemented yet): test that a class was initialized properly
    """

    SIMPLE = auto()
    RAISES = auto()
    ITERATOR = auto()
    CLASS = None


TestSubject = Union[Callable, Iterator]


class TestCase:
    """A single TestCase for TestCases, receives all the needed information about
    an unknown function's runtime behavior, and serves the caller with it.
    By 'caller' I mean the software that has called this object. Assuming it's either
    ``TestCases`` or ``Tester``

    Supplying ``case_`` is optional. The instance will infer which is the correct case
    IF it's either SIMPLE or RAISES. However, it can't differ between SIMPLE and
    ITERATOR.
    """

    __test__ = False  # make pytest not think this should be tested

    def __init__(
        self,
        name: str = "",
        case: Case = Case.SIMPLE,
        result: Optional[Any] = None,
        raises: Optional[type[Exception]] = None,
        exc_msg: Optional[str] = None,
        **kwargs,
    ):
        self.name = name
        self.case = case
        self.result = result
        self.raises = raises
        self.exc_msg = exc_msg
        self.meta = kwargs
        self._is_result = self.result is not None
        self._is_exc = self.raises is not None
        self._is_exc_msg = self.exc_msg is not None

        # If ``raises`` is set, force ``case`` to be RAISES
        if self._is_exc and self.case != Case.RAISES:
            self.case = Case.RAISES

        self._tests = {
            Case.SIMPLE: self.test_simple,
            Case.RAISES: self.test_raises,
            Case.ITERATOR: self.test_iter,
            Case.CLASS: self.test_class,
        }

    def test_simple(self, f: Callable):
        """Test a Simple Case"""
        res = f(**self.meta)
        # If res is None, assume the function tested for simply not crashing
        # regardless of the returned value
        if self._is_result and res != self.result:
            pytest.fail(f"Expected result: {self.result} but got: {res}")

    def test_raises(self, f: Callable):
        """Test an Exception Case"""
        assert self.raises is not None
        with pytest.raises(self.raises, match=self.exc_msg):
            f(**self.meta)

    def test_iter(self, it: Iterator):
        """Test an Iterator Case"""
        results = []
        for i in it:
            results.append(i)
        if self.result != results:
            pytest.fail(
                f"Iteration expected results:\n\t{self.result}\n"
                f"Actual results\n\t{results}"
            )

    def test_class(self, f: Callable):
        raise NotImplementedError("Case.CLASS Isn't implemented yet")

    def run_test(self, f: TestSubject):
        return self._tests[self.case](f)


class TestCasesIter(NamedTuple):
    __test__ = False  # make pytest not think this should be tested
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

    __test__ = False  # make pytest not think this should be tested

    name: str
    cases: list[TestCase]

    i: int = field(default_factory=int, init=False)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self) -> TestCasesIter:
        if self.i == len(self.cases):
            raise StopIteration
        try:
            cur_case = self.cases[self.i]
            name = f"{self.name}_{self.i}" if not cur_case.name else f"{cur_case.name}"
            return TestCasesIter(name, cur_case)
        finally:
            self.i += 1
