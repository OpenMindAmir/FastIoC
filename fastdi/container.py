import inspect
from typing import Callable, Any

from typeguard import typechecked
from fastapi.params import Depends

from fastdi.definitions import LifeTime
from fastdi.errors import ProtocolNotRegisteredError, SingletonGeneratorNotAllowedError


class Container:

    def __init__(self):
        self.dependencies: dict[type, Depends] = {}

    @typechecked
    def Register(self, protocol: type, concrete: type | Callable[..., Any], lifeTime: LifeTime):
        if lifeTime is LifeTime.SINGLETON:
            conc = concrete()
            if inspect.isgenerator(conc) or inspect.isasyncgen(conc):
                raise SingletonGeneratorNotAllowedError('Cannot register Generators or AsyncGenerators as Singleton dependencies.')
            def provideSingleton() -> Any:
                return conc
            self.dependencies[protocol] = Depends(dependency=provideSingleton, use_cache=True)
        else:
            self.dependencies[protocol] = Depends(dependency=concrete, use_cache = False if lifeTime is LifeTime.FACTORY else True)


    def AddSingleton(self, protocol: type, concrete: type):
        self.Register(protocol, concrete, LifeTime.SINGLETON)

    def AddScoped(self, protocol: type, concrete: type):
        self.Register(protocol, concrete, LifeTime.SCOPED)

    def AddFactory(self, protocol: type, concrete: type):
        self.Register(protocol, concrete, LifeTime.FACTORY)

    @typechecked
    def CheckIfRegistered(self, protocol: type):
        if not self.dependencies.get(protocol):
            raise ProtocolNotRegisteredError(
                f"Protocol {protocol.__name__} is not registered in the container")

    def Resolve(self, protocol: type) -> Depends:
        self.CheckIfRegistered(protocol)
        return self.dependencies[protocol]