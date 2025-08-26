from typing import Any, Callable, TypeVar

from fastapi import Depends
from fastapi.params import Depends as _Depends

from fastdi.container import Container
from fastdi.custom_types import FastAPIDependable
from fastdi.errors import InterfaceNotRegistered

T = TypeVar('T')

def pretendSignatureOf(func: T) -> Callable[[Any], T]:
    return lambda f: f

def injectToList(_list: list[Any], item: Any, container: Container):
    if isinstance(item, _Depends):
        _list.append(item)
        return

    try:
        dependable: FastAPIDependable = container.Resolve(item)
        _list.append(Depends(dependable))

    except InterfaceNotRegistered:
        _list.append(item)


# TODO Remove Extra code

# def getSafeAttrs() -> list[str]:
#     signature = inspect.signature(APIRouter.__init__)
#     return [name for name in signature.parameters if name != 'self']


# def cloneRouter(router: APIRouter, newRouter: type[APIRouter]) -> APIRouter:
#     _newRouter = newRouter()
#     for key in getSafeAttrs():
#         setattr(_newRouter, key, getattr(router, key, None))
#     return _newRouter