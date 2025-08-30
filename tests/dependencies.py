from dataclasses import dataclass
from typing import Protocol

from .constants import *

# --- State ---


@dataclass
class State:
    GlobalServiceNumber: int = 0
    GlobalDirectNumber: int = 0
    GlobalUsualNumber: int = 0


    _instance: 'State | None' = None

    @classmethod
    def get(cls) -> 'State':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = cls()


state = State()

# --- Interfaces ---


class INumberService(Protocol):

    def GetNumber(self) -> int: ...


class IGlobalService(Protocol):
    ...


# --- Implementations ---


class NumberService(INumberService):
    def __init__(self) -> None:
        self.number = SERVICE_NUMBER

    def GetNumber(self) -> int:
        return self.number


class GlobalService(IGlobalService):
    def __init__(self) -> None:
        state.GlobalServiceNumber = GLOBAL_SERVICE_NUMBER


# --- Direct Depedencies ---

class DirectNumber(int): ...

def GetDirectNumber() -> int:
    return DIRECT_NUMBER

class GlobalDirectNumber(int): ...

def SetGlobalDirectNumber():
    state.GlobalDirectNumber = GLOBAL_DIRECT_NUMBER

def SetGlobalUsualNumbe():
    state.GlobalUsualNumber = GLOBAL_USUAL_NUMBER