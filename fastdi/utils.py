"""
A set of helper utilities used internally by the FastDI library.
"""

from typing import Any, Callable, TypeVar, Annotated, get_args, get_origin
from inspect import Parameter
import types
import inspect

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

def clone_function(func: types.FunctionType) -> types.FunctionType:
    """Clone a Python function (sync, async, or generator)."""
    clone = types.FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=func.__defaults__,
        closure=func.__closure__,
    )
    # متادیتاها
    clone.__dict__.update(func.__dict__)
    clone.__annotations__ = func.__annotations__.copy() if func.__annotations__ else {}
    clone.__kwdefaults__ = func.__kwdefaults__.copy() if func.__kwdefaults__ else None
    clone.__doc__ = func.__doc__
    clone.__module__ = func.__module__
    clone.__qualname__ = func.__qualname__
    return clone


def clone_class(cls: type) -> type:
    """Clone a Python class (with all methods and attributes)."""
    namespace = dict(cls.__dict__)
    # private متاهای خاصی که نباید کپی بشن
    namespace.pop("__dict__", None)
    namespace.pop("__weakref__", None)
    clone = type(cls.__name__, cls.__bases__, namespace)
    clone.__module__ = cls.__module__
    clone.__doc__ = cls.__doc__
    clone.__qualname__ = cls.__qualname__
    return clone


def clone_concrete(impl: Any) -> Any:
    """
    Clone either a function or a class.
    - Preserves async / generator / closure for functions
    - Preserves methods/attributes for classes
    """
    if inspect.isfunction(impl):
        return clone_function(impl)
    elif inspect.isclass(impl):
        return clone_class(impl)
    else:
        raise TypeError(f"Unsupported implementation type: {type(impl)}")