"""Utilities and helpers to the tests module"""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo


def get_datetime(s: str, fmt: str, tz: Optional[ZoneInfo] = None) -> datetime:
    """Parse datetime string and optinally, add timezone"""
    d = datetime.strptime(s, fmt)
    if tz:
        d.replace(tzinfo=tz)
    return d
