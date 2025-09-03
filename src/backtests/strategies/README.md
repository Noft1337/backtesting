# Strategies
This is the parent class that all the methods inherit from this will specify how long should the price action of a ticker be inspected before taking action and/or, when to take action.  
When the method is "confirmed", a percentage of certianty will be returned according to how many triggers were activated

# `class: Logic`
This is the actual core building block of a method, this simply checks if the registered logic is `True`/`False`
---
# `class: Trigger`
This class is given a weight, a price action and logic and checks if the logic is applied to the given price action
---
# `class: Method`
## Arguments
>**_Note_:** either `timed` and/or `conditioned` is required to be True or else an exception will be raised
- `price_action`: the price action to run the method on
- `timed`: is this method requiring some timeframe to inspect the price action
- `conditioned`: is this method requiring 
- `triggers`: a set of triggers


## Functions
- `register_trigger()`: register a trigger of type `Trigger`
- `get_price_action()`: calculates the price action of the interval
- `trigger()`: if some condition of the method is activated, return the percentage of trigger