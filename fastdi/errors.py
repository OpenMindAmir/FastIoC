"""
Exceptions used by the FastDI library.
"""


class FastDIError(Exception):
    """
    Base class for all exceptions raised by the FastDI library.
    Allows users to catch all FastDI-related errors with a single except clause.
    """
    pass


class ProtocolNotRegisteredError(FastDIError):
    """
    Raised when a requested protocol, interface, or service has not been
    registered in the container.
    """
    pass


class SingletonGeneratorNotAllowedError(FastDIError):
    """
    Raised when attempting to register a generator or async generator as
    a singleton dependency in the DI container.

    Generator objects cannot be used more than once - reusing them would
    raise an error. Therefore, singleton scope does not make sense here.
    """
    pass


class ProtocolRequiredForNonClassProvidedError(FastDIError):
    """
    Raised when a non-class dependency is provided without specifying a protocol.
    """
    pass