"""
A set of helper utilities used internally by the FastDI library.
"""

from typing import Any, Callable, TypeVar, Annotated, get_args, get_origin, TYPE_CHECKING

from fastapi.params import Depends

from fastdi.errors import ProtocolNotRegisteredError
if TYPE_CHECKING:
    from fastdi.container import Container

T = TypeVar('T')


def pretendSignatureOf(func: T) -> Callable[[Any], T]:

    """
    Decorator helper to "pretend" that another function `f`
    has the same type signature as `func`.
    (Used only for type checkers; no runtime effect.)
    """
    
    return lambda f: f


def injectToList(_list: list[Any], item: Any, container: 'Container'):

    """
    Append a dependency-like item into a list.

    - If `item` is a `Depends` or annotated with `Depends`, append as-is.
    - Otherwise try to resolve it from the container and append the resolved `Depends`.
    - If the type is not registered in the container, append the item itself.
    """

    if isinstance(item, Depends) or isAnnotatedWithDepends(item):
        _list.append(item)
        return

    try:
        dependancy: Depends = container.Resolve(item)
        _list.append(dependancy)

    except ProtocolNotRegisteredError:
        _list.append(item)


def isAnnotatedWithDepends(annotation: Any) -> bool:

    """
    Check if a type annotation is wrapped with `Annotated[..., Depends(...)]`.

    Returns True if the given annotation is an `Annotated` type that includes
    a `Depends` marker among its extra arguments, otherwise False.
    """

    if get_origin(annotation) is Annotated:
        mainType, *extras = get_args(annotation)  # pyright: ignore[reportUnusedVariable]
        for extra in extras:
            if isinstance(extra, Depends):
                return True
    return False

def getAnnotatedDependencyIfRegistered(annotation: Any, container: Container) -> Depends | None:

    """
    Attempts to resolve a dependency from the container if the given annotation
    is an Annotated type with a registered dependency.

    Returns the first resolved dependency if found (stops at the first match),
    otherwise None.
    """

    dependency = None
    if get_origin(annotation) is Annotated:
        mainType, *extras = get_args(annotation)  # pyright: ignore[reportUnusedVariable]
        for extra in extras:
            if isinstance(extra, type):
                try:
                    dependency = container.Resolve(extra)
                    break
                except ProtocolNotRegisteredError:
                    continue
    return dependency



# TODO Remove Extra code

# def getSafeAttrs() -> list[str]:
#     signature = inspect.signature(APIRouter.__init__)
#     return [name for name in signature.parameters if name != 'self']


# def cloneRouter(router: APIRouter, newRouter: type[APIRouter]) -> APIRouter:
#     _newRouter = newRouter()
#     for key in getSafeAttrs():
#         setattr(_newRouter, key, getattr(router, key, None))
#     return _newRouter
