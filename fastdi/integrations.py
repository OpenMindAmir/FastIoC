"""
FastDI-Enhanced FastAPI Integration

This module provides extended versions of FastAPI and APIRouter with
automatic FastDI dependency injection support. It allows:

- Management of global dependencies via a built-in FastDI Container.
- Developer-friendly DX helpers for registering singleton, request-scoped, and transient dependencies.
- Seamless integration with existing FastAPI routes and APIRouters without
  requiring manual injection setup.
"""

from typing import Any, Optional, cast, Callable

from typeguard import typechecked
from fastapi import FastAPI as _FastAPI, APIRouter as _APIRouter

from fastdi.container import Container
from fastdi.definitions import FastDIConcrete, DEPENDENCIES
from fastdi.utils import pretend_signature_of

def init(self: 'FastAPI | APIRouter', container: Container | None, kwargs: dict[Any, Any]) -> dict[Any, Any]:

    """
    Initialize the extended instances for integrations.
    """

    if container:
        self._container = container  # pyright: ignore[reportPrivateUsage]
        if DEPENDENCIES in kwargs and kwargs[DEPENDENCIES]:
            kwargs[DEPENDENCIES] = self._container._process_dependencies_list(kwargs[DEPENDENCIES]) # pyright: ignore[reportPrivateUsage]
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
        self._container.injectify(cast(FastAPI | APIRouter, self))

    def add_singleton(self, protocol: type, implementation: FastDIConcrete):
        
        """
        Register a singleton dependency into the internal container.

        One single shared instance will be used throughout the entire process/worker.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            SingletonGeneratorNotAllowedError: If 'implementation' is a generator or async generator.
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self._container.add_singleton(protocol, implementation)

    def add_scoped(self, protocol: type, implementation: FastDIConcrete):

        """
        Register a request-scoped dependency into the internal container.

        A new instance is created for each HTTP request and reused throughout that request.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self._container.add_scoped(protocol, implementation)

    def add_transient(self, protocol: type, implementation: FastDIConcrete):

        """
        Register a transient dependency into the internal container.
        
        A new instance is created each time the dependency is resolved.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self._container.add_transient(protocol, implementation)

    def override_dependencies(self, dependencies: dict[Callable[..., Any], Callable[..., Any]] = {}, container: Optional['Container'] = None):

        """
        Override dependencies in a FastAPI app using the integrated FastDI container.

        This method merges user-provided overrides with the container’s registered dependencies
        and **directly updates** the app’s `dependency_overrides`.
        The original lifetime of each dependency is preserved.

        Parameters:
            dependencies (dict[Callable[..., Any], Callable[..., Any]]):
                Mapping from original dependency callables or protocol types to override callables.

            container (Optional[Container]):
                An optional secondary container (e.g., for testing or mocking).
                Only protocols registered in the main container are considered.
                - NOTE: The lifetime of each dependency should follow the main container, unless you know exactly what you are doing. 
                    - - For SCOPED or FACTORY dependencies in the main container, the original lifetime is always preserved regardless of what is registered in the secondary container (except SINGLETON). 
                    - - For SINGLETON dependencies in the main container: if the main container has SINGLETON and the secondary container has a different lifetime, the resulting lifetime will be SCOPED; 
                    - - If the main container has a non-SINGLETON lifetime and the secondary container registers it as SINGLETON, the resulting lifetime will be SINGLETON.
                    
        Example:
            >>> from fastdi import FastAPI
            >>> app = FastAPI()
            >>> app.add_scoped(IService, Service)
            >>> overrides = {
            ...     IService: MockService,
            ...     some_dependency: custom_callable
            ... }
            >>> app.override_dependencies(overrides)
        """

        self.dependency_overrides.update(self._container.override(dependencies, container))  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]

    async def dispose(self):

        """
        Dispose all registered singleton dependencies.

        This method calls the disposal function of each singleton that was registered
        in the container. Both synchronous and asynchronous disposal functions are supported.
        If a disposal function raises an exception, it will be caught and logged, and
        the disposal process will continue for the remaining singletons.

        Logging format:
            'Error disposing "ClassName": exception'

        Notes:
            - Async disposal functions will be awaited.
            - Errors during disposal do not prevent other singletons from being disposed.
        """

        await self._container.dispose()
class FastAPI(_FastAPI, Injectified):

    """
    Extended FastAPI class with automatic FastDI integration.

    Features:
        - Supports global dependencies via an internal FastDI Container.
          A default container is created automatically, but it can be replaced via the `container` property.
        - Lazy injection of dependencies into route endpoints.
        - Developer-friendly DX sugar:
            - `add_singleton`, `add_scoped`, `add_transient` to register dependencies in the container.
        - Global and route-level dependencies are automatically processed.
    """

    @pretend_signature_of(_FastAPI.__init__)
    def __init__(self, *args: Any, container: Optional[Container] = None, **kwargs: Any):

        """
        Initialize the extended FastAPI instance.
        """

        kwargs = init(self, container, kwargs)

        super().__init__(*args, **kwargs)

        self._container.injectify(self)

class APIRouter(_APIRouter, Injectified):

    """
    Extended APIRouter class with automatic FastDI integration.

    Features:
        - Supports global dependencies via an internal FastDI Container.
          A default container is created automatically, but it can be replaced via the `container` property.
        - Lazy injection of dependencies into route endpoints.
        - Developer-friendly DX sugar:
            - `add_singleton`, `add_scoped`, `add_transient` to register dependencies in the container.
        - Global and route-level dependencies are automatically processed.
    """

    @pretend_signature_of(_APIRouter.__init__)
    def __init__(self, *args: Any, container: Container | None = None, **kwargs: Any):

        """
        Initialize the extended APIRouter instance.
        """

        kwargs = init(self, container, kwargs)

        super().__init__(*args, **kwargs)

        self._container.injectify(self)
