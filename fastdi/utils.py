"""
A set of helper utilities used internally by the FastDI library.
"""

from typing import Any, Callable, TypeVar, Annotated, get_args, get_origin

from fastapi.params import Depends

T = TypeVar('T')


def pretend_signature_of(func: T) -> Callable[[Any], T]:

    """
    Decorator helper to "pretend" that another function `f`
    has the same type signature as `func`.
    (Used only for type checkers; no runtime effect.)
    """
    
    return lambda f: f


def is_annotated_with_depends(annotation: Any) -> bool:

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
