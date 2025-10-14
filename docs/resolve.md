# Dependency Resolution

Once you've registered your dependencies, you can resolve and use them in your FastAPI endpoints. FastIoC makes this incredibly simple - just add type hints to your endpoint parameters, and the container automatically injects the registered implementations.

## Simple Resolution

The most straightforward way to resolve dependencies is by type-hinting your endpoint parameters with the registered interface:

```python
# main.py
from fastapi import FastAPI
from project.interfaces import IUserService

app = FastAPI()
container.injectify(app)

@app.get('/user/{user_id}')
def get_user_endpoint(user_id: int, service: IUserService) -> dict:
    # service is automatically injected with the registered implementation
    return service.get_user(user_id)
```

```python
# project/interfaces.py
from typing import Protocol

class IUserService(Protocol):
    def get_user(self, id: int) -> dict: ...
```

That's it! No `Depends()` needed. FastIoC automatically recognizes that `IUserService` is registered and injects it.

!!! note "Dependency Not Working?"
    If your endpoint returns **422 Unprocessable Entity** errors, it likely means the dependency wasn't registered in the container. See [Unregistered Dependencies](injectify.md#important-unregistered-dependencies) for troubleshooting.

## Annotated Resolution

For non-class dependencies (like functions or custom marker types), you can use Python's `Annotated` type for clearer intent:

```python
# main.py
from typing import Annotated
from project.interfaces import IUserService
from project.dependencies import UserId, ApiKey

@app.get('/profile')
def get_profile(
    user_id: Annotated[int, UserId],
    api_key: Annotated[str, ApiKey]
) -> dict:
    return {
        "user_id": user_id,
        "authenticated": True
    }
```

```python
# project/dependencies.py
# Marker types for function-based dependencies
class UserId(int): ...
class ApiKey(str): ...
```

**Why use Annotated?**

- Makes the dependency source explicit and clear
- Works seamlessly with any dependency type
- Provides better IDE support and documentation
- Can also be used with class-based dependencies if preferred

```python
# This also works for classes
@app.get('/data')
def get_data(service: Annotated[IUserService, IUserService]) -> dict:
    return service.get_user(1)
```

## Mixing with FastAPI Features

FastIoC is 100% compatible with FastAPI's native features. You can freely mix registered dependencies with query parameters, path parameters, request bodies, headers, cookies, and traditional `Depends()`:

```python
# project/routers/items.py
from fastapi import APIRouter, Depends, Header, Cookie
from typing import Annotated
from project.interfaces import IUserService
from project.dependencies import UserId

router = APIRouter()

def get_request_id() -> str:
    """A regular FastAPI dependency (not registered in container)"""
    return "req-12345"

@router.get('/items/{item_id}')
async def get_item(
    # Path parameter
    item_id: int,

    # Query parameters
    q: str,
    page_size: int = 10,

    # FastIoC registered dependency (simple)
    service: IUserService,

    # FastIoC registered dependency (annotated)
    user_id: Annotated[int, UserId],

    # Traditional FastAPI dependency
    request_id: str = Depends(get_request_id),

    # Headers and cookies
    authorization: Annotated[str, Header()],
    session_token: Annotated[str, Cookie()]
) -> dict:
    return {
        "item_id": item_id,
        "query": q,
        "page_size": page_size,
        "user": service.get_user(user_id),
        "request_id": request_id,
        "auth": authorization,
        "session": session_token
    }
```

Everything works together seamlessly!

<!-- ## ⚠️ Important: Parameter Ordering

Since FastIoC dependencies are converted to FastAPI's `Depends()` under the hood, you need to follow Python's parameter ordering rules:

```python
from typing import Annotated
from project.interfaces import IUserService
from project.dependencies import UserId

@app.get('/example')
def good_example(
    # ✅ CORRECT: Simple parameters first
    item_id: int,
    q: str,
    page: int = 1,

    # Then dependencies (they have default values under the hood)
    service: IUserService,
    user_id: Annotated[int, UserId]
) -> dict:
    return {"status": "ok"}

@app.get('/example')
def bad_example(
    # ❌ WRONG: Dependencies before simple required parameters
    service: IUserService,
    user_id: Annotated[int, UserId],

    # This will cause: "non-default argument follows default argument"
    item_id: int,
    q: str
) -> dict:
    return {"status": "error"}
```

**The rule:** Place required parameters (path params, required query params) **before** injected dependencies.

This is because under the hood, FastIoC transforms:
```python
service: IUserService
```
Into:
```python
service: IUserService = Depends(registered_service)
``` -->

## Async Endpoints

Both sync and async endpoints work identically:

```python
# project/routers/users.py
from project.interfaces import IUserService

@router.get('/sync')
def sync_endpoint(service: IUserService) -> dict:
    return service.get_user(1)

@router.get('/async')
async def async_endpoint(service: IUserService) -> dict:
    # Same syntax, FastAPI handles execution automatically
    return service.get_user(1)
```

Whether your dependency implementation is sync or async, FastAPI automatically handles the execution.

## Next Steps

- Understand [Passive Dependencies](passive.md) - using dependencies in route decorators
- Learn about [Dependency Lifetimes](lifetime.md) - singleton, scoped, and transient behaviors
- Explore [Nested Dependencies](nested.md) - automatic resolution of dependency chains
