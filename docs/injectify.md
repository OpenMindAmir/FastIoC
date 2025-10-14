# Injectification: Integrating FastIoC with FastAPI

Before you can use dependency injection in your FastAPI application, you need to "injectify" your FastAPI application and routers. This tells FastIoC to intercept and inject dependencies into your endpoints.

## Basic Usage

The `injectify()` method integrates FastIoC with your FastAPI application:

```python
# main.py
from fastapi import FastAPI
from fastioc import Container

container = Container()
app = FastAPI()

# Injectify the FastAPI app
container.injectify(app)

@app.get('/')
def index():
    return {"message": "Hello World"}
```

⚠️ **Important:** You must call `injectify()` **before** defining your endpoints (routes). If you define routes before injectifying, those routes won't have dependency injection enabled.

## Injectifying Routers

When working with [APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/), you must injectify each router individually. Here's a simple example:

```python
# main.py
from fastapi import FastAPI, APIRouter
from fastioc import Container

container = Container()
app = FastAPI()
router = APIRouter()

# Injectify both app and router
container.injectify(app, router)

# Now define endpoints
@app.get('/')
def index():
    return {"message": "Hello from app"}

@router.get('/items')
def list_items():
    return {"items": []}

# Include the router
app.include_router(router)
```

⚠️ **Important:** `app.include_router()` does **NOT** automatically injectify the router. You must explicitly call `container.injectify(router)` before defining endpoints on that router.

### Large-Scale Applications

In larger applications with multiple files, importing a router module executes the endpoint definitions. You need to set up your container in a separate file first:

```python
# project/container.py
from fastioc import Container
from project.interfaces import IUserService
from project.services import UserService

container = Container()

# Register dependencies
container.add_scoped(IUserService, UserService)
```

```python
# project/routers/users.py
from fastapi import APIRouter
from project.interfaces import IUserService
from project.container import container

router = APIRouter()

# Injectify the router before defining endpoints
container.injectify(router)

@router.get('/users/{user_id}')
def get_user(user_id: int, service: IUserService):
    return service.get_user(user_id)
```

```python
# main.py
from fastapi import FastAPI
from project.container import container
from project.routers import users

app = FastAPI()

# Injectify the app if you define endpoints directly on it
# container.injectify(app)

# Now include the router (already injectified)
app.include_router(users.router)
```

## Multiple Injectify Calls

You can call `injectify()` multiple times if needed. This is useful when you need to injectify components created at different times:

```python
# project/container.py
from fastioc import Container

container = Container()
# Register dependencies here...
```

```python
# project/routers/admin.py
from fastapi import APIRouter
from project.container import container

router = APIRouter()

# Injectify when the router is created
container.injectify(router)

@router.get('/admin/stats')
def get_stats():
    return {"stats": "data"}
```

```python
# main.py
from fastapi import FastAPI
from project.container import container

app = FastAPI()

# Injectify the main app
container.injectify(app)

# ... later in your code, dynamically load a router ...

from project.routers import admin

# Router is already injectified in its own module
app.include_router(admin.router)
```

This flexibility is particularly useful in scenarios where:
- Routers are dynamically loaded
- You're building modular applications
- Different parts of your app are initialized at different times

## Injectifying Multiple Targets

You can injectify multiple routers in a single call when they're created in the same file:

```python
# project/container.py
from fastioc import Container

container = Container()
# Register dependencies here...
```

```python
# project/routers.py
from fastapi import APIRouter
from project.container import container

users_router = APIRouter()
items_router = APIRouter()
dashboard_router = APIRouter()

# Injectify all routers at once before defining endpoints
container.injectify(users_router, items_router, dashboard_router)

@users_router.get('/users')
def list_users():
    return {"users": []}

@items_router.get('/items')
def list_items():
    return {"items": []}

@dashboard_router.get('/dashboard')
def get_dashboard():
    return {"data": "dashboard"}
```

```python
# main.py
from fastapi import FastAPI
from project.container import container
from project.routers import users_router, items_router, dashboard_router

app = FastAPI()

# Injectify the app
container.injectify(app)

# Include routers (already injectified)
app.include_router(users_router, prefix="/api")
app.include_router(items_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
```

