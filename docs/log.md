# Logging

FastIoC provides comprehensive logging to help you understand what's happening inside your dependency injection container. The logging system tracks container initialization, dependency registration, resolution, disposal, and potential issues.

## Enabling Logs

FastIoC uses Python's standard `logging` module with the logger name `"FastIoC"`. To enable and configure logging:

```python
import logging

# Get the FastIoC logger
logger = logging.getLogger("FastIoC")

# Set the logging level
logger.setLevel(logging.DEBUG)  # Show all logs

# Optional: Add a custom handler if needed
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
logger.addHandler(handler)
```

## Log Levels

FastIoC uses different log levels for different types of events:

### DEBUG - Application Events

The DEBUG level logs normal application events and operations. This is useful for understanding the flow of dependency registration and resolution.

**Events logged at DEBUG level:**

- **Container initialization**
  ```
  FastIoC: DEBUG: IoC/DI Container initialized ...
  ```

- **Dependency registration**
  ```
  FastIoC: DEBUG: Dependency "UserService" registered with "SCOPED" lifetime for protocol: "IUserService"
  ```

- **Singleton initialization**
  ```
  FastIoC: DEBUG: Singleton dependency "DatabaseService" initialized
  ```

- **Disposal registration**
  ```
  FastIoC: DEBUG: Disposal registered for dependency "DatabaseService"
  ```

- **Dependency resolution**
  ```
  FastIoC: DEBUG: Resolve called for protocol "IUserService"
  ```

- **Nested dependency resolution**
  ```
  FastIoC: DEBUG: Resolved Protocol "IDatabaseService" as nested dependency for "UserService"
  FastIoC: DEBUG: Resolved Protocol "IEmailService" as nested dependency for "UserService" (from class annotations)
  ```

- **FastAPI built-in resolution**
  ```
  FastIoC: DEBUG: Resolved FastAPI built-in "Request" as nested dependency for "MyService"
  ```

- **Hook execution**
  ```
  FastIoC: DEBUG: Registration hook executed for dependency "IUserService->UserService@SCOPED"
  FastIoC: DEBUG: Resolve hook executed for protocol "IUserService"
  ```

- **Dependency override**
  ```
  FastIoC: DEBUG: Registered dependency "IUserService" overridden
  FastIoC: DEBUG: Registered dependency "IEmailService" overridden by Mock Container
  ```

- **Disposal execution**
  ```
  FastIoC: DEBUG: Dependency "DatabaseService" disposed
  ```

- **FastAPI integration**
  ```
  FastIoC: DEBUG: FastAPI application injectified
  FastIoC: DEBUG: FastAPI router injectified
  ```

### INFO - Skipped Dependencies

The INFO level logs when FastIoC skips resolving a dependency because it's not registered in the container (and it's not a built-in type, FastAPI special type, or Pydantic model).

**Events logged at INFO level:**

- **Unregistered protocol skipped**
  ```
  FastIoC: INFO: Skipped protocol "ICustomService": No registered dependency found
  ```

- **Nested unregistered protocol skipped**
  ```
  FastIoC: INFO: (Nested)Skipped protocol "IHelperService": No registered dependency found
  ```

This helps you identify dependencies that might be missing from your container configuration.

### WARNING - Potential Issues

The WARNING level logs situations that might indicate configuration problems or unexpected behavior, but don't prevent the application from running.

**Events logged at WARNING level:**

- **Scoped dependency depends on transient**
  ```
  FastIoC: WARNING: Request-scoped dependency "UserService" depends on transient dependency "HelperService"
  ```
  This warns you that a scoped dependency depends on a transient one, which might not be what you intended (the transient will be recreated each time).

- **Built-in type registered as protocol**
  ```
  FastIoC: WARNING: Dependency "MyService" registered for protocol "dict" which is a built-in, type, Pydantic model, FastAPI special class. This may override default behavior; make sure this is what you intend
  ```
  This warns when you register a dependency for built-in Python types (like `str`, `int`, `dict`), Pydantic models, or FastAPI special classes (like `Request`, `Response`). This can override FastAPI's default behavior.

### EXCEPTION - Errors During Disposal

The EXCEPTION level logs errors that occur during the disposal process. These errors don't stop other dependencies from being disposed.

**Events logged at EXCEPTION level:**

- **Disposal error**
  ```
  FastIoC: EXCEPTION: Error disposing "DatabaseService": Connection already closed
  ```

## Configuration Examples

### Basic Setup - Show All Logs

```python
import logging
from fastioc import Container

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s: %(levelname)s: %(message)s"
)

# Create container - you'll see initialization log
container = Container()
```

### Production Setup - Only Warnings and Errors

```python
import logging

logger = logging.getLogger("FastIoC")
logger.setLevel(logging.WARNING)  # Only show warnings and errors
```

### Development Setup - Verbose Logging

```python
import logging

# Get the FastIoC logger
logger = logging.getLogger("FastIoC")
logger.setLevel(logging.DEBUG)

# Create a detailed formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Optionally, log to file
file_handler = logging.FileHandler("fastioc.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
```

