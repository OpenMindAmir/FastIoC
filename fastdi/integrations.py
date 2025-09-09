"""
FastDI-Enhanced FastAPI Integration

This module provides extended versions of FastAPI and APIRouter with
automatic FastDI dependency injection support. It allows:

- Management of global dependencies via a built-in FastDI Container.
- Developer-friendly DX helpers for registering singleton, scoped, and factory dependencies.
- Seamless integration with existing FastAPI routes and APIRouters without
  requiring manual injection setup.
"""

from typing import Any, cast

from typeguard import typechecked
from fastapi import FastAPI as _FastAPI, APIRouter as _APIRouter

from fastdi.container import Container
from fastdi.injectify import Injectify, DEPENDENCIES
from fastdi.definitions import FastDIConcrete
from fastdi.utils import pretendSignatureOf, processDependenciesList

def init(self: 'FastAPI | APIRouter', container: Container | None, kwargs: dict[Any, Any]) -> dict[Any, Any]:

    """
    Initialize the extended instances for integrations.
    """

    if container:
        self._container = container  # pyright: ignore[reportPrivateUsage]
        if DEPENDENCIES in kwargs and kwargs[DEPENDENCIES]:
            kwargs[DEPENDENCIES] = processDependenciesList(kwargs[DEPENDENCIES], self._container) # pyright: ignore[reportPrivateUsage]
    else:
        self._container = Container() # pyright: ignore[reportPrivateUsage]

    return kwargs

class Injectified:

    """
    Base class providing shared FastDI integration functionality.
    """

    _container: Container

    @property
    def container(self) -> Container:

        """
        Get the FastDI container.

        Returns:
            Container: The container instance used for dependency injection.
        """

        return self._container
    
    @container.setter
    @typechecked
    def container(self, value: Container):

        """
        Set a new FastDI container.

        Args:
            value (Container): A valid FastDI Container instance.

        NOTE:
            Endpoints defined earlier have already been bound to the
            previous container. Only endpoints defined after this call
            will be processed with the new container.
        """

        self._container = value
        Injectify(cast(FastAPI | APIRouter, self), self._container)


    def AddSingleton(self, protocol: type, concrete: FastDIConcrete):
        
        """
        Register a singleton dependency into the internal container.
        One single shared instance will be used throughout the entire process/worker.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            SingletonGeneratorNotAllowedError: If 'concrete' is a generator or async generator.
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self._container.AddSingleton(protocol, concrete)

    def AddScoped(self, protocol: type, concrete: FastDIConcrete):

        """
        Register a request-scoped dependency into the internal container.
        A new instance is created for each HTTP request and reused throughout that request.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self._container.AddScoped(protocol, concrete)

    def AddFactory(self, protocol: type, concrete: FastDIConcrete):

        """
        Register a factory (transient) dependency into the internal container.
        A new instance is created each time the dependency is resolved.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            concrete (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self._container.AddFactory(protocol, concrete)


class FastAPI(_FastAPI, Injectified):

    """
    Extended FastAPI class with automatic FastDI integration.

    Features:
        - Supports global dependencies via an internal FastDI Container.
          A default container is created automatically, but it can be replaced via the `container` property.
        - Lazy injection of dependencies into route endpoints.
        - Developer-friendly DX sugar:
            - `AddGlobalDependency` to add a single global dependency.
            - `AddSingleton`, `AddScoped`, `AddFactory` to register dependencies in the container.
        - Global and route-level dependencies are automatically processed.
    """

    @pretendSignatureOf(_FastAPI.__init__)
    def __init__(self, *args: Any, container: Container | None = None, **kwargs: Any):

        """
        Initialize the extended FastAPI instance.
        """

        kwargs = init(self, container, kwargs)

        super().__init__(*args, **kwargs)

        Injectify(self, self._container) # pyright: ignore[reportPrivateUsage]

class APIRouter(_APIRouter, Injectified):

    """
    Extended APIRouter class with automatic FastDI integration.

    Features:
        - Supports global dependencies via an internal FastDI Container.
          A default container is created automatically, but it can be replaced via the `container` property.
        - Lazy injection of dependencies into route endpoints.
        - Developer-friendly DX sugar:
            - `AddGlobalDependency` to add a single global dependency.
            - `AddSingleton`, `AddScoped`, `AddFactory` to register dependencies in the container.
        - Global and route-level dependencies are automatically processed.
    """

    @pretendSignatureOf(_APIRouter.__init__)
    def __init__(self, *args: Any, container: Container | None = None, **kwargs: Any):

        """
        Initialize the extended APIRouter instance.
        """

        kwargs = init(self, container, kwargs)

        super().__init__(*args, **kwargs)

        Injectify(self, self._container) # pyright: ignore[reportPrivateUsage]
