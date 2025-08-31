"""
FastDI Container module.

Provides a dependency injection IoC container for registering and resolving
dependencies with different lifetimes (singleton, scoped, factory) in FastAPI.
"""

import inspect
from typing import Any

from typeguard import typechecked
from fastapi.params import Depends

from fastdi.definitions import LifeTime, FastDIConcrete
from fastdi.errors import ProtocolNotRegisteredError, SingletonGeneratorNotAllowedError
from fastdi.utils import isAnnotatedWithDepends

class Container:

    """
    Dependency Injection IoC container for registering and resolving dependencies 
    in FastAPI applications.

    Supports three lifetimes:
        - Singleton: One single shared instance per process/worker.
        - Scoped: One instance per HTTP request, reused during that request.
        - Factory: A new instance each time the dependency is resolved.

    Attributes:
        dependencies (dict[type, Depends]): Maps protocol types to FastAPI Depends instances.
    """

    def __init__(self):

        """Initialize an empty dependency container."""

        self.dependencies: dict[type, Depends] = {}

    @typechecked
    def Register(self, protocol: type, concrete: FastDIConcrete, lifeTime: LifeTime):

        """
        Register a dependency with a given lifetime.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.
            lifeTime (LifeTime): SINGLETON, SCOPED, or FACTORY.

        Raises:
            SingletonGeneratorNotAllowedError: If a generator or async generator is registered as singleton.
        """

        concrete = self._nestedInjector(concrete)
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

        """
        Register a singleton dependency.
        One single shared instance will be used throughout the entire process/worker.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            SingletonGeneratorNotAllowedError: If 'concrete' is a generator or async generator.
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self.Register(protocol, concrete, LifeTime.SINGLETON)

    def AddScoped(self, protocol: type, concrete: FastDIConcrete):

        """
        Register a request-scoped dependency.
        A new instance is created for each HTTP request and reused throughout that request.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self.Register(protocol, concrete, LifeTime.SCOPED)

    def AddFactory(self, protocol: type, concrete: FastDIConcrete):

        """
        Register a factory (transient) dependency.
        A new instance is created each time the dependency is resolved.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self.Register(protocol, concrete, LifeTime.FACTORY)


    @typechecked
    def CheckIfRegistered(self, protocol: type):

        """Raises ProtocolNotRegisteredError if the protocol is not registered."""

        if not self.dependencies.get(protocol):
            raise ProtocolNotRegisteredError(
                f"Protocol {protocol.__name__} is not registered in the container")

    def Resolve(self, protocol: type) -> Depends:

        """Return the Depends instance for a protocol. Raises ProtocolNotRegisteredError if not registered."""
        
        self.CheckIfRegistered(protocol)
        return self.dependencies[protocol]
    
    @typechecked
    def _nestedInjector(self, concrete: FastDIConcrete) -> FastDIConcrete:

        """
        Inject dependencies into class or callable signatures automatically.
        Used to inject dependencies of a dependency
        """

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
        concrete.__signature__ = signature.replace(parameters=params)  # pyright: ignore[reportFunctionMemberAccess]

        return concrete

