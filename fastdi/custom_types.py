from enum import Enum, auto
class LifeTime(Enum):
    SINGLETON = auto()
    SCOPED = auto()
    FACTORY = auto()
    CONTEXT = auto()