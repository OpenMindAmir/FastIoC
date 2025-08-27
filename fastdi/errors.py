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

class SingletonGeneratorError(FastDIError):
    """
    Raised when attempting to register a generator or async generator as
    a singleton dependency in the DI container.
    
    In FastAPI, generator dependencies are designed to run cleanup logic
    after each request. Registering them as singletons would bypass this
    behavior, making it meaningless and potentially unsafe.
    """

    pass