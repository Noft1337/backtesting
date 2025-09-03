class WTF(Exception):
    """SHOULD NEVER be raised"""


class IntervalNotSupported(Exception):
    """Raised when the supplied interval is not supported/allowed"""


class InvalidIntervalFormat(Exception):
    """Raised when a str representation of a time interval is invalid"""


class IdenticalSMASCantCrossError(Exception):
    pass


class EmptyPriceActionError(Exception):
    pass
