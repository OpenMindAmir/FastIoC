"""
FastDI Container module.

Provides a dependency injection IoC container for registering and resolving
dependencies with different lifetimes (singleton, scoped, factory) in FastAPI.
"""

import inspect
from inspect import Parameter, Signature
from typing import Any, Callable, Annotated, Optional, get_origin, get_args, cast, get_type_hints
from functools import wraps

from typeguard import typechecked, TypeCheckError
from fastapi.params import Depends
from fastapi import FastAPI, APIRouter

from fastdi.definitions import LifeTime, FastDIConcrete, FastDIDependency, Dependency, DEPENDENCIES
from fastdi.errors import ProtocolNotRegisteredError, SingletonGeneratorNotAllowedError
from fastdi.utils import is_annotated_with_depends, pretend_signature_of


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


    # --- Injectify ---

    @typechecked
    def injectify(self, target: FastAPI | APIRouter):

        """
        Wrap a FastAPI app or APIRouter to automatically inject dependencies.

        THIS MUST BE CALLED BEFORE ADDING ANY ENDPOINTS THAT REQUIRE DEPENDENCY INJECTION.

        This function overrides `add_api_route` to:
            - Inject dependencies into endpoint parameters using the provided container.
            - Resolve route-level dependencies automatically.
            - Support both FastAPI application and APIRouter instances.

        Args:
            target (FastAPI | APIRouter): The FastAPI app or APIRouter to wrap.

        Example:
            >>> app = FastAPI()
            >>> container = Container()
            >>> container.injectify(app)
        """

        original_add_api_route: Callable[..., None]

        if isinstance(target, FastAPI):
            if getattr(target.router, '_add_api_route', None):
                original_add_api_route = target.router._add_api_route  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownMemberType]
            else:
                original_add_api_route = target.router.add_api_route
        else:
            if getattr(target, '_add_api_route', None):
                original_add_api_route = target._add_api_route  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownMemberType]
            else:
                original_add_api_route = target.add_api_route

        @pretend_signature_of(APIRouter.add_api_route)
        def injective_add_api_route(path: str, endpoint: Callable[..., Any], **kwargs: Any):

            # --- Check Endpoint Params ---

            signature = inspect.signature(endpoint)  # pyright: ignore[reportUnknownArgumentType]
            params: list[inspect.Parameter] = []

            for name, param in signature.parameters.items():  # pyright: ignore[reportUnusedVariable]
                if isinstance(param.default, Depends) or is_annotated_with_depends(param.annotation):
                    params.append(param)
                    continue
                if annotated_dependency := self._get_annotated_dependency_if_registered(param.annotation):
                    new_param = param.replace(default=annotated_dependency)
                    params.append(new_param)
                    continue
                try:
                    new_param = param.replace(default=self.resolve(param.annotation))
                    params.append(new_param)

                except ProtocolNotRegisteredError:
                    params.append(param)

            endpoint.__signature__ = signature.replace(parameters=params)  # pyright: ignore[reportFunctionMemberAccess]


            # --- Route Level Dependencies ---

            dependencies: list[Depends] = []
            
            for dependency in kwargs.get(DEPENDENCIES) or []:  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                self._inject_to_list(dependencies, dependency)

            kwargs[DEPENDENCIES] = dependencies

            original_add_api_route(path, endpoint, **kwargs)
        
        if isinstance(target, FastAPI):
            target.router.add_api_route = injective_add_api_route  # pyright: ignore[reportAttributeAccessIssue]
            target.router._add_api_route = original_add_api_route  # pyright: ignore[reportAttributeAccessIssue]
        else:
            target.add_api_route = injective_add_api_route  # pyright: ignore[reportAttributeAccessIssue]
            target._add_api_route = original_add_api_route  # pyright: ignore[reportAttributeAccessIssue]
            

    # --- Register & Resolve ---

    @typechecked
    def register(self, protocol: type, implementation: FastDIConcrete, lifetime: LifeTime):

        """
        Register a dependency with a given lifetime.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.
            lifetime (Lifetime): SINGLETON, SCOPED, or FACTORY.

        Raises:
            SingletonGeneratorNotAllowedError: If a generator or async generator is registered as singleton.
        """

        dependency: Dependency[Any] | None = self.before_register_hook(Dependency[Any](protocol, implementation, lifetime))   # pyright: ignore[reportArgumentType]
        if dependency:
            protocol = dependency.protocol
            implementation = dependency.implementation
            lifetime = dependency.lifetime

        implementation = self._nested_injector(implementation)
        if lifetime is LifeTime.SINGLETON:
            impl = implementation()
            if inspect.isgenerator(impl) or inspect.isasyncgen(impl):
                raise SingletonGeneratorNotAllowedError('Cannot register Generators or AsyncGenerators as Singleton dependencies.')
            def singleton_provider() -> Any:
                return impl
            self.dependencies[protocol] = Depends(dependency=singleton_provider, use_cache=True)
        else:
            self.dependencies[protocol] = Depends(dependency=implementation, use_cache = False if lifetime is LifeTime.FACTORY else True)


    def resolve(self, protocol: type) -> Depends:

        """Return the Depends instance for a protocol. Raises ProtocolNotRegisteredError if not registered."""
        
        self.check_if_registered(protocol)
        dependency: Depends = self.dependencies[protocol]

        if hooked_dependency := self.before_resolve_hook(dependency):
            return hooked_dependency
        
        return dependency
    
    
    @typechecked
    def check_if_registered(self, protocol: type):

        """Raises ProtocolNotRegisteredError if the protocol is not registered."""

        if not self.dependencies.get(protocol):
            raise ProtocolNotRegisteredError(
                f"Protocol {protocol.__name__} is not registered in the container")
        

    # --- Registeration sugar methods ---   
    
    def add_singleton(self, protocol: type, implementation: FastDIConcrete):

        """
        Register a singleton dependency.

        One single shared instance will be used throughout the entire process/worker.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            SingletonGeneratorNotAllowedError: If 'implementation' is a generator or async generator.
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self.register(protocol, implementation, LifeTime.SINGLETON)


    def add_scoped(self, protocol: type, implementation: FastDIConcrete):

        """
        Register a request-scoped dependency.

        A new instance is created for each HTTP request and reused throughout that request.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self.register(protocol, implementation, LifeTime.SCOPED)


    def add_factory(self, protocol: type, implementation: FastDIConcrete):

        """
        Register a factory (transient) dependency.

        A new instance is created each time the dependency is resolved.

        Args:
            protocol (type): The interface or protocol type that acts as the key for resolving this dependency.
            implementation (FastDIConcrete): The actual implementation to be provided when the protocol is resolved.

        Raises:
            ProtocolNotRegisteredError: If a nested dependency is not registered.
        """

        self.register(protocol, implementation, LifeTime.FACTORY)

    # --- Override

    def override(self, dependencies: dict[Callable[..., Any], Callable[..., Any]] = {}, container: Optional['Container'] = None) -> dict[Callable[..., Any], Callable[..., Any]]:

        """
        Generate an updated dictionary suitable for FastAPI's `dependency_overrides`.

        This method allows merging and overriding dependencies from two sources:
        1. A dictionary of user-provided overrides.
        2. An optional secondary FastDI container (e.g., a mock container for testing).

        NOTE: The lifetime of each dependency is preserved: 
        overridden dependencies are injected with the SAME LIFETIME AS ORIGINAL CONTAINER REGISTERATION.

        Parameters:
            dependencies (dict[Callable[..., Any], Callable[..., Any]]):
                A dictionary where keys are the original dependency callables or
                protocol types that may have been registered in the container,
                and values are the new callables that should override them.

                - If a key is registered in the container, it will be replaced
                with the registered dependancy,
                while the value remains the provided override callable.
                - Keys not registered in the container are left unchanged.
                - This means you can mix normal FastAPI overrides with container-based
                dependencies without conflict.

            container (Optional[Container]):
                An optional secondary container (e.g., a test or mock container).
                - For each protocol in this container that is also registered in
                the main container, the resolved dependency from the main container
                will be used as the key, and the dependency from the secondary
                container will be used as the value.
                - Protocols in the secondary container that are not registered
                in the main container are ignored.
                - NOTE: The lifetime of each dependency should follow the main container, unless you know exactly what you are doing. 
                    - - For SCOPED or FACTORY dependencies in the main container, the original lifetime is always preserved regardless of what is registered in the secondary container (except SINGLETON). 
                    - - For SINGLETON dependencies in the main container: if the main container has SINGLETON and the secondary container has a different lifetime, the resulting lifetime will be SCOPED; 
                    - - If the main container has a non-SINGLETON lifetime and the secondary container registers it as SINGLETON, the resulting lifetime will be SINGLETON.

        Returns:
            dict[Callable[..., Any] | Depends, Callable[..., Any]]:
                A new dictionary suitable for assigning to
                `app.dependency_overrides`.

        Example:
            >>> from fastdi import Container, FastAPI
            >>> app = FastAPI()
            >>> container = Container()
            >>> container.add_scoped(IService, Service)
            >>> overrides = {
            ...     IService: MockService,
            ...     some_dependency: custom_callable
            ... }
            >>> app.dependency_overrides.update(container.override(overrides))
        """

        for key, value in dependencies.items():
            original = key
            try:
                original = cast(Callable[..., Any], self.resolve(cast(type, key)).dependency)
                dependencies |= {original: value}
            except (ProtocolNotRegisteredError, TypeCheckError):
                pass
        
        if container:
            for key, value in container.dependencies.items():
                try:
                    original = cast(Callable[..., Any], self.resolve(key).dependency)
                    dependencies |= {original: cast(Callable[..., Any], value.dependency)}
                except:
                    pass

        return dependencies


    # --- Internal helper functions
    
    @typechecked
    def _nested_injector(self, implementation: FastDIConcrete) -> FastDIConcrete:

        """
        Inject dependencies into class or callable signatures automatically.
        Used to inject dependencies of a dependency
        """

        signature: Signature = inspect.signature(implementation.__init__) if inspect.isclass(implementation) else inspect.signature(implementation)
        hints: Optional[dict[str, Any]] = get_type_hints(implementation) if inspect.isclass(implementation) else None
        params: list[Parameter] = []
        for name, param in signature.parameters.items():
            if name == 'self':
                continue
            annotation = param.annotation
            if annotation != Signature.empty:
                if isinstance(param.default, Depends) or is_annotated_with_depends(annotation):
                    params.append(param)
                    continue
                if annotated_dependency := self._get_annotated_dependency_if_registered(param.annotation):
                    new_param = param.replace(default=annotated_dependency)
                    params.append(new_param)
                    continue
                try:
                    new_param = param.replace(default=self.resolve(annotation))
                    params.append(new_param)
                except ProtocolNotRegisteredError:
                    params.append(param)
        if hints:
            original_init = implementation.__init__
            @wraps(original_init) # pyright: ignore[reportArgumentType]
            def __init__(_self: object, *args: Any, **kwargs: Any):
                original_init(_self, *args, **kwargs)  # pyright: ignore[reportCallIssue]

                for name, annotation in hints.items():
                    if hasattr(_self, name):
                        continue
                    try:
                        setattr(_self, name, self.resolve(annotation))
                    except ProtocolNotRegisteredError:
                        pass
            implementation.__init__ = __init__  # pyright: ignore[reportFunctionMemberAccess]
        implementation.__signature__ = signature.replace(parameters=params)  # pyright: ignore[reportFunctionMemberAccess]

        return implementation
    

    def _inject_to_list(self, _list: list[Any], item: Any):

        """
        Append a dependency-like item into a list.

        - If `item` is a `Depends` or annotated with `Depends`, append as-is.
        - Otherwise try to resolve it from the container and append the resolved `Depends`.
        - If the type is not registered in the container, append the item itself.
        """

        if isinstance(item, Depends) or is_annotated_with_depends(item):
            _list.append(item)
            return

        try:
            dependency: Depends = self.resolve(item)
            _list.append(dependency)

        except ProtocolNotRegisteredError:
            _list.append(item)
    

    def _process_dependencies_list(self, dependencies: list[FastDIDependency]) -> list[Depends]:

        """
        Process a list of global dependencies.

        - Iterates over the given dependencies.
        - Converts each item into a FastAPI-compatible `Depends` using the container.
        - Returns the processed list.
        """

        _list: list[Depends] = []
        for dependency in dependencies:
            self._inject_to_list(_list, dependency)
        return _list
    

    def _get_annotated_dependency_if_registered(self, annotation: Any) -> Depends | None:

        """
        Attempts to resolve a dependency from the container if the given annotation
        is an Annotated type with a registered dependency.

        Returns the first resolved dependency if found (stops at the first match),
        otherwise None.
        """

        dependency = None
        if get_origin(annotation) is Annotated:
            mainType, *extras = get_args(annotation)  # pyright: ignore[reportUnusedVariable]
            for extra in extras:
                if isinstance(extra, type):
                    try:
                        dependency = self.resolve(extra)
                        break
                    except ProtocolNotRegisteredError:
                        continue
        return dependency
    

    # --- Hooks ---

    def before_register_hook(self, dependency: Dependency[Any]) -> Dependency[Any]:
        """
        Hook executed **before a dependency is registered** in the container.

        This method allows you to inspect, modify, or validate the dependency 
        before it is stored in the container.

        Args:
            dependency (Dependency[Any]): The dependency instance about to be registered.
                - `dependency.protocol`: The interface or protocol type.
                - `dependency.implementation`: The implementation implementation or factory.
                - `dependency.lifetime`: The lifetime of the dependency (SINGLETON, SCOPED, FACTORY).

        Returns:
            Dependency[Any]: The (optionally modified) dependency that will actually be registered.

        Usage:
            You can override this method to implement custom logic such as:
            - Logging registration
            - Wrapping the implementation class
            - Validating dependency types
            - Applying decorators or configuration

        Example (monkey patch):

            def my_register_hook(dep):
                print(f"Registering {dep.protocol.__name__} -> {dep.implementation}")
                return dep

            container = Container()
            container.before_register_hook = my_register_hook  # Monkey patch the hook

            container.add_scoped(IService, Service)
            # Now each register prints info before storing the dependency
        """
        ...

    def before_resolve_hook(self, dependency: Depends) -> Depends:
        """
        Hook executed **before a dependency is resolved** from the container.

        This method allows you to inspect, wrap, or modify the dependency
        just before it is provided to a consumer (endpoint, service, etc).

        Args:
            dependency (Depends): The FastAPI Depends instance representing the dependency 
                about to be resolved.
                - `dependency.dependency`: The callable that will produce the actual instance.
                - `dependency.use_cache`: Whether the instance should be cached for reuse.

        Returns:
            Depends: The (optionally modified) Depends instance to be used in resolution.

        Usage:
            You can override this method to implement custom logic such as:
            - Logging resolution
            - Wrapping the callable with additional behavior
            - Injecting default parameters
            - Applying metrics or tracing

        Example (monkey patch):

            def my_resolve_hook(dep):
                print(f"Resolving dependency {dep.dependency.__name__}")
                return dep

            container = Container()
            container.before_resolve_hook = my_resolve_hook  # Monkey patch the hook

            # Now, when resolving a dependency:
            resolved_dep = container.resolve(IService)
            # Each resolve prints info before returning the instance
        """
        ...
