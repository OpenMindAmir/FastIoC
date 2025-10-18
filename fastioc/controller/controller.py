"""
This module integrates FastIoC with FastAPI by providing the `APIController` base class.

`APIController` automatically registers routes defined with FastIoC decorators 
and supports full dependency injection for both controllers and their endpoints.  
Make sure to include a valid `container` in the controller's config.
"""

import inspect

from fastapi_controllers.definitions import WebsocketRouteMeta, Route, HTTPRouteMeta  # pyright: ignore[reportMissingTypeStubs]
from fastapi_controllers.helpers import _replace_signature  # pyright: ignore[reportUnknownVariableType, reportPrivateUsage, reportMissingTypeStubs]

from fastioc.integrations import APIRouter
from fastioc.controller.definitions import APIRouterParams
from fastioc.container import Container
from fastioc.definitions import LifeTime

class APIController:

    """
    APIController provides an integration layer between FastIoC's dependency injection container and FastAPI's routing system.

    This class acts as a declarative controller that automatically registers all endpoint methods 
    decorated with FastIoC route decorators (e.g., @get, @post, etc.) into a FastIoC-powered APIRouter.

    Each route and its dependencies are resolved through FastIoC's dependency injection mechanism, 
    allowing constructor injection, type-hint-based injection, and lifecycle management (e.g., singleton, transient).

    The controller can define a class-level `config` attribute containing APIRouterParams, which 
    specifies routing configuration such as prefix, tags, responses, and more.

    ⚠️ Important:
    You must include a valid `container` instance in the `config` parameter to enable dependency injection 
    and proper controller instantiation.

    Usage example:
    ```python
        class UserController(APIController):
            config = {
                "prefix": "/users",
                "container": app_container
            }

            @get("/")
            def list_users(self, service: UserService):
                return service.get_all()

        router = UserController.router()
        app.include_router(router)
    ```
    """

    config: APIRouterParams = {}

    @classmethod
    def router(cls, config: APIRouterParams = {}) -> APIRouter:  # pyright: ignore[reportRedeclaration]
        """
        Create a new FastIoc APIRouter instance and populate it with APIRoutes.

        Args:
            config (Optional[APIRouterParams]): Optional configuration parameters for the APIRouter. 
                If not provided, uses the controller's default config.

        Returns:
            APIRouter: An instance of fastioc.integrations.APIRouter with routes registered.
        """

        config = {**cls.config, **config}
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