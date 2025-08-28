import re
from datetime import timedelta


def parse_interval(i: str) -> timedelta:
    """Parses an interval string into a datetime.timedelta object.

    The string should be a sequence of number-unit pairs, such as '3d6h' or '2w'.
    Spaces between pairs are ignored.

    NOTE:
        This function does not support month or year intervals, as their duration
        is not constant. Using 'mo' will raise a ValueError. For calculations
        involving months, consider using `dateutil.relativedelta`.

    Args:
        i (str): The interval string to parse. Examples: "30m", "1d12h", "2w".

    Returns:
        datetime.timedelta: The resulting timedelta object.

    Raises:
        ValueError: If the string format is invalid or contains unknown units
    """
    regex = r"^(?:(\d+)w)?\s*(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?\s*"
    m = re.fullmatch(regex, i)
    if not m or all(x is None for x in m.groups()):
        raise ValueError(
            f"Time fmt: {i} is not allowed. "
            "Allowed formats must have one of these units included: w,d,h,m,s"
        )
    try:
        weeks, days, hours, minutes, seconds = (int(g) if g else 0 for g in m.groups())
    except ValueError as e:  # Shouldn't ever be raised because regex is matching digits
        raise ValueError(
            f"Time fmt: {i} is not allowed, time must be a digit followed by a unit"
        ) from e
    days = weeks * 7 + days
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
