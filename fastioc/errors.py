"""
Exceptions used by the FastIoC library.
"""


class FastIoCError(Exception):
    """
    Base class for all exceptions raised by the FastIoC library.
    Allows users to catch all FastIoC-related errors with a single except clause.
    """
    pass


class UnregisteredProtocolError(FastIoCError):
    """
    Raised when a requested protocol, interface, or service has not been
    registered in the container.
    """
    pass


class SingletonGeneratorError(FastIoCError):
    """
    Raised when attempting to register a generator or async generator as
    a singleton dependency in the DI container.

    Generator objects cannot be used more than once - reusing them would
    raise an error. Therefore, singleton scope does not make sense here.
    """
    pass


class SingletonLifetimeViolationError(FastIoCError):
    """
    Raised when a singleton dependency attempts to depend on a scoped or transient
    dependency. 

    This violates lifetime rules because singleton instances live for the entire
    process/worker lifetime, while scoped and transient instances are created per
    request or per resolution. Injecting shorter-lived dependencies into a
    singleton may lead to captured request state, invalid references, or memory leaks.
    """
    pass