### Selective Logging - Different Levels per Handler

```python
import logging

logger = logging.getLogger("FastIoC")
logger.setLevel(logging.DEBUG)  # Capture all logs

# Console: Only warnings and errors
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(console)

# File: Everything (DEBUG and above)
file_handler = logging.FileHandler("fastioc_debug.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)
```

## Complete Example with Logging

Here's a complete example showing what logs you might see during typical operations:

```python
import logging
from fastapi import FastAPI
from fastioc import Container

# Enable DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s: %(levelname)s: %(message)s"
)

# Create container
# LOG: FastIoC: DEBUG: IoC/DI Container initialized ...
container = Container()

# Define services
class IDatabaseService:
    pass

class IEmailService:
    pass

class DatabaseService(IDatabaseService):
    def __init__(self):
        self.connected = True

    def __dispose__(self):
        self.connected = False

class EmailService(IEmailService):
    def __init__(self, db: IDatabaseService):
        self.db = db

# Register dependencies
container.add_singleton(IDatabaseService, DatabaseService)
# LOG: FastIoC: DEBUG: Singleton dependency "DatabaseService" initialized
# LOG: FastIoC: DEBUG: Disposal registered for dependency "DatabaseService"
# LOG: FastIoC: DEBUG: Dependency "DatabaseService" registered with "SINGLETON" lifetime for protocol: "IDatabaseService"

container.add_scoped(IEmailService, EmailService)
# LOG: FastIoC: DEBUG: Resolved Protocol "IDatabaseService" as nested dependency for "EmailService"
# LOG: FastIoC: DEBUG: Dependency "EmailService" registered with "SCOPED" lifetime for protocol: "IEmailService"

# Create FastAPI app
app = FastAPI()

# Injectify
container.injectify(app)
# LOG: FastIoC: DEBUG: FastAPI application injectified

# Define endpoint
@app.get("/test")
async def test(email: IEmailService):
    return {"status": "ok"}

# When endpoint is called:
# LOG: FastIoC: DEBUG: Resolve called for protocol "IEmailService"

# During shutdown:
# await container.dispose()
# LOG: FastIoC: DEBUG: Dependency "DatabaseService" disposed
```

## Understanding Log Output

### Tracking Dependency Resolution

When DEBUG logging is enabled, you can trace exactly how FastIoC resolves your dependencies:

```
FastIoC: DEBUG: Resolve called for protocol "IUserService"
FastIoC: DEBUG: Resolved Protocol "IDatabaseService" as nested dependency for "UserService"
FastIoC: DEBUG: Resolved Protocol "IAuthService" as nested dependency for "UserService"
FastIoC: DEBUG: Resolved Protocol "IEmailService" as nested dependency for "UserService"
```

This shows that `UserService` depends on three other services, and FastIoC resolved all of them.

### Identifying Missing Dependencies

INFO logs help you spot dependencies that aren't registered:

```
FastIoC: INFO: Skipped protocol "IOptionalService": No registered dependency found
```

If you see this for a dependency you expected to be registered, check your container configuration.

### Catching Configuration Issues

WARNING logs alert you to potential problems:

```
FastIoC: WARNING: Request-scoped dependency "UserService" depends on transient dependency "HelperService"
```

This might indicate that you should register `HelperService` as scoped instead of transient for better performance and consistency.

## Disabling Logs

To completely disable FastIoC logs:

```python
import logging

logger = logging.getLogger("FastIoC")
logger.setLevel(logging.CRITICAL)  # Only critical errors (effectively disables logs)
# Or completely disable:
logger.disabled = True
```

## Best Practices

1. **Development**: Use `DEBUG` level to understand how dependencies are wired
   ```python
   logger.setLevel(logging.DEBUG)
   ```

2. **Testing**: Use `WARNING` level to catch configuration issues without noise
   ```python
   logger.setLevel(logging.WARNING)
   ```

3. **Production**: Use `WARNING` or `ERROR` level for minimal logging
   ```python
   logger.setLevel(logging.WARNING)
   ```

4. **Debugging Issues**: Enable `DEBUG` temporarily and log to a file
   ```python
   handler = logging.FileHandler("fastioc_debug.log")
   handler.setLevel(logging.DEBUG)
   logger.addHandler(handler)
   ```

5. **CI/CD**: Disable logs during automated tests to reduce noise
   ```python
   logger.disabled = True
   ```

## Log Level Summary

| Level | Use Case | Example Events |
|-------|----------|----------------|
| **DEBUG** | Development, understanding flow | Container init, registration, resolution, disposal |
| **INFO** | Identifying skipped dependencies | Unregistered protocols |
| **WARNING** | Catching potential issues | Scoped -> Transient dependency, built-in type registration |
| **EXCEPTION** | Disposal errors | Failed cleanup operations |

## Related Documentation

- [Container Registration](lifetime.md)
- [Nested Dependencies](nested.md)
- [Singleton Cleanup](dispose.md)
- [Hooks](hook.md)
