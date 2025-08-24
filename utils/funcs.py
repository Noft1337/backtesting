import yfinance as yf
from typing import Optional
from datetime import datetime, timedelta

from .models import PriceAction


YF_TIME_FMT = "%y-%m-%d"


def get_price_action(
    ticker: str,
    start: datetime,
    end: datetime,
    interval: str,
    chunk: Optional[timedelta],
) -> PriceAction:
    """
    Get a |ticker|, a |start| and |end| time, and |chunk| time.
    This will then return only the Price Action within the given
    range and only a data chunk of size |chunk|

    Args:
        tikcer(str): the ticker to use
        start(datetime): begining of time range
        end(datetime): end of time range
        interval(str): timedelta in str repr (e.g '1d')
        chunk(optional, timedelta): if present, "paginate" the
            price action to these timedeltas to prevent the need
            to download a super large time range action
    """
    ystart = start.strftime(YF_TIME_FMT)
    chunked_end = start + chunk if chunk else None

    # Calculate the real end time using chunk (if needed)
    if chunked_end and chunked_end > end:
        real_end = chunked_end
    else:
        real_end = end
    yend = real_end.strftime(YF_TIME_FMT)
    data = yf.download(ticker, start=ystart, end=yend, interval=interval)
    if data is None:  # todo: create a more indicative Exception class
        raise Exception(f"Can't fetch data for {ticker} between {ystart} -> {yend}")

    return PriceAction(data=data, start=start, end=real_end, chunk=chunk)
