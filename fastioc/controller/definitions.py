from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union, TypedDict

from fastapi import APIRouter
from fastapi.routing import APIRoute
from fastapi.responses import Response
from fastapi.params import Depends
from starlette.routing import BaseRoute
from starlette.types import Lifespan, ASGIApp
from fastapi_controllers.routing import _RouteDecorator  # pyright: ignore[reportPrivateUsage, reportMissingTypeStubs]
from fastapi_controllers.definitions import RouteMetadata # pyright: ignore[reportMissingTypeStubs]

from fastioc.utils import pretend_signature_of
from fastioc.container import Container


# --- APIRouter Parameters class ---

class APIRouterParams(TypedDict, total=False):
    prefix: str
    tags: Optional[List[Union[str, Any]]]
    container: Optional[Container]
    dependencies: Optional[Sequence[Depends | type]]
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]]
    callbacks: Optional[List[BaseRoute]]
    routes: Optional[List[BaseRoute]]
    redirect_slashes: bool
    default: Optional[ASGIApp]
    dependency_overrides_provider: Optional[Any]
    route_class: Type[APIRoute]
    default_response_class: Type[Response]
    on_startup: Optional[Sequence[Callable[[], Any]]]
    on_shutdown: Optional[Sequence[Callable[[], Any]]]
    lifespan: Optional[Lifespan[Any]]
    include_in_schema: bool
    deprecated: Optional[bool]
    generate_unique_id_function: Callable[[APIRoute], str]


# --- Endpoint Actions ---

router = APIRouter()

class delete(_RouteDecorator, route_meta=RouteMetadata.delete):
    @pretend_signature_of(router.delete)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class get(_RouteDecorator, route_meta=RouteMetadata.get):
    @pretend_signature_of(router.get)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class head(_RouteDecorator, route_meta=RouteMetadata.head):
    @pretend_signature_of(router.head)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class options(_RouteDecorator, route_meta=RouteMetadata.options):
    @pretend_signature_of(router.options)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class patch(_RouteDecorator, route_meta=RouteMetadata.patch):
    @pretend_signature_of(router.patch)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class post(_RouteDecorator, route_meta=RouteMetadata.post):
    @pretend_signature_of(router.post)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class put(_RouteDecorator, route_meta=RouteMetadata.put):
    @pretend_signature_of(router.put)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class trace(_RouteDecorator, route_meta=RouteMetadata.trace):
    @pretend_signature_of(router.trace)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

class websocket(_RouteDecorator, route_meta=RouteMetadata.websocket):
    @pretend_signature_of(router.websocket)
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

del router
