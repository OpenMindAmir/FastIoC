import inspect
from typing import Any, Callable

from fastapi import APIRouter, FastAPI
from fastapi.params import Depends
from typeguard import typechecked

from fastdi.errors import InterfaceNotRegistered
from fastdi.container import Container
from fastdi.utils import injectToList, pretendSignatureOf

@typechecked
def Injectify(target: FastAPI | APIRouter, container: Container):

    originalAddAPIRouter: Callable[..., None]

    if isinstance(target, FastAPI):
        originalAddAPIRouter = target.router.add_api_route
    else:
        originalAddAPIRouter = target.add_api_route

    @pretendSignatureOf(APIRouter.add_api_route)
    def addApiRoute(path: str, endpoint: Callable[..., Any], **kwargs: Any):

        # --- Check Endpoint Params ---

        signature = inspect.signature(endpoint) # pyright: ignore[reportUnknownArgumentType]
        params: list[inspect.Parameter] = []

        for name, param in signature.parameters.items():  # pyright: ignore[reportUnusedVariable]
            if isinstance(param.default, Depends):
                params.append(param)
                continue

            try:
                dependancy: Depends = container.Resolve(param.annotation)
                newParam = param.replace(default=dependancy)
                params.append(newParam)

            except InterfaceNotRegistered:
                params.append(param)

        endpoint.__signature__ = signature.replace(parameters=params) # pyright: ignore[reportFunctionMemberAccess]


        # --- Route Level Dependencies ---

        dependencies: list[Any] = []
        
        for dependancy in kwargs.get('dependencies') or []: # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            injectToList(dependencies, dependancy, container)

        kwargs['dependencies'] = dependencies

        originalAddAPIRouter(path, endpoint, **kwargs)
    
    if isinstance(target, FastAPI):
        target.router.add_api_route = addApiRoute # pyright: ignore[reportAttributeAccessIssue]
        target.router._add_api_route = originalAddAPIRouter # pyright: ignore[reportAttributeAccessIssue]
    else:
        target.add_api_route = addApiRoute # pyright: ignore[reportAttributeAccessIssue]
        target._add_api_route = originalAddAPIRouter # pyright: ignore[reportAttributeAccessIssue]