import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, ClassVar, NamedTuple
from ..exceptions import IdenticalSMASCantCrossError


class SMAResult(NamedTuple):
    name: str
    sma: pd.Series


class SMACrossResult(NamedTuple):
    name: str  # e.g., "sma_cross_10_50"
    state: pd.Series  # 1 when sma(s1) > sma(s2), else 0
    position: pd.Series  # +1 on golden cross, -1 on death cross, 0 otherwise


@dataclass
class PriceAction:
    """This class is in charge of handling all the price action that's provided
    from the ``yfinance`` API
    """

    ticker: str
    data: pd.DataFrame
    start: datetime
    end: datetime
    chunk: Optional[timedelta]

    # constants / naming formats (class-level)
    sma_fmt: ClassVar[str] = "SMA_%d"
    sma_cross_fmt: ClassVar[str] = "SMA_CROSS_%d_%d"  # e.g., SMA_CROSS_50_100
    sma_cross_pos_fmt: ClassVar[str] = "%s_POSITION"  # e.g., SMA_CROSS_50_100_POSITION

    # runtime state (instance-level)
    active_smas: set[str] = field(default_factory=set, init=False)
    active_sma_crosses: set[str] = field(default_factory=set, init=False)

    # Will be useful when we support multiple tickers
    # tdata: ClassVar[dict[str, pd.Series]] = {}
    # def __post_init__(self):
    #     self.tickers = self.data.columns.get_level_values(0)
    #     for t in self.tickers:
    #         self.tdata[t] = self.data[t]

    def calc_return(self, col_name: str):
        self.data[col_name] = self.data["Close"].pct_change()

    def get_sma(self, period: int) -> SMAResult:
        """Calculate the SMA of |period| and register it. If the SMA of this |period|
        Already exist, don't calculate it again, just return it

        Return:
            SMAResult: the name identifier of the SMA and the Series itself
        """
        name = self.sma_fmt % period
        if name not in self.active_smas:
            self.data[name] = self.data["Close"].rolling(window=period).mean()
            self.active_smas.add(name)
        return SMAResult(name, self.data[name])

    def get_sma_cross(self, s1: int, s2: int) -> SMACrossResult:
        """Calculate the cross points of 2 SMAs and return it

        Return:
            SMACrossResult: the name identifier and the Series itself
        """
        # Sort it first
        if s1 > s2:
            s1, s2 = s2, s1
        elif s1 == s2:
            raise IdenticalSMASCantCrossError(
                f"Both SMAs provided are with period of {s1}"
            )

        _, sma1 = self.get_sma(s1)
        _, sma2 = self.get_sma(s2)
        cross_name = self.sma_cross_fmt % (s1, s2)
        if cross_name not in self.active_sma_crosses:
            # Keep memory small
            self.data[cross_name] = (sma1 > sma2).astype("int8")

            # events: diff of state; first value -> 0
            position_name = self.sma_cross_pos_fmt % cross_name
            self.data[position_name] = self.data[cross_name].diff()

            # register the cross
            self.active_sma_crosses.add(cross_name)
        return SMACrossResult(
            cross_name, self.data[cross_name], self.data[position_name]
        )
