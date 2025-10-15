# APIController

The `APIController` is FastIoC's powerful class-based view system that brings modern controller patterns to FastAPI. It allows you to organize related endpoints into classes with shared attributes, variables, methods, and dependencies making your code more maintainable and easier to scale.

## Why Use APIController?

Traditional FastAPI function-based views work great for simple APIs, but as your application grows, you'll find yourself:
- Repeating dependency injections across multiple related endpoints
- Creating helper functions that need access to the same services
- Struggling to organize related endpoint logic
- Missing the benefits of class-based organization

`APIController` solves these problems by letting you:
- **Share dependencies** across all endpoints in the controller
- **Group related endpoints** in a single, organized class
- **Reuse methods and attributes** across multiple routes
- **Keep your code DRY** by avoiding repetition

## Importing APIController

```python
from fastioc.controller import (
    APIController,  # Base controller class
    # HTTP method decorators (same as FastAPI)
    get,
    post,
    put,
    patch,
    delete,
    head,
    options,
    trace,
    websocket
)
```

All HTTP method decorators work exactly like their FastAPI counterparts (`@app.get`, `@app.post`, etc.), but are designed for use in controllers.

## Basic Usage

### Minimal Controller

Here's the simplest possible controller:

```python
from fastapi import FastAPI
from fastioc.controller import APIController, get

class HealthController(APIController):
    config = {
        'prefix': '/health'
    }

    @get('/')
    def check_health(self):
        return {"status": "healthy"}

# Create FastAPI app and include the controller
app = FastAPI()
app.include_router(HealthController.router())  # Call .router() class method
```

**Important**: Use `HealthController.router()` (class method), not `HealthController().router()` (instance method). Don't create instances yourself FastAPI handles that internally.

## Configuration with IDE Support

The `config` dictionary contains all `APIRouter` parameters plus the FastIoC container. It provides full IDE autocomplete and type hints:

```python
from fastioc import Container
from fastioc.controller import APIController, get

container = Container()
# Register your dependencies...

class UserController(APIController):
    config = {
        'prefix': '/users',                    # Router prefix
        'tags': ['Users'],                     # OpenAPI tags
        'container': container,                # FastIoC container (required for DI)
        'dependencies': [IAuthService],        # Shared dependencies for all routes
        'deprecated': False,                   # Mark all routes as deprecated
        'include_in_schema': True,             # Include in OpenAPI schema
        # ... all other APIRouter parameters are supported
    }

    @get('/')
    def list_users(self):
        return {"users": []}
```

**All `APIRouter` parameters are supported**, including:
- `prefix`, `tags`, `dependencies`, `responses`
- `callbacks`, `routes`, `redirect_slashes`
- `default_response_class`, `route_class`
- `on_startup`, `on_shutdown`, `lifespan`
- `include_in_schema`, `deprecated`
- `generate_unique_id_function`
- And more...

For type hints, import the `APIRouterParams` type:

```python
from fastioc.controller.definitions import APIRouterParams

config: APIRouterParams = {
    'prefix': '/api',
    'container': container
}
```

## Using Dependency Injection

### With Container

To use FastIoC's dependency injection, you **must** pass your container in the config:

```python
from fastioc import Container
from fastioc.controller import APIController, get, post

# Setup container
container = Container()
container.add_scoped(IUserService, UserService)
container.add_scoped(IEmailService, EmailService)

class UserController(APIController):
    config = {
        'prefix': '/users',
        'container': container  # Required for DI
    }

    @get('/{user_id}')
    def get_user(self, user_id: int, service: IUserService):
        # service is automatically injected
        return service.get_user(user_id)

    @post('/')
    def create_user(self, user: UserCreate, service: IUserService):
        return service.create_user(user)
```

### Without Container

If you don't need dependency injection, simply omit the container:

```python
class SimpleController(APIController):
    config = {
        'prefix': '/simple'
        # No container needed
    }

    @get('/')
    def hello(self):
        return {"message": "Hello World"}
```

## Shared Dependencies and Data

One of the most powerful features of `APIController` is the ability to share dependencies, data, and methods across all endpoints.

### Shared Dependencies via Class Type Hints

