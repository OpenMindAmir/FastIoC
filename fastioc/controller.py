# type: ignore
import inspect
from typing import Optional, Sequence, List, Union, Dict, Any
from enum import Enum

from fastapi import params, APIRouter as _APIRouter
from fastapi_controllers.definitions import WebsocketRouteMeta, Route, HTTPRouteMeta
from fastapi_controllers.helpers import _replace_signature, _validate_against_signature
from fastapi_controllers.routing import _RouteDecorator

from fastioc.integrations import APIRouter
from fastioc.utils import pretend_signature_of

router = APIRouter()

class delete(_RouteDecorator, route_meta=RouteMetadata.delete):
    @pretend_signature_of(router.delete)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class get(_RouteDecorator, route_meta=RouteMetadata.get):
    @pretend_signature_of(router.get)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class head(_RouteDecorator, route_meta=RouteMetadata.head):
    @pretend_signature_of(router.head)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class options(_RouteDecorator, route_meta=RouteMetadata.options):
    @pretend_signature_of(router.options)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class patch(_RouteDecorator, route_meta=RouteMetadata.patch):
    @pretend_signature_of(router.patch)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class post(_RouteDecorator, route_meta=RouteMetadata.post):
    @pretend_signature_of(router.post)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class put(_RouteDecorator, route_meta=RouteMetadata.put):
    @pretend_signature_of(router.put)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class trace(_RouteDecorator, route_meta=RouteMetadata.trace):
    @pretend_signature_of(router.trace)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class websocket(_RouteDecorator, route_meta=RouteMetadata.websocket):
    @pretend_signature_of(router.websocket)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

del router


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