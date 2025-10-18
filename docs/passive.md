# Passive Dependencies

Passive dependencies (also known as [path operation dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/)) are dependencies that run for every request but don't inject their return value into the endpoint function. They're useful for side effects like logging, authentication checks, or setting up request-scoped state.

FastIoC fully supports passive dependencies in endpoints, routers, and applications - just like regular FastAPI dependencies.

## Endpoint Passive Dependencies

You can add passive dependencies to individual endpoints using the `dependencies` parameter:

```python
# main.py
from fastapi import FastAPI, Depends
from project.interfaces import IAuthService, ILogService
from project.container import container

app = FastAPI()
container.injectify(app)

@app.get(
    '/protected',
    dependencies=[IAuthService, ILogService]  # pyright: ignore[reportArgumentType]
)
def protected_endpoint(data: str):
    # IAuthService and ILogService run before this function
    # but their return values are not injected here
    return {"data": data}
```

**Important:** Add `# pyright: ignore[reportArgumentType]` at the end of the line (or use your IDE's quick fix to ignore the error). Type checkers expect `dependencies` to be a list of `Depends()` objects, but FastIoC automatically converts your registered types to `Depends()` under the hood.

You can also mix FastIoC dependencies with traditional FastAPI dependencies:

```python
from fastapi import Depends

def some_fastapi_dep():
    print("Running FastAPI dependency")

@app.get(
    '/mixed',
    dependencies=[IAuthService, Depends(some_fastapi_dep)]  # pyright: ignore[reportArgumentType]
)
def mixed_endpoint():
    return {"status": "ok"}
```

## Router Passive Dependencies

Apply passive dependencies to all endpoints in a router:

```python
# project/routers/admin.py
from fastapi import APIRouter, Depends
from project.interfaces import IAdminAuthService, IAuditService
from project.container import container

router = APIRouter(
    prefix="/admin",
    dependencies=[IAdminAuthService, IAuditService]  # pyright: ignore[reportArgumentType]
)

container.injectify(router)

@router.get('/users')
def list_admin_users():
    # IAdminAuthService and IAuditService run for every endpoint in this router
    return {"users": []}

@router.get('/settings')
def get_admin_settings():
    # Same dependencies run here too
    return {"settings": {}}
```

All endpoints in the router will automatically have these dependencies executed before the endpoint handler.

## Application Passive Dependencies

Apply passive dependencies to all endpoints in your entire application (also known as [Global Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/global-dependencies/) in FastAPI):

```python
# main.py
from fastapi import FastAPI, Depends
from project.interfaces import IGlobalLogger, IRequestTracker
from project.container import container

app = FastAPI(
    dependencies=[IGlobalLogger, IRequestTracker]  # pyright: ignore[reportArgumentType]
)

container.injectify(app)

@app.get('/endpoint1')
def endpoint1():
    # IGlobalLogger and IRequestTracker run here
    return {"endpoint": 1}

@app.get('/endpoint2')
def endpoint2():
    # And here too - for every endpoint
    return {"endpoint": 2}
```

Every endpoint in the application will execute these dependencies.

## Combining Passive Dependencies

You can combine passive dependencies at different levels - they all stack together:

```python
# main.py
from fastapi import FastAPI, APIRouter, Depends
from project.interfaces import IGlobalLogger, IAuthService, IRateLimiter
from project.container import container

# Application-level: runs for ALL endpoints
app = FastAPI(
    dependencies=[IGlobalLogger]  # pyright: ignore[reportArgumentType]
)

# Router-level: runs for all endpoints in this router
admin_router = APIRouter(
    prefix="/admin",
    dependencies=[IAuthService]  # pyright: ignore[reportArgumentType]
)

container.injectify(app, admin_router)

# Endpoint-level: runs only for this specific endpoint
@admin_router.get(
    '/critical',
    dependencies=[IRateLimiter]  # pyright: ignore[reportArgumentType]
)
def critical_operation():
    # All three run: IGlobalLogger � IAuthService � IRateLimiter
    return {"status": "executed"}

@admin_router.get('/normal')
def normal_operation():
    # Only two run: IGlobalLogger � IAuthService
    return {"status": "ok"}

app.include_router(admin_router)
```

The dependencies execute in order from broadest to most specific:
1. Application-level dependencies
2. Router-level dependencies
3. Endpoint-level dependencies

## Type Checker Warnings

When using FastIoC dependencies in the `dependencies` parameter, your IDE or type checker (like Pyright, mypy) will show an error because it expects `Depends()` objects:

```python
# Type checker will complain about this:
@app.get('/endpoint', dependencies=[IUserService])
#                                    ^^^^^^^^^^^
# Expected type 'Depends', got 'type[IUserService]'
```

**Solutions:**

### Option 1: Inline Comment (Recommended)

```python
@app.get('/endpoint', dependencies=[IUserService])  # pyright: ignore[reportArgumentType]
```

### Option 2: Type Ignore Comment

```python
@app.get('/endpoint', dependencies=[IUserService])  # type: ignore
```

### Option 3: IDE Quick Fix

Most IDEs (VS Code, PyCharm) offer quick fixes to suppress these warnings. Use the IDE's suggestion feature to add the appropriate ignore comment.

**Why this happens:** FastIoC intercepts these dependencies and converts them to `Depends()` automatically during the injectify process. The type checker doesn't know about this runtime transformation, so it sees a type mismatch.

## Use Cases for Passive Dependencies

Passive dependencies are ideal for:

- **Authentication/Authorization** - Validate tokens, check permissions
- **Logging/Monitoring** - Log requests, track metrics
- **Rate Limiting** - Throttle requests per user/IP
- **Request Validation** - Check headers, validate API keys
- **Database Transactions** - Set up transaction context
- **Caching** - Check cache validity
- **Feature Flags** - Enable/disable features per request
- **Audit Trails** - Record who accessed what

Since passive dependencies don't inject their return values, they're perfect for side effects that don't need to pass data to the endpoint.

## Next Steps

- Learn about [Dependency Lifetimes](lifetime.md) - singleton, scoped, and transient behaviors
- Explore [Nested Dependencies](nested.md) - automatic resolution of dependency chains
