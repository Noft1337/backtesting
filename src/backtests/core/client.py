import pandas as pd
import yfinance as yf
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from .price_action import PriceAction
from ..exceptions import EmptyPriceActionError, WTF


class YClient(BaseModel):
    """
    This is the class that gets the financial data of tickers using time ranges,
    intervals and such.
    It also supports chunking the financial data to prevent long download times
    """

    _yf_time_fmt: str = "%Y-%m-%d"

    def get_price_action(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
        interval: str,
        chunk: Optional[timedelta] = None,
    ) -> PriceAction:
        """
        Get a |ticker|, a |start| and |end| time, and |chunk| time.
        This will then return only the Price Action within the given
        range and only a data chunk of size |chunk|

        NOTE: Doesn't support multiple tickers. YET.

        Args:
            tikcer(str): the ticker to use
            start(datetime): begining of time range
            end(datetime): end of time range
            interval(str): timedelta in str repr (e.g '1d')
            chunk(optional, timedelta): if present, "paginate" the
                price action to these timedeltas to prevent the need
                to download a super large time range action
        """
        ystart = start.strftime(self._yf_time_fmt)
        chunked_end = start + chunk if chunk else None

        # Calculate the real end time using chunk (if needed)
        if chunked_end and chunked_end > end:
            real_end = chunked_end
        else:
            real_end = end
        yend = real_end.strftime(self._yf_time_fmt)
        data = yf.download(
            ticker,
            start=ystart,
            end=yend,
            interval=interval,
            auto_adjust=True,
            group_by="ticker",
        )
        if data is None:
            raise EmptyPriceActionError(
                f"Can't fetch data for {ticker} between {ystart} -> {yend}"
            )

        # No Support for multi-index DataFrames
        tdata = data[ticker].copy()
        # Here for linting, shows tdata as pd.Series for some reason...
        if not isinstance(tdata, pd.DataFrame):
            raise WTF("For some reason, the data returned isn't a DataFrame")
        return PriceAction(
            ticker=ticker,
            data=tdata,
            start=start,
            end=real_end,
            chunk=chunk,
        )
