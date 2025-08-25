from typing import Any, Callable, TypeVar
from fastdi import Container
from fastdi.custom_types import FastAPIDependable
from fastdi.errors import InterfaceNotRegistered
from fastapi import Depends
from fastapi.params import Depends as _Depends

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