Use [class-level type hints](nested.md#method-2-resolution-in-class-type-hints) to inject dependencies that are available in all endpoints:

```python
class ProductController(APIController):
    config = {
        'prefix': '/products',
        'container': container
    }

    # Shared dependencies - available in ALL endpoints
    db: IDatabaseService
    cache: ICacheService
    logger: ILoggerService

    @get('/')
    def list_products(self):
        # Access shared dependencies via self
        self.logger.log("Listing products")
        products = self.db.query("SELECT * FROM products")
        return {"products": products}

    @get('/{product_id}')
    def get_product(self, product_id: int):
        # Same dependencies available here
        cached = self.cache.get(f"product:{product_id}")
        if cached:
            return cached

        product = self.db.query(f"SELECT * FROM products WHERE id = {product_id}")
        self.cache.set(f"product:{product_id}", product)
        return {"product": product}
```

### Shared Data from FastAPI (Request Data)

You can also share request data (query params, headers, etc.) across endpoints. See [Passing Data to Dependencies - Pattern 1](data.md#pattern-1-fastapi-native-dependencies) for full details.

**In Class Type Hints**, you must use `Annotated` with FastAPI's parameter types:

```python
from fastapi import Query, Header
from typing import Annotated

class ApiController(APIController):
    config = {
        'prefix': '/api',
        'container': container
    }

    # ✅ CORRECT: Use Annotated for request data in class hints
    api_key: Annotated[str, Header()]
    page: Annotated[int, Query(default=1)]

    # L WRONG: Simple types don't work
    # api_key: str  # Won't receive header!

    # ✅ FastIoC dependencies work as usual
    service: IApiService

    @get('/data')
    def get_data(self):
        # api_key and page are available
        self.service.authenticate(self.api_key)
        return self.service.fetch_data(page=self.page)
```

**In `__init__` Parameters**, FastAPI parameters work normally (no `Annotated` needed):

```python
from fastapi import Query, Header, Depends
from typing import Annotated

def get_auth_token(authorization: str = Header()) -> str:
    return authorization.replace("Bearer ", "")

class AuthController(APIController):
    config = {
        'prefix': '/auth',
        'container': container
    }

    # Receive data in __init__ - works like normal FastAPI
    def __init__(
        self,
        user_id: int = Query(),
        token: Annotated[str, Depends(get_auth_token)] = None,
        service: IAuthService = None  # From container
    ):
        self.user_id = user_id
        self.token = token
        self.service = service

    @get('/profile')
    def get_profile(self):
        return self.service.get_user_profile(self.user_id, self.token)
```

See [Nested Dependencies - Class Type Hints](nested.md#method-2-resolution-in-class-type-hints) for more details.

### Shared Methods

You can define helper methods that all endpoints can use:

```python
class OrderController(APIController):
    config = {
        'prefix': '/orders',
        'container': container
    }

    db: IDatabaseService
    logger: ILoggerService

    def _log_action(self, action: str, order_id: int):
        """Helper method shared by all endpoints"""
        self.logger.log(f"{action} order {order_id}")

    def _validate_order(self, order_id: int) -> bool:
        """Another helper method"""
        return self.db.exists("orders", order_id)

    @get('/{order_id}')
    def get_order(self, order_id: int):
        self._log_action("GET", order_id)
        if not self._validate_order(order_id):
            raise HTTPException(404, "Order not found")
        return self.db.query(f"SELECT * FROM orders WHERE id = {order_id}")

    @delete('/{order_id}')
    def delete_order(self, order_id: int):
        self._log_action("DELETE", order_id)
        if not self._validate_order(order_id):
            raise HTTPException(404, "Order not found")
        self.db.execute(f"DELETE FROM orders WHERE id = {order_id}")
        return {"status": "deleted"}
```

## Complete Example

Here's a comprehensive example showing all features together:

```python
from fastapi import FastAPI, Query, Header, HTTPException
from fastioc import Container
from fastioc.controller import APIController, get, post, put, delete
from typing import Annotated

# Setup container
container = Container()
container.add_scoped(IUserService, UserService)
container.add_scoped(IAuthService, AuthService)
container.add_scoped(ILoggerService, LoggerService)

# Define controller
class UserController(APIController):
    config = {
        'prefix': '/users',
        'tags': ['Users'],
        'container': container,
        'dependencies': [IAuthService]  # Runs on all routes
    }

    # Shared dependencies via class hints
    service: IUserService
    logger: ILoggerService

    # Shared request data via class hints (must use Annotated)
    api_version: Annotated[str, Header(alias="X-API-Version", default="1.0")]

    # Receive data in __init__
    def __init__(
        self,
        page_size: int = Query(10, ge=1, le=100)
    ):
        self.page_size = page_size

    # Helper method
    def _log(self, message: str):
        self.logger.log(f"[v{self.api_version}] {message}")

    @get('/')
    def list_users(self, page: int = Query(1, ge=1)):
        self._log(f"Listing users - page {page}")
        users = self.service.get_users(
            skip=(page - 1) * self.page_size,
            limit=self.page_size
        )
        return {"users": users, "page": page}

    @get('/{user_id}')
    def get_user(self, user_id: int):
        self._log(f"Getting user {user_id}")
        user = self.service.get_user(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return {"user": user}

    @post('/')
    def create_user(self, user: UserCreate):
        self._log(f"Creating user: {user.email}")
        new_user = self.service.create_user(user)
        return {"user": new_user, "created": True}

    @put('/{user_id}')
    def update_user(self, user_id: int, user: UserUpdate):
        self._log(f"Updating user {user_id}")
        updated = self.service.update_user(user_id, user)
        return {"user": updated}

    @delete('/{user_id}')
    def delete_user(self, user_id: int):
        self._log(f"Deleting user {user_id}")
        self.service.delete_user(user_id)
        return {"status": "deleted", "user_id": user_id}

# Include in FastAPI app
app = FastAPI()
app.include_router(UserController.router())
```

## Runtime Configuration with `router()`

Sometimes you want to keep your controller abstract and provide configuration when including it in your app. You can pass an optional configuration dictionary to the `router()` class method:

```python
from fastioc.controller.definitions import APIRouterParams

# Abstract controller (no config)
class GenericController(APIController):
    @get('/')
    def index(self):
        return {"message": "Hello"}

# Provide config at runtime
app = FastAPI()

# Option 1: Dictionary
app.include_router(GenericController.router({
    'prefix': '/api/v1',
    'tags': ['API V1']
}))

# Option 2: Typed dictionary for IDE support
config: APIRouterParams = {
    'prefix': '/api/v2',
    'tags': ['API V2'],
    'deprecated': True
}
app.include_router(GenericController.router(config))
```

**⚠️ Important**: The runtime config **completely replaces** the class config. It doesn't merge it replaces. If you don't provide a key, it uses the default value:

```python
class MyController(APIController):
    config = {
        'prefix': '/original',
        'tags': ['Original'],
        'container': container
    }

    @get('/')
    def index(self):
        return {}

# Runtime config REPLACES class config
app.include_router(MyController.router({
    'prefix': '/new'
    # 'tags' is not provided ⚠️ uses default (empty)
    # 'container' is not provided ⚠️ uses default (None, DI won't work!)
}))

# Result:
# - prefix: '/new'
# - tags: []  (not ['Original'])
# - container: None  (not the original container!)
```

If you need to keep some values from the class config, you must explicitly include them in the runtime config.

## Controller Dependencies in Config

You can specify dependencies that apply to **all routes** in the controller via the `dependencies` key:

```python
container = Container()
container.add_singleton(IGlobalService, GlobalService)
container.add_singleton(IAuthService, AuthService)

class SecureController(APIController):
    config = {
        'prefix': '/secure',
        'container': container,
        'dependencies': [IGlobalService, IAuthService]  # Run on ALL routes
    }

    @get('/data')
    def get_data(self):
        # IGlobalService and IAuthService are resolved for this route
        return {"data": "secure"}

    @post('/update')
    def update_data(self):
        # Same dependencies apply here too
        return {"status": "updated"}
```

You can also add route-specific dependencies using the decorator:

```python
class MixedController(APIController):
    config = {
        'prefix': '/mixed',
        'container': container,
        'dependencies': [IGlobalService]  # All routes
    }

    @get('/public')
    def public_route(self):
        # Only IGlobalService
        return {"public": True}

    @get('/admin', dependencies=[IAdminService])  # Additional dependency
    def admin_route(self):
        # Both IGlobalService AND IAdminService
        return {"admin": True}
```

## Key Points

- Use `APIController` to organize related endpoints into classes
- Import HTTP decorators from `fastioc.controller`: `get`, `post`, `put`, `delete`, etc.
- Configure via the `config` dictionary (full IDE support)
- Pass `container` in config to enable dependency injection (optional)
- Use class type hints for shared dependencies (available in all endpoints)
- Use `Annotated` for request data in class hints; normal syntax in `__init__`
- Call `Controller.router()` as a **class method**, not on an instance
- Optionally pass runtime config to `router()` for abstract controllers
- Runtime config **replaces** class config completely (doesn't merge)

## Related Documentation

- [Passing Data to Dependencies - Pattern 1: FastAPI Native Dependencies](data.md#pattern-1-fastapi-native-dependencies)
- [Nested Dependencies - Class Type Hints](nested.md#method-2-resolution-in-class-type-hints)
- [FastAPI APIRouter Documentation](https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter)
