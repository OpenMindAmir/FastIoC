from typing import Generator

from typeguard import typechecked

from fastdi.custom_types import Dependency, LifeTime, FastAPIDependable
from fastdi.errors import InterfaceNotRegistered


class Container:

    def __init__(self):
        self.dependencies: dict[type, Dependency] = {}

    @typechecked
    def Register(self, interface: type, implementation: type, lifeTime: LifeTime):
        impl = implementation
        if lifeTime is LifeTime.SINGLETON:
            impl = implementation()
        self.dependencies[interface] = Dependency(
            Implementation=impl, LifeTime=lifeTime)

    def AddSingleton(self, interface: type, implementation: type):
        self.Register(interface, implementation, LifeTime.SINGLETON)

    def AddScoped(self, interface: type, implementation: type):
        self.Register(interface, implementation, LifeTime.SCOPED)

    def AddFactory(self, interface: type, implementation: type):
        self.Register(interface, implementation, LifeTime.FACTORY)

    @typechecked
    def CheckIfRegistered(self, interface: type):
        if not self.dependencies.get(interface):
            raise InterfaceNotRegistered(
                f"Interface {interface.__name__} not found in container")

    def Resolve(self, interface: type) -> FastAPIDependable:
        self.CheckIfRegistered(interface)
        dependency: Dependency = self.dependencies[interface]
        result: object

        def DependableFunction() -> object:
            return result
        
        def DependableGenerator() -> Generator[object, None, None]:
            yield result

        if dependency.LifeTime is LifeTime.SINGLETON:
            result = dependency.Implementation
            return DependableFunction
        elif dependency.LifeTime is LifeTime.FACTORY:
            result = dependency.Implementation() # pyright: ignore[reportUnknownVariableType, reportCallIssue]
            return DependableFunction
        else:
            result = dependency.Implementation() # pyright: ignore[reportUnknownVariableType, reportCallIssue]
            return DependableGenerator