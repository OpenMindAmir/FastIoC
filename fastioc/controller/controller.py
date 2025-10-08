import inspect
from typing import Optional

from fastapi_controllers.definitions import WebsocketRouteMeta, Route, HTTPRouteMeta  # pyright: ignore[reportMissingTypeStubs]
from fastapi_controllers.helpers import _replace_signature  # pyright: ignore[reportUnknownVariableType, reportPrivateUsage, reportMissingTypeStubs]

from fastioc.integrations import APIRouter
from fastioc.controller.definitions import APIRouterParams
from fastioc.container import Container
from fastioc.definitions import LifeTime

class APIController:
    config: APIRouterParams = {}

    @classmethod
    def router(cls, config: Optional[APIRouterParams] = {}) -> APIRouter:  # pyright: ignore[reportRedeclaration]
        """
        Create a new FastIoc APIRouter instance and populate it with APIRoutes.

        Args:
            config (Optional[APIRouterParams]): Optional configuration parameters for the APIRouter. 
                If not provided, uses the controller's default config.

        Returns:
            APIRouter: An instance of fastioc.integrations.APIRouter with routes registered.
        """

        if not config:
            config = cls.config
        container = config['container'] or Container() # pyright: ignore[reportTypedDictNotRequiredAccess]

        controller: type['APIController'] = container._nested_injector(cls, lifetime=LifeTime.SINGLETON)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAssignmentType, reportPrivateUsage]
        
        router = APIRouter(**(config or {}))  # pyright: ignore[reportCallIssue]
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