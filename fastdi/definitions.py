"""
Defines core types, enums, and aliases used throughout the FastDI library.
"""

from enum import Enum, auto
from typing import Callable, Any, Generic, TypeVar
from dataclasses import dataclass

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

D = TypeVar('D')

@dataclass
class Dependency(Generic[D]):
    """
    Represents a dependency to be registered in the DI container.

    This class holds all the necessary metadata for a dependency, including:
    - The interface or protocol it implements (`protocol`).
    - The concrete implementation or class (`concrete`).
    - Its lifetime (`lifeTime`), controlling how the container caches or reuses the instance.

    Attributes:
        protocol (type): The interface or protocol type that this dependency implements.
        concrete (type[D]): The concrete implementation class of type `D`.
        lifeTime (LifeTime): The lifetime of the dependency. Can be one of:
            - `LifeTime.SINGLETON`: Single shared instance for the entire container.
            - `LifeTime.SCOPED`: One instance per request or scope.
            - `LifeTime.FACTORY`: A new instance every time it is resolved.

    Generic Type Parameters:
        D: The type of the concrete implementation.

    Usage:
        This class is typically used internally by the DI container, but can be instantiated
        manually if needed.

    Example:

        class INumberService:
            def GetNumber(self) -> int: ...
        
        class NumberService(INumberService):
            def GetNumber(self) -> int:
                return 42

        dep = Dependency[INumberService](
            protocol=INumberService,
            concrete=NumberService,
            lifeTime=LifeTime.SCOPED
        )

        print(dep.protocol)   # <class '__main__.INumberService'>
        print(dep.concrete)   # <class '__main__.NumberService'>
        print(dep.lifeTime)   # LifeTime.SCOPED

    Notes:
        - The container may call `concrete()` to instantiate the dependency when resolving it.
        - Generic typing helps with static type checking and ensures the concrete class
          implements the expected interface.
    """
    protocol: type
    concrete: type[D]
    lifeTime: LifeTime


DEPENDENCIES = 'dependencies'
