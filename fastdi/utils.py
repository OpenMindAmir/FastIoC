"""
A set of helper utilities used internally by the FastDI library.
"""

from typing import Any, Callable, TypeVar, Annotated, get_args, get_origin
from inspect import Parameter

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


PARAM_KIND_ORDER = {
    Parameter.POSITIONAL_ONLY: 0,
    Parameter.POSITIONAL_OR_KEYWORD: 1,
    Parameter.VAR_POSITIONAL: 2,
    Parameter.KEYWORD_ONLY: 3,
    Parameter.VAR_KEYWORD: 4,
}

def sort_parameters(params: list[Parameter]) -> list[Parameter]:

    """
    Sort parameters into a valid Python function signature order.

    Rules:
    1. POSITIONAL_ONLY
    2. POSITIONAL_OR_KEYWORD (no default first, then with default)
    3. VAR_POSITIONAL (*args)
    4. KEYWORD_ONLY (no default first, then with default)
    5. VAR_KEYWORD (**kwargs)
    """

    def key(param: Parameter):
        order = PARAM_KIND_ORDER[param.kind]
        has_default = 1 if param.default is not Parameter.empty else 0
        return (order, has_default)
    
    return sorted(params, key=key)