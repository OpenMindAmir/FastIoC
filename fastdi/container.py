import inspect
from typing import Any

from typeguard import typechecked
from fastapi.params import Depends

from fastdi.definitions import LifeTime, FastDIConcrete
from fastdi.errors import ProtocolNotRegisteredError, SingletonGeneratorNotAllowedError
from fastdi.utils import isAnnotatedWithDepends

class Container:

    def __init__(self):
        self.dependencies: dict[type, Depends] = {}

    @typechecked
    def Register(self, protocol: type, concrete: FastDIConcrete, lifeTime: LifeTime):
        concrete = self._layeredInjector(concrete)
        if lifeTime is LifeTime.SINGLETON:
            conc = concrete()
            if inspect.isgenerator(conc) or inspect.isasyncgen(conc):
                raise SingletonGeneratorNotAllowedError('Cannot register Generators or AsyncGenerators as Singleton dependencies.')
            def provideSingleton() -> Any:
                return conc
            self.dependencies[protocol] = Depends(dependency=provideSingleton, use_cache=True)
        else:
            self.dependencies[protocol] = Depends(dependency=concrete, use_cache = False if lifeTime is LifeTime.FACTORY else True)


    def AddSingleton(self, protocol: type, concrete: FastDIConcrete):
        self.Register(protocol, concrete, LifeTime.SINGLETON)

    def AddScoped(self, protocol: type, concrete: FastDIConcrete):
        self.Register(protocol, concrete, LifeTime.SCOPED)

    def AddFactory(self, protocol: type, concrete: FastDIConcrete):
        self.Register(protocol, concrete, LifeTime.FACTORY)


    @typechecked
    def CheckIfRegistered(self, protocol: type):
        if not self.dependencies.get(protocol):
            raise ProtocolNotRegisteredError(
                f"Protocol {protocol.__name__} is not registered in the container")

    def Resolve(self, protocol: type) -> Depends:
        self.CheckIfRegistered(protocol)
        return self.dependencies[protocol]
    
    @typechecked
    def _layeredInjector(self, concrete: FastDIConcrete) -> FastDIConcrete:
        signature: inspect.Signature = inspect.signature(concrete.__init__) if inspect.isclass(concrete) else inspect.signature(concrete)
        params: list[inspect.Parameter] = []
        for name, param in signature.parameters.items():
            if name == 'self':
                continue
            annotation = param.annotation
            if annotation != inspect.Signature.empty:
                if isinstance(param.default, Depends) or isAnnotatedWithDepends(annotation):
                    params.append(param)
                    continue
                try:
                    newParam = param.replace(default=self.Resolve(annotation))
                    params.append(newParam)
                except ProtocolNotRegisteredError:
                    params.append(param)
        concrete.__signature__ = signature.replace(parameters=params) # pyright: ignore[reportFunctionMemberAccess]

        return concrete

