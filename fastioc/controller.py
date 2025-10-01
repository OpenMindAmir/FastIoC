# type: ignore
import inspect
from typing import Optional, Sequence, List, Union, Dict, Any
from enum import Enum

from fastapi import params, APIRouter as _APIRouter
from fastapi_controllers.definitions import WebsocketRouteMeta, Route, HTTPRouteMeta
from fastapi_controllers.helpers import _replace_signature, _validate_against_signature

from fastioc.integrations import APIRouter

def _is_route(obj: Any) -> bool:
    """
    Check if an object is an instance of Route.

    Args:
        obj: The object to be checked.

    Returns:
        True if the checked object is an instanc of Route.
    """
    return isinstance(obj, Route)

class APIController:
    prefix: str = ""
    dependencies: Optional[Sequence[params.Depends | type]] = None
    tags: Optional[List[Union[str, Enum]]] = None
    __router_params__: Optional[Dict[str, Any]] = None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__router_params__ = cls.__router_params__ or {}
        for param in ["prefix", "dependencies", "tags"]:
            if not cls.__router_params__.get(param):
                cls.__router_params__[param] = getattr(cls, param)
        _validate_against_signature(_APIRouter.__init__, kwargs=cls.__router_params__)

    @classmethod
    def create_router(cls) -> APIRouter:
        """
        Create a new APIRouter instance and populate the APIRoutes.

        Returns:
            APIRouter: An APIRouter instance.
        """
        router = APIRouter(**(cls.__router_params__ or {}))
        for _, route in inspect.getmembers(cls, predicate=_is_route):
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