"""
Defines core types, enums, and aliases used throughout the FastDI library.
"""

from enum import Enum, auto
from typing import Callable, Any

from fastapi.params import Depends

class LifeTime(Enum):
    """
    Dependency lifetime policy.

    - SINGLETON: One instance shared for the whole process/worker.
    - SCOPED: One instance per HTTP request.
    - FACTORY: A new instance on every resolve.
    """
    SINGLETON = auto()
    SCOPED = auto()
    FACTORY = auto()


FastDIConcrete = type | Callable[..., Any]
FastDIDependency = type | Depends

DEPENDENCIES = 'dependencies'
