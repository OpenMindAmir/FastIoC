import inspect
from typing import Any, Callable
from functools import wraps

from fastapi import FastAPI, APIRouter, Depends
from fastapi.params import Depends as _Depends
from typeguard import typechecked

from fastdi.errors import InterfaceNotRegistered
from fastdi.custom_types import FastAPIDependable
from fastdi.container import Container

def inject(_list: list[Any], item: Any, container: Container):
    if isinstance(item, _Depends):
        _list.append(item)
        return

    try:
        dependable: FastAPIDependable = container.Resolve(item)
        _list.append(Depends(dependable))

    except InterfaceNotRegistered:
        _list.append(item)

safeAttrs = [
        "routes",
        "dependencies",
        "prefix",
        "tags",
        "responses",
        "default_response_class",
        "deprecated",
        "include_in_schema",
        "redirect_slashes",
        "default",
        "on_startup",
        "on_shutdown",
        "exception_handlers",
        "route_class",
    ]

def cloneRouter(router: APIRouter, newRouter: type[APIRouter]) -> APIRouter:
    _newRouter = newRouter()
    for key in safeAttrs:
        setattr(_newRouter, key, getattr(router, key, None))
    return _newRouter 

@typechecked
def Injectify(app: FastAPI, container: Container):
    originalRouter: APIRouter = app.router
    originalIncludeRouter: Callable = app.include_router # pyright: ignore[reportMissingTypeArgument]

    class AutoWireRouter(APIRouter):
        def add_api_route(self, path: str, endpoint: Callable, **kwargs): # pyright: ignore[reportMissingTypeArgument, reportMissingParameterType, reportUnknownParameterType]

            # --- Check Endpoint Params ---

            signature = inspect.signature(endpoint) # pyright: ignore[reportUnknownArgumentType]
            params: list[inspect.Parameter] = []

            for name, param in signature.parameters.items():  # pyright: ignore[reportUnusedVariable]
                if isinstance(param.default, _Depends):
                    params.append(param)
                    continue

                try:
                    dependable: FastAPIDependable = container.Resolve(param.annotation)
                    newParam = param.replace(default=Depends(dependable))
                    params.append(newParam)

                except InterfaceNotRegistered:
                    params.append(param)

            endpoint.__signature__ = signature.replace(parameters=params) # pyright: ignore[reportFunctionMemberAccess]


            # --- Route Level Dependencies ---

            dependencies: list[Any] = []
            
            for dependancy in kwargs.get('dependencies') or []: # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                inject(dependencies, dependancy, container)

            kwargs['dependencies'] = dependencies

            return super().add_api_route(path, endpoint, **kwargs) # pyright: ignore[reportUnknownArgumentType]
    
    newRouter = cloneRouter(originalRouter, AutoWireRouter)
    app.router = newRouter

    @wraps(originalIncludeRouter) # pyright: ignore[reportUnknownArgumentType]
    def patchedIncludeRouter(router: APIRouter, *args, **kwargs): # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]

        # --- Router Level Dependencies ---

        if not isinstance(router, AutoWireRouter):
            router = cloneRouter(router, AutoWireRouter)
            dependencies: list[Any] = []
            for dependency in getattr(router, 'dependencies', []):
                inject(dependencies, dependency, container)

            router.dependencies = dependencies

        return originalIncludeRouter(router, *args, **kwargs) # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    
    app.include_router = patchedIncludeRouter

    # Save original versions for debug
    app._router = originalRouter # pyright: ignore[reportAttributeAccessIssue]
    app._include_router = originalIncludeRouter # pyright: ignore[reportAttributeAccessIssue]

    # --- App Level Dependencies ---

    dependencies: list[Any] = []
    for dependency in getattr(app, 'dependencies', []):
        inject(dependencies, dependency, container)
    
    app.dependencies = dependencies # pyright: ignore[reportAttributeAccessIssue]