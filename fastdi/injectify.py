"""
FastDI Integration for FastAPI and APIRouter.

Provides automatic dependency injection for route endpoints and route-level
dependencies using a FastDI container. The main function, `Injectify`, wraps
FastAPI or APIRouter to inject registered dependencies based on type annotations.
"""

import inspect
from typing import Any, Callable

from fastapi import APIRouter, FastAPI
from fastapi.params import Depends
from typeguard import typechecked

from fastdi.errors import ProtocolNotRegisteredError
from fastdi.container import Container
from fastdi.utils import injectToList, pretendSignatureOf, isAnnotatedWithDepends, getAnnotatedDependencyIfRegistered


@typechecked
def Injectify(target: FastAPI | APIRouter, container: Container):

    """
    Wrap a FastAPI app or APIRouter to automatically inject dependencies.

    THIS MUST BE CALLED BEFORE ADDING ANY ENDPOINTS THAT REQUIRE DEPENDENCY INJECTION.

    This function overrides `add_api_route` to:
        - Inject dependencies into endpoint parameters using the provided container.
        - Resolve route-level dependencies automatically.
        - Support both FastAPI application and APIRouter instances.

    Args:
        target (FastAPI | APIRouter): The FastAPI app or APIRouter to wrap.
        container (Container): The FastDI container used to resolve dependencies.

    Example:
        >>> app = FastAPI()
        >>> container = Container()
        >>> Injectify(app, container)
    """

    originalAddAPIRouter: Callable[..., None]

    if isinstance(target, FastAPI):
        originalAddAPIRouter = target.router.add_api_route
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
            if annotatedDependency := getAnnotatedDependencyIfRegistered(param.annotation, container):
                newParam = param.replace(default=annotatedDependency)
                params.append(newParam)
                continue
            try:
                newParam = param.replace(default=container.Resolve(param.annotation))
                params.append(newParam)

            except ProtocolNotRegisteredError:
                params.append(param)

        endpoint.__signature__ = signature.replace(parameters=params)  # pyright: ignore[reportFunctionMemberAccess]


        # --- Route Level Dependencies ---

        dependencies: list[Any] = []
        
        for dependancy in kwargs.get('dependencies') or []:  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            injectToList(dependencies, dependancy, container)

        kwargs['dependencies'] = dependencies

        originalAddAPIRouter(path, endpoint, **kwargs)
    
    if isinstance(target, FastAPI):
        target.router.add_api_route = addApiRoute  # pyright: ignore[reportAttributeAccessIssue]
        target.router._add_api_route = originalAddAPIRouter  # pyright: ignore[reportAttributeAccessIssue]
    else:
        target.add_api_route = addApiRoute  # pyright: ignore[reportAttributeAccessIssue]
        target._add_api_route = originalAddAPIRouter  # pyright: ignore[reportAttributeAccessIssue]