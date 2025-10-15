# Singleton Cleanup with `__dispose__`

When working with singleton dependencies, you often need to perform cleanup operations when your application shuts down such as closing database connections, releasing file handles, or cleaning up resources. FastIoC provides a clean way to handle this through the `__dispose__` method.

## Why `__dispose__` Instead of Generators?

In many dependency injection systems, you might use generators with `yield` for cleanup:

```python
def get_db():
    db = Database()
    yield db
    db.close()  # Cleanup after yield
```

However, **generators and async generators cannot be registered as singletons** in FastIoC. This is because generators are meant to be called multiple times, which conflicts with the singleton pattern of having one shared instance throughout the application lifecycle.

Instead, FastIoC uses the `__dispose__` method pattern for singleton cleanup.

## The `__dispose__` Method

Any singleton class that defines a `__dispose__` method will have that method automatically called when you invoke `container.dispose()`. FastIoC supports both synchronous and asynchronous disposal.

### Basic Example

```python
from fastioc import Container

class DatabaseService:
    def __init__(self):
        self.connection = self._create_connection()
        print("Database connection opened")

    def _create_connection(self):
        # Create database connection
        return "db_connection"

    def query(self, sql: str):
        return f"Executing: {sql}"

    def __dispose__(self):
        """Called automatically during container.dispose()"""
        print("Database connection closed")
        self.connection = None

# Register as singleton
container = Container()
container.add_singleton(DatabaseService, DatabaseService)
```

### Async Disposal

FastIoC automatically detects and awaits async `__dispose__` methods:

```python
import asyncio

class CacheService:
    def __init__(self):
        self.cache = {}
        self.connected = True
        print("Cache service started")

    async def __dispose__(self):
        """Async cleanup - will be awaited automatically"""
        print("Flushing cache...")
        await asyncio.sleep(0.1)  # Simulate async cleanup
        self.cache.clear()
        self.connected = False
        print("Cache service stopped")

container = Container()
container.add_singleton(CacheService, CacheService)
```

## Calling `container.dispose()`

You must call `container.dispose()` during your application's shutdown to trigger all singleton cleanups. The recommended approach is to use FastAPI's [lifespan events](https://fastapi.tiangolo.com/advanced/events/).

### Using Lifespan Context Manager

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastioc import Container

# Setup container
container = Container()
container.add_singleton(DatabaseService, DatabaseService)
container.add_singleton(CacheService, CacheService)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Application initialization happens here
    print("Application starting...")
    yield
    # Shutdown: Cleanup happens after yield
    print("Application shutting down...")
    await container.dispose()

# Create app with lifespan
app = FastAPI(lifespan=lifespan)
container.injectify(app)

@app.get("/")
async def root(db: DatabaseService, cache: CacheService):
    return {"message": "Hello World"}
```

When the application shuts down, `container.dispose()` will automatically call the `__dispose__` method of all registered singletons.

## Accessing FastAPI App in `__dispose__`

The `dispose()` method can optionally receive the FastAPI app instance, which you can then access in your `__dispose__` methods:

```python
from fastapi import FastAPI

class ServiceWithAppAccess:
    def __init__(self):
        self.resource = "allocated"
        print("Service initialized")

    def __dispose__(self, app: FastAPI):
        """Receives the FastAPI app during disposal"""
        print(f"Disposing service for app: {app.title}")
        print(f"App state: {app.state}")
        self.resource = None

# In your lifespan:
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await container.dispose(app)  # Pass app to dispose
```

FastIoC automatically detects if your `__dispose__` method has an `app` parameter and passes it accordingly. If your `__dispose__` doesn't need the app, simply omit the parameter.

## Key Points

- Use `__dispose__` for singleton cleanup (generators aren't allowed for singletons)
- Both sync and async `__dispose__` methods are supported
- Call `container.dispose()` in your FastAPI lifespan shutdown
- Optionally receive the FastAPI `app` instance in `__dispose__(self, app: FastAPI)`
- Errors in one disposal don't stop others from running
- All `__dispose__` methods are automatically detected and called no manual registration needed

## Related Documentation

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI Startup and Shutdown](https://fastapi.tiangolo.com/advanced/events/#lifespan)
