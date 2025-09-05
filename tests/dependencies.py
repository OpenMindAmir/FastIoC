from dataclasses import dataclass
from typing import Protocol, Generator, Annotated

from fastapi import Depends

from .constants import *

# --- State ---


@dataclass
class State:
    GlobalServiceNumber: int = 0
    GlobalDirectNumber: int = 0
    GlobalUsualNumber: int = 0
    GeneratorExitNumber: int = 0
    NestedNumber: int = 0

    _instance: 'State | None' = None

    @classmethod
    def get(cls) -> 'State':
        if cls._instance == None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = cls()


state = State()

# --- Class Based Dependencies ---


class INumberService(Protocol):

    def GetNumber(self) -> int: ...


class NumberService(INumberService):
    def __init__(self) -> None:
        self.number = SERVICE_NUMBER

    def GetNumber(self) -> int:
        return self.number


class IGlobalService(Protocol):
    ...


class GlobalService(IGlobalService):
    def __init__(self) -> None:
        state.get().GlobalServiceNumber = GLOBAL_SERVICE_NUMBER


# --- Function Based Depedencies ---

class FunctionNumber(int):
    ...


def GetFunctionNumber() -> int:
    return FUNCTION_NUMBER


class GlobalFunctionNumber(int):
    ...


def SetGlobalFunctionNumber():
    state.get().GlobalDirectNumber = GLOBAL_FUNCTION_NUMBER


def SetGlobalUsualNumber():
    state.get().GlobalUsualNumber = GLOBAL_USUAL_NUMBER


class GeneratorDependencyType(int):
    ...


def GeneratorDependency() -> Generator[int, None, None]:
    try:
        yield GENERATOR_NUMBER
    finally:
        state.get().GeneratorExitNumber = GENERATOR_EXIT_NUMBER


# --- Nested Dependencies ---


def GetUsualNestedNumber() -> int:
    return NESTED_NUMBER


class DependentNestedNumber(int):
    ...


def GetDependentNestedNumber(number: int = Depends(GetUsualNestedNumber)) -> int:
    return number


class INestedService(Protocol):

    def GetNumber(self) -> int: ...

    def GetServiceNumber(self) -> int: ...

    def GetNestedNumber(self) -> int: ...


class NestedService(INestedService):

    def __init__(self, service: INumberService, nested: Annotated[int, DependentNestedNumber], number: int = Depends(GetUsualNestedNumber)):
        self.serviceNumber = service.GetNumber()
        self.usualNumber = number
        self.nestedNumber = nested

    def GetNumber(self) -> int:
        return self.usualNumber

    def GetServiceNumber(self) -> int:
        return self.serviceNumber

    def GetNestedNumber(self) -> int:
        return self.nestedNumber


class IGlobalNestedNumber(type):
    ...


def GlobalNestedNumber():
    state.get().NestedNumber = NESTED_NUMBER


class IGlobalNestedService(Protocol):
    ...


class GlobalNestedService(IGlobalNestedService):
    def __init__(self, nested: IGlobalNestedNumber) -> None:
        return None


# --- Lifetime Dependencies ---

class ILifetimeService(Protocol):

    index: int

    def GetCurrentItem(self) -> int: ...


class ILifetimeServiceSingleton(ILifetimeService):
    ...


class ILifetimeServiceScoped(ILifetimeService):
    ...


class ILifetimeServiceFactory(ILifetimeService):
    ...


class LifetimeServiceSingleton(ILifetimeServiceSingleton):

    def __init__(self) -> None:
        self.index = 0

    def GetCurrentItem(self) -> int:
        self.index += 1
        return NUMBERS[self.index]


class LifetimeServiceScoped(ILifetimeServiceScoped):

    def __init__(self) -> None:
        self.index = 0

    def GetCurrentItem(self) -> int:
        self.index += 1
        return NUMBERS[self.index]


class LifetimeServiceFactory(ILifetimeServiceFactory):

    def __init__(self) -> None:
        self.index = 0

    def GetCurrentItem(self) -> int:
        self.index += 1
        return NUMBERS[self.index]
