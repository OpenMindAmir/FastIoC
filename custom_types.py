from typing import Callable, Generator
from enum import Enum
from dataclasses import dataclass

class LifeTime(Enum):
    SINGLETON = 0
    SCOPED = 1
    FACTORY = 2

@dataclass(frozen=True)
class Dependency:
    Implementation: type | object
    LifeTime: LifeTime

FastAPIDependable = Callable[[], object | Generator[object]]