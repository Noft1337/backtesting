import pytest
from sketch import sketch
from tests.tester import TestCases, TestCase, TestCasesIter


tcs_sketch = TestCases(
    "test_sketch",
    [
        TestCase(a=0, b=0, result=True),
        TestCase(a=1, b=0, result=False),
        TestCase(a=0, b=1, raises=ValueError, exc_msg="A IS LOWER THAN B !!!"),
    ],
)


@pytest.mark.parametrize("test_case", tcs_sketch, ids=[tc.name for tc in tcs_sketch])
def test_sketch(test_case: TestCasesIter):
    test_case.case.run_test(sketch)
