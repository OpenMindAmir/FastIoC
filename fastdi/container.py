"""
FastDI Container module.

Provides a dependency injection IoC container for registering and resolving
dependencies with different lifetimes (singleton, scoped, factory) in FastAPI.
"""

import inspect
from typing import Any, Callable, Annotated, get_origin, get_args

from typeguard import typechecked
from fastapi.params import Depends
from fastapi import FastAPI, APIRouter

from fastdi.definitions import LifeTime, FastDIConcrete, FastDIDependency, Dependency, DEPENDENCIES
from fastdi.errors import ProtocolNotRegisteredError, SingletonGeneratorNotAllowedError
from fastdi.utils import isAnnotatedWithDepends, pretendSignatureOf

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
    def Injectify(self, target: FastAPI | APIRouter):

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
            >>> container.Injectify(app)
        """

        originalAddAPIRouter: Callable[..., None]

        if isinstance(target, FastAPI):
            if getattr(target.router, '_add_api_route', None):
                originalAddAPIRouter = target.router._add_api_route  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownMemberType]
            else:
                originalAddAPIRouter = target.router.add_api_route
        else:
            if getattr(target, '_add_api_route', None):
                originalAddAPIRouter = target._add_api_route  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownMemberType]
            else:
                originalAddAPIRouter = target.add_api_route

        @pretendSignatureOf(APIRouter.add_api_route)
        def addApiRoute(path: str, endpoint: Callable[..., Any], **kwargs: Any):

            # --- Check Endpoint Params ---

            signature = inspect.signature(endpoint)  # pyright: ignore[reportUnknownArgumentType]
            params: list[inspect.Parameter] = []

            for name, param in signature.parameters.items():  # pyright: ignore[reportUnusedVariable]
                if isinstance(param.default, Depends) or isAnnotatedWithDepends(param.annotation):
                    params.append(param)
                    continue
                if annotatedDependency := self._getAnnotatedDependencyIfRegistered(param.annotation):
                    newParam = param.replace(default=annotatedDependency)
                    params.append(newParam)
                    continue
                try:
                    newParam = param.replace(default=self.Resolve(param.annotation))
                    params.append(newParam)

                except ProtocolNotRegisteredError:
                    params.append(param)

            endpoint.__signature__ = signature.replace(parameters=params)  # pyright: ignore[reportFunctionMemberAccess]


            # --- Route Level Dependencies ---

            dependencies: list[Depends] = []
            
            for dependency in kwargs.get(DEPENDENCIES) or []:  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                self._injectToList(dependencies, dependency)

            kwargs[DEPENDENCIES] = dependencies

            originalAddAPIRouter(path, endpoint, **kwargs)
        
        if isinstance(target, FastAPI):
            target.router.add_api_route = addApiRoute  # pyright: ignore[reportAttributeAccessIssue]
            target.router._add_api_route = originalAddAPIRouter  # pyright: ignore[reportAttributeAccessIssue]
        else:
            target.add_api_route = addApiRoute  # pyright: ignore[reportAttributeAccessIssue]
            target._add_api_route = originalAddAPIRouter  # pyright: ignore[reportAttributeAccessIssue]
            

    # --- Register & Resolve ---

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

        dependency: Dependency[Any] | None = self.BeforeRegisterHook(Dependency[Any](protocol, concrete, lifeTime))   # pyright: ignore[reportArgumentType]
        if dependency:
            protocol = dependency.protocol
            concrete = dependency.concrete
            lifeTime = dependency.lifeTime

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


    def Resolve(self, protocol: type) -> Depends:

        """Return the Depends instance for a protocol. Raises ProtocolNotRegisteredError if not registered."""
        
        self.CheckIfRegistered(protocol)
        dependency: Depends = self.dependencies[protocol]

        if hookedDependency := self.BeforeResolveHook(dependency):
            return hookedDependency
        
        return dependency
    
    
    @typechecked
    def CheckIfRegistered(self, protocol: type):

        """Raises ProtocolNotRegisteredError if the protocol is not registered."""

        if not self.dependencies.get(protocol):
            raise ProtocolNotRegisteredError(
                f"Protocol {protocol.__name__} is not registered in the container")
        

    # --- Registeration sugar methods ---   
    
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


    # --- Internal helper functions
    
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
                if annotatedDependency := self._getAnnotatedDependencyIfRegistered(param.annotation):
                    newParam = param.replace(default=annotatedDependency)
                    params.append(newParam)
                    continue
                try:
                    newParam = param.replace(default=self.Resolve(annotation))
                    params.append(newParam)
                except ProtocolNotRegisteredError:
                    params.append(param)
        concrete.__signature__ = signature.replace(parameters=params)  # pyright: ignore[reportFunctionMemberAccess]

        return concrete
    

    def _injectToList(self, _list: list[Any], item: Any):

        """
        Append a dependency-like item into a list.

        - If `item` is a `Depends` or annotated with `Depends`, append as-is.
        - Otherwise try to resolve it from the container and append the resolved `Depends`.
        - If the type is not registered in the container, append the item itself.
        """

        if isinstance(item, Depends) or isAnnotatedWithDepends(item):
            _list.append(item)
            return

        try:
            dependency: Depends = self.Resolve(item)
            _list.append(dependency)

        except ProtocolNotRegisteredError:
            _list.append(item)
    

    def _processDependenciesList(self, dependencies: list[FastDIDependency]) -> list[Depends]:

        """
        Process a list of global dependencies.

        - Iterates over the given dependencies.
        - Converts each item into a FastAPI-compatible `Depends` using the container.
        - Returns the processed list.
        """

        _list: list[Depends] = []
        for dependency in dependencies:
            self._injectToList(_list, dependency)
        return _list
    

    def _getAnnotatedDependencyIfRegistered(self, annotation: Any) -> Depends | None:

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
                        dependency = self.Resolve(extra)
                        break
                    except ProtocolNotRegisteredError:
                        continue
        return dependency
    

    # --- Hooks ---

    def BeforeRegisterHook(self, dependency: Dependency[Any]) -> Dependency[Any]:
        """
        Hook executed **before a dependency is registered** in the container.

        This method allows you to inspect, modify, or validate the dependency 
        before it is stored in the container.

        Args:
            dependency (Dependency[Any]): The dependency instance about to be registered.
                - `dependency.protocol`: The interface or protocol type.
                - `dependency.concrete`: The concrete implementation or factory.
                - `dependency.lifeTime`: The lifetime of the dependency (SINGLETON, SCOPED, FACTORY).

        Returns:
            Dependency[Any]: The (optionally modified) dependency that will actually be registered.

        Usage:
            You can override this method to implement custom logic such as:
            - Logging registration
            - Wrapping the concrete class
            - Validating dependency types
            - Applying decorators or configuration

        Example (monkey patch):

            def my_register_hook(dep):
                print(f"Registering {dep.protocol.__name__} -> {dep.concrete}")
                return dep

            container = Container()
            container.BeforeRegisterHook = my_register_hook  # Monkey patch the hook

            container.AddScoped(IService, Service)
            # Now each register prints info before storing the dependency
        """
        ...

    def BeforeResolveHook(self, dependency: Depends) -> Depends:
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
            container.BeforeResolveHook = my_resolve_hook  # Monkey patch the hook

            # Now, when resolving a dependency:
            resolved_dep = container.Resolve(IService)
            # Each resolve prints info before returning the instance
        """
        ...
