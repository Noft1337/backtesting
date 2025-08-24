from pydantic import BaseModel
from dataclasses import dataclass


@dataclass
class Logic:
    pass

    def is_true(self) -> bool:
        """Runs the logic"""
        return self.__sizeof__() != 0


@dataclass
class Trigger:
    weight: int


@dataclass
class Method(BaseModel):
    ticker: str
    timed: bool
    conditioned: bool

    def __post_init__(self):
        self.triggers: set[Trigger]

    def register_trigger(self, t: Trigger):
        self.triggers.add(t)


@dataclass
class MethodWeighted:
    m: Method
    weight: int
