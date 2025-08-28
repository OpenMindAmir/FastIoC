from enum import Enum, auto
from typing import Callable, Any
class LifeTime(Enum):
    SINGLETON = auto()
    SCOPED = auto()
    FACTORY = auto()

FastDIConcrete = type | Callable[..., Any]