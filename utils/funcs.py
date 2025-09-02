import re
from datetime import timedelta, datetime


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


def td_to_str(i: timedelta) -> str:
    """Converts a datetime.timedelta into a string representation

    Examples:
        >>> td_to_str(timedelta(days=1)
        "1d"
        >>> td_to_str(timedelta(days=1, hours=12))
        "1d12h"
    """
    ret = ""
    seconds = i.seconds % 60
    minutes = i.seconds // 60 % 60
    hours = i.seconds // 3600
    days = i.days % 7
    weeks = i.days // 7
    d = {"w": weeks, "d": days, "h": hours, "m": minutes, "s": seconds}

    for k, v in d.items():
        if v > 0:
            ret += f"{v}{k}"

    return ret


def discard_datetime_by_interval(dt: datetime, i: timedelta) -> datetime:
    """
    Truncate `dt` by the precision implied by `i` (a timedelta).

    Rules:
        - i >= 1 day      -> keep date only (00:00:00.000000)
        - i >= 1 hour     -> keep up to hour     (mm=ss=us=0)
        - i >= 1 minute   -> keep up to minute   (ss=us=0)
        - i >= 1 second   -> keep up to second   (us=0)
        - 0 < i < 1 sec   -> leave as-is

    Preserves tzinfo/fold.
    """
    if i <= timedelta(0):
        raise ValueError("interval must be positive")

    if i >= timedelta(days=1):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if i >= timedelta(hours=1):
        return dt.replace(minute=0, second=0, microsecond=0)
    if i >= timedelta(minutes=1):
        return dt.replace(second=0, microsecond=0)
    if i >= timedelta(seconds=1):
        return dt.replace(microsecond=0)

    # sub-second intervals: no truncation (microsecond is the smallest unit)
    return dt
