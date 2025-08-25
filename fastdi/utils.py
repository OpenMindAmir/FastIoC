from typing import Any, Callable, TypeVar

T = TypeVar('T')

def pretendSignatureOf(func: T) -> Callable[[Any], T]:
    return lambda f: f