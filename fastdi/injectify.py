import inspect
from typing import Any, Callable

from fastapi import APIRouter, Depends, FastAPI
from fastapi.params import Depends as _Depends
from typeguard import typechecked

from fastdi.errors import InterfaceNotRegistered
from fastdi.custom_types import FastAPIDependable
from fastdi.container import Container
from fastdi.utils import injectToList


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
                injectToList(dependencies, dependancy, container)

            kwargs['dependencies'] = dependencies

            return super().add_api_route(path, endpoint, **kwargs) # pyright: ignore[reportUnknownArgumentType]
    
    newRouter = cloneRouter(originalRouter, AutoWireRouter)
    app.router = newRouter

    # Save original versions for debug
    app._router = originalRouter # pyright: ignore[reportAttributeAccessIssue]