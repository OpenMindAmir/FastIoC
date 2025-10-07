import sys
import copy
import inspect
from inspect import Parameter
from typing import Any

from fastapi import APIRouter as _APIRouter, Request, Response, BackgroundTasks, WebSocket, UploadFile
from fastapi.params import Depends
from fastapi.security import SecurityScopes
from fastapi_controllers.definitions import WebsocketRouteMeta, Route, HTTPRouteMeta  # pyright: ignore[reportMissingTypeStubs]
from fastapi_controllers.helpers import _replace_signature  # pyright: ignore[reportUnknownVariableType, reportPrivateUsage, reportMissingTypeStubs]

from fastioc.integrations import APIRouter
from fastioc.controller.definitions import APIRouterParams
from fastioc.utils import pretend_signature_of, resolve_forward_refs, is_annotated_with_marker, log_skip, log
from fastioc.container import Container
from fastioc.errors import UnregisteredProtocolError

class APIController(APIRouter):
    RouterConfig: APIRouterParams = {}

    @pretend_signature_of(_APIRouter.__init__)
    def __init__(self, *args: Any, **kwargs: Any):
        router_params = copy.deepcopy(self.RouterConfig)
        controller_dependency = None

        if 'container' in kwargs and isinstance(kwargs.get('container'), Container):
            router_params['container'] = kwargs.pop('container')
        
        container: Container = router_params.get('container') or Container()

        hint_params: list[Parameter] = [] 
        hints = resolve_forward_refs(self.__class__.__annotations__, vars(sys.modules[self.__class__.__module__]), dict(vars(self.__class__)))
        if hints:
            for name, annotation in hints.items():
                if name in kwargs:
                    setattr(self, name, kwargs.pop(name))
                    continue
                if annotation in (Request, Response, BackgroundTasks, WebSocket, UploadFile, SecurityScopes) or is_annotated_with_marker(annotation):
                    hint_params.append(Parameter(
                        name=name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=annotation
                    ))
                    log.debug('Resolved FastAPI built-in "%s" as nested dependency for Controller "%s"', annotation, self.__class__.__name__)
                    continue
                if annotated_dependency := container._get_annotated_dependency_if_registered(annotation):  # pyright: ignore[reportPrivateUsage]
                    hint_params.append(Parameter(
                        name=name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=annotation,
                        default=annotated_dependency
                    ))
                    log.debug('Resolved Protocol "%s" as nested dependency for Controller "%s" (from class annotations)', annotation, self.__class__.__name__)
                    continue
                try:
                    dependency: Depends = container.resolve(annotation)
                    hint_params.append(Parameter(
                        name=name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=annotation,
                        default=dependency
                    ))
                    log.debug('Resolved Protocol "%s" as dependency for Controller "%s" (from class annotations)', annotation, self.__class__.__name__)
                except UnregisteredProtocolError:
                    log_skip(annotation, False)
            if hint_params:
                # class ControllerDependency:
                #     def __init__(self, *args: Any, **kwargs: Any):
                #         param_names = list(inspect.signature(self.__class__.__init__).parameters.keys())[1:]
                #         for name, value in zip(param_names, args):
                #             setattr(self, name, value)
                #         for key, value in kwargs.items():
                #             setattr(self, key, value)

                # signature = inspect.signature(ControllerDependency.__init__)
                # ControllerDependency.__signature__ = signature.replace(parameters=hint_params)  # pyright: ignore[reportAttributeAccessIssue]
                # controller_dependency = ControllerDependency
        
        

    @classmethod
    def create_router(cls) -> APIRouter:
        """
        Create a new APIRouter instance and populate the APIRoutes.

        Returns:
            APIRouter: An APIRouter instance.
        """
        router = APIRouter(**(cls.RouterConfig or {}))  # pyright: ignore[reportCallIssue]
        for _, route in inspect.getmembers(cls, predicate=lambda r: isinstance(r, Route)):
            _replace_signature(cls, route.endpoint)
            if isinstance(route.route_meta, HTTPRouteMeta):
                router.add_api_route(
                    route.route_args[0],
                    route.endpoint,
                    *route.route_args[1:],
                    methods=[route.route_meta.request_method],
                    **route.route_kwargs,
                )
            if isinstance(route.route_meta, WebsocketRouteMeta):
                router.add_api_websocket_route(
                    route.route_args[0],
                    route.endpoint,
                    *route.route_args[1:],
                    **route.route_kwargs,
                )
        return router