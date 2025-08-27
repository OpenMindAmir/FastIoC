from typing import Generator, AsyncGenerator , Callable, Any

from typeguard import typechecked
from fastapi.params import Depends

from fastdi.custom_types import LifeTime
from fastdi.errors import InterfaceNotRegistered


class Container:

    def __init__(self):
        self.dependencies: dict[type, Depends] = {}

    @typechecked
    def Register(self, protocol: type, implementation: type | Callable[..., Any], lifeTime: LifeTime):
        impl = implementation
        if lifeTime is LifeTime.SINGLETON:
            impl = implementation()
            def injectSingleton() -> object:
                return impl
            self.dependencies[protocol] = Depends(dependency=injectSingleton)
        else:
            self.dependencies[protocol] = Depends(dependency=implementation, use_cache = False if lifeTime is LifeTime.FACTORY else True)


    def AddSingleton(self, interface: type, implementation: type):
        self.Register(interface, implementation, LifeTime.SINGLETON)

    def AddScoped(self, interface: type, implementation: type):
        self.Register(interface, implementation, LifeTime.SCOPED)

    def AddFactory(self, interface: type, implementation: type):
        self.Register(interface, implementation, LifeTime.FACTORY)

    def AddContext(self, protocol: type, implementation: Callable[..., Generator[Any, None, None] | AsyncGenerator[Any, None] ]):
        self.Register(protocol, implementation, LifeTime.CONTEXT)

    @typechecked
    def CheckIfRegistered(self, protocol: type):
        if not self.dependencies.get(protocol):
            raise InterfaceNotRegistered(
                f"Interface/Protocol {protocol.__name__} not found in container")

    def Resolve(self, protocol: type) -> Depends:
        self.CheckIfRegistered(protocol)
        return self.dependencies[protocol]