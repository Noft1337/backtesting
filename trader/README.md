# Trader
Trader is a class that holds all the information needed to backtest using registered methods. This class will back test in price action chunks in order to reduce download time.

## Arguments
- `ticker`: The ticker to backtest on
- `start`: beginning of time range 
- `end`: end of time range
- `interval`: the chart's time interval on which the main backtest will be done

## Functions
- `register()`: register a new method, takes a `MethodWeighted` class as argument
- `start()`: start backtesting

### Todos:
- determine how to calculate final volume
- fetch all data using `yfinance`
- Be cautios of start & close prices
- include tqdm that shows how many intervals have been processed out of total intervals to be processed
  - calculate total intervals 
  - calculate total processed 
  - run progress in a thread ? 