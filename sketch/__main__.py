from datetime import datetime
from src.backtests.core import YClient, Clock
from src.backtests.config import TIME_FMT_DAY

CASH = 1000.0


def smas_cross():
    c = YClient()
    start = datetime.strptime("2025-01-01", "%Y-%m-%d")
    end = datetime.now()
    pa = c.get_price_action("SPY", start=start, end=end, interval="1d")
    ret_name = "Daily_Return"
    pa.calc_return(ret_name)
    smas_cross = pa.get_sma_cross(50, 100)

    d = pa.data
    d["Holdings"] = 0.0  # Value of our stock
    d["Cash"] = CASH  # Cash on hand
    d["Total"] = CASH  # Total portfolio value

    col_hold = d.columns.get_loc("Holdings")
    col_cash = d.columns.get_loc("Cash")
    col_ret = d.columns.get_loc("Daily_Return")
    col_total = d.columns.get_loc("Total")

    # Iterate over all the days in the range, for each day, if the SMAs crossed up,
    # Go Long with 100% of |cash|, if they crossed down, liquidate all positions.
    # If nothing happened, calculate the holdings, current holdings * daily change (%)
    for i in range(1, len(d)):
        prev = i - 1  # I hate seeing so many `i - 1`s
        sig = smas_cross.position.iat[i]

        prev_cash = d.iat[prev, col_cash]
        prev_hold = d.iat[prev, col_hold]
        day_ret = d.iat[i, col_ret]

        if sig == 1:  # SMAs Crossed UP, go Long
            d.iat[i, col_cash] = 0.0
            d.iat[i, col_hold] = prev_cash * (1 + day_ret)
        elif sig == -1:  # SMAs Crossed Down, Liquidate
            d.iat[i, col_cash] = prev_hold
            d.iat[i, col_hold] = 0.0
        else:  # Update Holdings based on the daily return
            d.iat[i, col_cash] = prev_cash
            d.iat[i, col_hold] = prev_hold * (1 + day_ret)

        # update values
        d.iat[i, col_total] = d.iat[i, col_hold] + d.iat[i, col_cash]

    last_total = d.iat[-1, col_total]
    pct = (last_total - CASH) / CASH * 100
    print(
        f"Cash on start: {CASH:.2f}\n"
        f"Cash after investing: {last_total:.2f} ({pct:.2f}%)"
    )

    return pa


def iter_clock():
    start = datetime.strptime("2025-04-07", TIME_FMT_DAY)
    end = datetime.strptime("2025-04-15", TIME_FMT_DAY)
    c = Clock(start, end, interval="1w")
    fmt = "%Y-%m-%dT%H:%M:%S"
    for t in c:
        print(f"Open: {t.open.strftime(fmt)}\tClose: {t.close.strftime(fmt)}")


def main():
    iter_clock()


if __name__ == "__main__":
    main()
