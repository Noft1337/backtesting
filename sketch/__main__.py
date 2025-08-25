from datetime import datetime
from utils.models import YClient

CASH = 1000.0


def main():
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

        prev_cash = d.iat[i, col_cash]
        prev_hold = d.iat[prev, col_hold]
        day_ret = d.iat[i, col_ret]

        if sig == 1:  # SMAs Crossed UP, go Long
            d.iat[i, col_cash] = 0.0
            d.iat[i, col_hold] = prev_cash * day_ret
        elif sig == -1:  # SMAs Crossed Down, Liquidate
            d.iat[i, col_cash] = prev_hold
            d.iat[i, col_hold] = 0.0
        else:  # Update Holdings based on the daily return
            d.iat[i, col_hold] = prev_cash * day_ret

        # update values
        d.iat[i, col_total] = d.iat[i, col_hold] + d.iat[i, col_cash]

    return pa


if __name__ == "__main__":
    main()
