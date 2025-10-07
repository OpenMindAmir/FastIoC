import inspect
from typing import Optional

from fastapi_controllers.definitions import WebsocketRouteMeta, Route, HTTPRouteMeta  # pyright: ignore[reportMissingTypeStubs]
from fastapi_controllers.helpers import _replace_signature  # pyright: ignore[reportUnknownVariableType, reportPrivateUsage, reportMissingTypeStubs]

from fastioc.integrations import APIRouter
from fastioc.controller.definitions import APIRouterParams
from fastioc.container import Container
from fastioc.definitions import LifeTime

class APIController:
    RouterConfig: APIRouterParams = {}

    @classmethod
    def router(cls, RouterConfig: Optional[APIRouterParams] = {}) -> APIRouter:  # pyright: ignore[reportRedeclaration]
        """
        Create a new APIRouter instance and populate the APIRoutes.

        Returns:
            APIRouter: An APIRouter instance.
        """

        if not RouterConfig:
            RouterConfig = cls.RouterConfig
        container = RouterConfig['container'] or Container() # pyright: ignore[reportTypedDictNotRequiredAccess]

        controller: type['APIController'] = container._nested_injector(cls, lifetime=LifeTime.SINGLETON)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAssignmentType, reportPrivateUsage]
        
        router = APIRouter(**(RouterConfig or {}))  # pyright: ignore[reportCallIssue]
        for _, route in inspect.getmembers(controller, predicate=lambda r: isinstance(r, Route)):
            _replace_signature(controller, route.endpoint)
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