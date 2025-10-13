# Dependency Registration

Registration is the process of telling the container which implementation to provide when a specific interface (protocol) is requested. FastIoC makes this incredibly simple with zero boilerplate.

## Creating a Container

First, create a `Container` instance:

```python
from fastioc import Container

container = Container()
```

That's it! Your container is ready to register dependencies.

## Understanding Interfaces

In FastIoC, any type can be used as an interface - whether it's a Protocol, an abstract class, a regular class, or even a custom marker type. However, **Protocols are recommended for class-based dependencies** as they provide better type safety, editor support, and enable true interface-based programming following the Dependency Inversion Principle:

```python
from typing import Protocol

class IService(Protocol):
    """This is your interface - what you'll request in endpoints"""

    def get_data(self) -> str: ...
```

## Registering Dependencies

FastIoC supports everything that can be a [dependency in FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/) - **classes**, **functions**, **generators**, **async generators**, **callable objects**, and more. All of them work seamlessly with both sync and async implementations - FastAPI handles the execution automatically.

Here are the most common patterns:

### Class-Based Dependencies

The most common pattern for stateful services:

```python
from typing import Protocol

# 1. Define your interface
class IUserService(Protocol):
    def get_user(self, id: int) -> dict: ...
    async def get_user_async(self, id: int) -> dict: ...

# 2. Implement the concrete class
class UserService(IUserService):
    def __init__(self):
        self.db_connection = "postgresql://..."

    def get_user(self, id: int) -> dict:
        return {"id": id, "name": "John Doe"}

    async def get_user_async(self, id: int) -> dict:
        # You can mix sync and async methods in the same class
        return {"id": id, "name": "Jane Doe"}

# 3. Register with the container
container.add_scoped(IUserService, UserService)
```

**Using the Same Class as Interface:**

For simpler projects, you can use the class itself as both the interface and implementation (similar to NestJS):

```python
class UserService:
    def get_user(self, id: int) -> dict:
        return {"id": id, "name": "John Doe"}

# Register the class to itself
container.add_scoped(UserService, UserService)
```

However, for larger projects, **using separate Protocols as interfaces is considered best practice** as it:
- Follows the Dependency Inversion Principle (depend on abstractions, not concretions)
- Makes your code more testable (easy to mock interfaces)
- Provides better separation of concerns
- Enables swapping implementations without changing dependent code

### Function-Based Dependencies

Perfect for simple, stateless operations or direct value providers:

```python
# 1. Define a marker type for your dependency
class UserId(int):
    """Custom type to identify this dependency"""
    ...

# 2. Create your function
def get_user_id() -> int:
    return 42

# 3. Register with the container
container.add_scoped(UserId, get_user_id)
```

**Async Example:**

```python
class ApiKey(str):
    ...

async def fetch_api_key() -> str:
    # FastAPI handles async automatically
    return "secret-key-123"

container.add_scoped(ApiKey, fetch_api_key)
```

### Generator-Based Dependencies

Ideal when you need setup and teardown logic (like managing database connections or file handles):

```python
from typing import Generator

class DatabaseConnection(object):
    """Marker type for DB connection"""
    ...

def get_db_connection() -> Generator[object, None, None]:
    # Setup: acquire resource
    connection = create_connection()
    print("Connection opened")

    try:
        yield connection  # Provide the dependency
    finally:
        # Teardown: cleanup resource
        connection.close()
        print("Connection closed")

container.add_scoped(DatabaseConnection, get_db_connection)
```

**Async Generator Example:**

```python
from typing import AsyncGenerator

class AsyncDbConnection(object):
    ...

async def get_async_db() -> AsyncGenerator[object, None]:
    # Setup
    db = await connect_async()

    try:
        yield db
    finally:
        # Cleanup
        await db.close()

container.add_scoped(AsyncDbConnection, get_async_db)
```

## Important Note: Avoid Built-in Types

**Do not use built-in types** (`str`, `int`, `dict`, etc.) as interfaces when registering dependencies:

```python
# ❌ BAD - FastAPI won't be able to parse request parameters
container.add_scoped(str, get_some_string)
container.add_scoped(int, get_some_number)

# ✅ GOOD - Use custom marker types
class SomeString(str): ...
class SomeNumber(int): ...

container.add_scoped(SomeString, get_some_string)
container.add_scoped(SomeNumber, get_some_number)
```

This is because FastAPI needs to distinguish between query/path parameters and injected dependencies.

!!! warning "Advanced Usage"
    FastIoC does not block registering built-in types - the operation will work. However, you should only do this if you fully understand the implications and are certain your endpoints won't have parameter name conflicts. **Use at your own risk!**

## Registration Methods

FastIoC provides three registration methods that control dependency lifetimes:

```python
container.add_singleton(IService, ServiceImpl)   # One instance per application
container.add_scoped(IService, ServiceImpl)      # One instance per request
container.add_transient(IService, ServiceImpl)   # New instance every time
```

We'll explore these lifetimes in detail in the [Dependency Lifetimes](lifetime.md) chapter.

## Next Steps

- Learn about [Dependency Resolution](resolve.md) - how to access registered dependencies
- Understand [Dependency Lifetimes](lifetime.md) - singleton, scoped, and transient behaviors
- Explore [Nested Dependencies](nested.md) - automatic resolution of dependency chains
