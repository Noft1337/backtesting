from datetime import datetime
from typing import NamedTuple


class Bar(NamedTuple):
    open: datetime
    close: datetime
