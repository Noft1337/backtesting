# Backtesting
This repo is my way of backtesting various trading methods.

## Architecture
These are the core components that construct this project

### [methods](methods/)
This module holds all the supported methods within. Current supported methods are:
- [**Mark Fisher's ACD Breakout**](methods/breakouts/acd)

### [trader](trader/)
This is the brain of this backtesting program. The way it works is by registering a method (that's located in [methods](methods/)) and giving it a weight so that when multiple methods are in conflict, the buy/sell and/or long/short position will be determined by the summed weight of all methods together.

---
## Todos
- use `jetblack-markdown` to generate docs
- create a **pre-commit** that generates docs