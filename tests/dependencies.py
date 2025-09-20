from dataclasses import dataclass
from typing import Protocol, Generator, Annotated, Optional

from fastapi import Depends, Request, Cookie, BackgroundTasks

from .constants import *

# --- State ---


@dataclass
class State:
    global_service_number: int = 0
    global_service_number_2: int = 0
    global_service_number_3: int = 0
    global_direct_number: int = 0
    global_usual_number: int = 0
    generator_exit_number: int = 0
    nested_number: int = 0
    global_override_number: int = 0
    background_number: int = 0
    dispose_number: int = 0

    _instance: Optional['State'] = None

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

    def get_number(self) -> int: ...


class NumberService(INumberService):
    def __init__(self) -> None:
        self.number = SERVICE_NUMBER

    def get_number(self) -> int:
        return self.number


class IGlobalService(Protocol):
    ...


class GlobalService(IGlobalService):
    def __init__(self) -> None:
        state.get().global_service_number = GLOBAL_SERVICE_NUMBER


# --- Function Based Depedencies ---

class FunctionNumber(int):
    ...


def get_function_number() -> int:
    return FUNCTION_NUMBER


class GlobalFunctionNumber(int):
    ...


def set_global_function_number():
    state.get().global_direct_number = GLOBAL_FUNCTION_NUMBER


def set_global_usual_number():
    state.get().global_usual_number = GLOBAL_USUAL_NUMBER


class GeneratorDependencyType(int):
    ...


def generator_dependency() -> Generator[int, None, None]:
    try:
        yield GENERATOR_NUMBER
    finally:
        state.get().generator_exit_number = GENERATOR_EXIT_NUMBER


# --- Nested Dependencies ---


def get_usual_nested_number() -> int:
    return NESTED_NUMBER


class DependentNestedNumber(int):
    ...


def get_dependent_nested_number(number: int = Depends(get_usual_nested_number)) -> int:
    return number


class INumberService2(INumberService):
    ...


class NumberService2(INumberService2):
    def __init__(self) -> None:
        self.number = SERVICE_NUMBER_2

    def get_number(self) -> int:
        return self.number


class INestedService(Protocol):

    def get_number(self) -> int: ...

    def get_service_number(self) -> int: ...

    def get_nested_number(self) -> int: ...

    def get_service_number_2(self) -> int: ...


class NestedService(INestedService):

    service2: INumberService2

    def __init__(self, service: INumberService, nested: Annotated[int, DependentNestedNumber], number: int = Depends(get_usual_nested_number)):
        self.service_number = service.get_number()
        self.usual_number = number
        self.nested_number = nested

    def get_number(self) -> int:
        return self.usual_number

    def get_service_number(self) -> int:
        return self.service_number

    def get_nested_number(self) -> int:
        return self.nested_number
    
    def get_service_number_2(self) -> int:
        return self.service2.get_number()


class IGlobalNestedNumber(type):
    ...


def GlobalNestedNumber():
    state.get().nested_number = NESTED_NUMBER


class IGlobalNestedService(Protocol):
    ...


class GlobalNestedService(IGlobalNestedService):
    def __init__(self, nested: IGlobalNestedNumber) -> None:
        return None


# --- Lifetime Dependencies ---

class ILifetimeService(Protocol):

    index: int

    def get_current_item(self) -> int: ...


class ILifetimeServiceSingleton(ILifetimeService):
    ...


class ILifetimeServiceScoped(ILifetimeService):
    ...


class ILifetimeServiceFactory(ILifetimeService):
    ...


class LifetimeServiceSingleton(ILifetimeServiceSingleton):

    def __init__(self) -> None:
        self.index = 0

    def get_current_item(self) -> int:
        self.index += 1
        return NUMBERS[self.index]


class LifetimeServiceScoped(ILifetimeServiceScoped):

    def __init__(self) -> None:
        self.index = 0

    def get_current_item(self) -> int:
        self.index += 1
        return NUMBERS[self.index]


class LifetimeServiceFactory(ILifetimeServiceFactory):

    def __init__(self) -> None:
        self.index = 0

    def get_current_item(self) -> int:
        self.index += 1
        return NUMBERS[self.index]
    

# --- Integration Dependencies ---


class LazyNumber(int): ...


def get_lazy_number() -> int:
    return LAZY_NUMBER


class IGlobalService2(Protocol):
    ...


class GlobalService2(IGlobalService2):
    def __init__(self) -> None:
        state.get().global_service_number_2 = GLOBAL_SERVICE_NUMBER2



# --- Override dependencies ---


class OverrideNumberSerivce(INumberService):
    def __init__(self) -> None:
        self.number = OVERRIDE_SERVICE_NUMBER

    def get_number(self) -> int:
        return self.number
    

class GlobalOverrideService(IGlobalService):
    def __init__(self) -> None:
        state.get().global_override_number = GLOBAL_OVERRIDE_NUMBER


def get_override_function_number() -> int:
    return OVERRIDE_NUMBER

class LifetimeOverrideServiceSingleton(ILifetimeServiceSingleton):

    def __init__(self) -> None:
        self.index = 0

    def get_current_item(self) -> int:
        self.index += 1
        return OVERRIDE_NUMBERS[self.index]


class LifetimeOverrideServiceScoped(ILifetimeServiceScoped):

    def __init__(self) -> None:
        self.index = 0

    def get_current_item(self) -> int:
        self.index += 1
        return OVERRIDE_NUMBERS[self.index]


class LifetimeOverrideServiceFactory(ILifetimeServiceFactory):

    def __init__(self) -> None:
        self.index = 0

    def get_current_item(self) -> int:
        self.index += 1
        return OVERRIDE_NUMBERS[self.index]


# --- Integrity Dependencies ---


def get_extra_text(extra: str, id: int = Cookie()) -> tuple[str, int]:
    return extra, id

class ExtraText(str): ...


def background_task(number: int):
    state.get().background_number = number

class DeeperSerivce:

    request: Request
    id: Annotated[int, Cookie()]

    def get_id(self) -> int:
        return int(self.request.cookies.get('id'))  # pyright: ignore[reportArgumentType]
    
    def get_cookie(self) -> int:
        return self.id

class DeepService:

    service: DeeperSerivce
    aservice: Annotated[DeeperSerivce, DeeperSerivce]
    background: BackgroundTasks

    def __init__(self, request: Request):
        self.id = int(request.cookies.get('id'))  # pyright: ignore[reportArgumentType]
        self.background.add_task(background_task, BACKGROUND_NUMBER)
    
    def get_id(self) -> int:
        return self.id
    
    def get_deep_id(self) -> int:
        return self.service.get_id()
    
    def get_deep_cookie(self) -> int:
        return self.service.get_cookie()
    
    def get_annotated_id(self) -> int:
        return self.aservice.get_id()
    

# --- Dispose Dependencies ---


class IDisposable(Protocol):

    async def __dispose__(self): ...


class Disposable(IDisposable):

    async def __dispose__(self):
        state.get().dispose_number = DISPOSE_NUMBER