## Registration Order

The order of `injectify()` and dependency registration doesn't matter, but both **must happen before defining endpoints** that use those dependencies:

### ✅ Register First, Then Injectify

```python
# project/container.py
from fastioc import Container
from project.interfaces import IUserService
from project.services import UserService

container = Container()

# Register dependencies first
container.add_scoped(IUserService, UserService)
```

```python
# main.py
from fastapi import FastAPI
from project.container import container

app = FastAPI()

# Then injectify
container.injectify(app)

# Then define endpoints
@app.get('/users/{id}')
def get_user(id: int, service: IUserService):
    return service.get_user(id)
```

### ✅ Injectify First, Then Register

```python
# main.py
from fastapi import FastAPI
from fastioc import Container

container = Container()
app = FastAPI()

# Injectify first
container.injectify(app)

# Then register dependencies
from project.interfaces import IUserService
from project.services import UserService
container.add_scoped(IUserService, UserService)

# Then define endpoints
@app.get('/users/{id}')
def get_user(id: int, service: IUserService):
    return service.get_user(id)
```

### ❌ Wrong: Endpoint Before Registration/Injectify

```python
from fastapi import FastAPI
from fastioc import Container

container = Container()
app = FastAPI()

# Define endpoint first (WRONG!)
@app.get('/users/{id}')
def get_user(id: int, service: IUserService):
    return service.get_user(id)

# Then injectify (TOO LATE!)
container.injectify(app)
container.add_scoped(IUserService, UserService)

# This endpoint won't have dependency injection
```

## ⚠️ Important: Unregistered Dependencies

If you request a dependency that hasn't been registered in the container, FastIoC will **not** raise an error during startup. Instead, FastAPI will treat it as a regular type annotation, and requests will fail with **422 Unprocessable Entity**.

```python
# project/interfaces.py
class IUserService(Protocol):
    def get_user(self, id: int) -> dict: ...

# main.py
container = Container()
app = FastAPI()

container.injectify(app)

# Forgot to register IUserService!
# container.add_scoped(IUserService, UserService)  # <- Missing!

@app.get('/users/{id}')
def get_user(id: int, service: IUserService):
    return service.get_user(id)

# Requests to this endpoint will return: 422 Unprocessable Entity
# Because FastAPI can't resolve IUserService
```

**Why this happens:** FastIoC assumes unregistered types are not meant to be dependencies from the container, so it doesn't interfere with them. FastAPI then tries to extract them from the request (like query parameters), which fails.

**Solution:** Always ensure you register your dependencies before they're used in endpoints:

```python
# ✅ Correct
container.add_scoped(IUserService, UserService)

@app.get('/users/{id}')
def get_user(id: int, service: IUserService):
    return service.get_user(id)
```

## Advanced: Multiple Containers

For advanced use cases, you can use different containers for different apps or routers. This is useful when you want to isolate dependencies between different parts of your application:

```python
from fastapi import FastAPI, APIRouter
from fastioc import Container

# Create separate containers
main_container = Container()
admin_container = Container()

app = FastAPI()
admin_router = APIRouter()

# Register different dependencies in each container
main_container.add_scoped(IUserService, UserService)
admin_container.add_scoped(IAdminService, AdminService)

# Injectify with different containers
main_container.injectify(app)
admin_container.injectify(admin_router)

@app.get('/users')
def list_users(service: IUserService):
    # Uses main_container dependencies
    return service.list_users()

@admin_router.get('/admin/users')
def admin_list_users(service: IAdminService):
    # Uses admin_container dependencies
    return service.list_admin_users()

app.include_router(admin_router)
```

This pattern allows you to:
- Isolate dependencies between different modules
- Use different implementations for the same interface in different parts of your app
- Create cleaner separation of concerns in large applications

## Next Steps

- Learn about [Dependency Registration](register.md) - how to register dependencies with the container
- Understand [Dependency Resolution](resolve.md) - how to use registered dependencies in endpoints
- Explore [Dependency Lifetimes](lifetime.md) - singleton, scoped, and transient behaviors
