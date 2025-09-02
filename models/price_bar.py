from consts import TIME_FMT_FULL
from datetime import datetime
from typing import NamedTuple


class Bar(NamedTuple):
    open: datetime
    close: datetime

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        fmt = TIME_FMT_FULL
        return f"open={self.open.strftime(fmt)} close={self.close.strftime(fmt)}"
