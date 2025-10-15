# Nested Dependencies

Nested dependencies (also known as [Sub-dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/sub-dependencies/) in FastAPI) occur when a dependency itself depends on other dependencies. FastIoC fully supports nested dependencies with automatic resolution - just like FastAPI's native dependency injection.

FastIoC handles all the dependency resolution and passes them to FastAPI's `Depends()` under the hood, so everything works seamlessly.

## Basic Concept

When you register a dependency that requires other dependencies, FastIoC automatically resolves the entire dependency chain:

```python
# Service A depends on Service B
class ServiceB:
    def get_data(self) -> str:
        return "data from B"

class ServiceA:
    def __init__(self, service_b: IServiceB):
        self.service_b = service_b

    def process(self) -> str:
        return f"A processes: {self.service_b.get_data()}"

# Register both
container.add_scoped(IServiceB, ServiceB)
container.add_scoped(IServiceA, ServiceA)  # ServiceA automatically gets ServiceB injected
```

```python
@app.get('/process')
def process(service_a: IServiceA):
    # ServiceB is automatically resolved and injected into ServiceA
    return {"result": service_a.process()}
```

### ⚠️ Important: Registration Order

When registering nested dependencies, **inner dependencies must be registered before outer dependencies** that depend on them.

**Correct order:**

```python
# ✅ Register inner dependency first
container.add_scoped(IServiceB, ServiceB)      # Inner dependency
container.add_scoped(IServiceA, ServiceA)      # Outer dependency (depends on IServiceB)
```

**Wrong order:**

```python
# ❌ WRONG: Outer dependency registered first
container.add_scoped(IServiceA, ServiceA)      # Tries to resolve IServiceB, but it's not registered yet!
container.add_scoped(IServiceB, ServiceB)      # Too late
```

**What happens if the order is wrong:**

FastIoC won't find the dependency registration and will leave it as-is. FastAPI will then try to parse it as a request parameter or Pydantic model, which will fail and return **422 Unprocessable Entity** errors.

**If you encounter unexpected 422 errors, check that:**

1. All dependencies are registered in the container
2. Inner dependencies are registered before outer ones
3. See [Unregistered Dependencies troubleshooting](injectify.md#important-unregistered-dependencies) for more help

## Nested Dependencies in Functions and Generators

Functions and generators can depend on other registered dependencies:

```python
# project/dependencies.py
def get_database_url() -> str:
    return "postgresql://localhost/mydb"

def get_connection(db_url: DatabaseUrl) -> Connection:
    # db_url is automatically resolved
    return create_connection(db_url)

# project/container.py
container.add_scoped(DatabaseUrl, get_database_url)
container.add_scoped(IConnection, get_connection)
```

### With Generators

```python
from typing import Generator

def get_db_session(connection: IConnection) -> Generator[Session, None, None]:
    # connection is automatically resolved
    session = create_session(connection)
    try:
        yield session
    finally:
        session.close()

container.add_scoped(IDatabaseSession, get_db_session)
```

Both sync and async are supported - FastAPI handles them automatically.

## Nested Dependencies in Classes

Classes can resolve dependencies in two powerful ways: through `__init__` parameters and through class-level type hints.

### Method 1: Resolution in `__init__` (Standard)

This is the standard way - dependencies are resolved and passed to the `__init__` method:

```python
# project/services.py
class UserService:
    def __init__(
        self,
        db: IDatabaseSession,
        cache: ICacheService,
        logger: ILogger
    ):
        self.db = db
        self.cache = cache
        self.logger = logger

    def get_user(self, id: int) -> dict:
        self.logger.info(f"Getting user {id}")
        # Use self.db, self.cache, etc.
        return {"id": id}

container.add_scoped(IUserService, UserService)
```

You can mix FastIoC dependencies with FastAPI features:

```python
from fastapi import Header, Cookie

class AuthenticatedService:
    def __init__(
        self,
        # FastIoC dependencies
        db: IDatabaseSession,
        auth: IAuthService,

        # FastAPI features work too!
        authorization: Annotated[str, Header()],
        session_id: Annotated[str, Cookie()]
    ):
        self.db = db
        self.auth = auth
        self.token = authorization
        self.session = session_id
```

### Method 2: Resolution in Class Type Hints ⚡️

**This is FastIoC's unique feature!** You can declare dependencies as class-level type hints, and they'll be automatically resolved and available in all methods via `self`:

```python
# project/services.py
class OrderService:
    # Declare dependencies as class attributes (type hints only, no values!)
    db: IDatabaseSession
    payment: IPaymentService
    notification: INotificationService

    def create_order(self, user_id: int, amount: float):
        # All dependencies available via self!
        order = self.db.create_order(user_id, amount)
        self.payment.process(order)
        self.notification.send(order)
        return order

    def cancel_order(self, order_id: int):
        # Same dependencies available here too!
        order = self.db.get_order(order_id)
        self.payment.refund(order)
        self.notification.send_cancellation(order)

container.add_scoped(IOrderService, OrderService)
```

**How it works:**
- Dependency is resolved **once per class instance**
- Available in **all methods** via `self.attribute_name`
- No `__init__` needed for simple cases!

**Important Notes:**

1. **Attribute must not have a value** - If it has a default value, FastIoC ignores it:
   ```python
   class MyService:
       db: IDatabaseSession = None  # ❌ FastIoC ignores this (has default value)
       cache: ICacheService          # ✅ FastIoC injects this
   ```

2. **`__init__` parameter takes precedence** - If `__init__` has a parameter with the same name, FastIoC ignores the class hint:
   ```python
   class MyService:
       db: IDatabaseSession  # This will be ignored

       def __init__(self, db: CustomDB):
           # You're handling 'db' yourself
           self.db = db
   ```

3. **Works with FastAPI features** - You can use FastAPI's special annotations:
   ```python
   class APIService:
       # FastIoC dependencies
       db: IDatabaseSession

       # FastAPI features
       request: Request
       background: BackgroundTasks
       user_id: Annotated[int, Cookie()]
       api_key: Annotated[str, Header()]

       def process(self):
           # All available via self!
           cookies = self.request.cookies
           self.background.add_task(log_action)
           data = self.db.query(self.user_id)
           return data
   ```

   Supported FastAPI types: `Request`, `Response`, `BackgroundTasks`, `WebSocket`, `UploadFile`, `SecurityScopes`, and annotations like `Query`, `Body`, `Path`, `File`, `Form`, `Cookie`, `Header`, `Security`, or even `Depends()`.

4. **Lifetime consideration** - The dependency is resolved **once per class instance**, not per method call. Watch your [lifetime configurations](lifetime.md) carefully.

### Real-World Example

```python
# project/interfaces.py
from typing import Protocol

class IDatabaseSession(Protocol):
    def query(self, sql: str): ...

class IEmailService(Protocol):
    def send(self, to: str, message: str): ...

class ILogger(Protocol):
    def info(self, message: str): ...
```

```python
# project/services.py
from fastapi import BackgroundTasks, Request

class UserManagementService:
    # Dependencies as class attributes
    db: IDatabaseSession
    email: IEmailService
    logger: ILogger
    background: BackgroundTasks
    request: Request

    def create_user(self, username: str, email_addr: str):
        # All dependencies available!
        self.logger.info(f"Creating user: {username}")

        user = self.db.query(f"INSERT INTO users ...")

        # Queue email in background
        self.background.add_task(
            self.email.send,
            email_addr,
            "Welcome!"
        )

        # Access request info
        ip = self.request.client.host
        self.logger.info(f"User created from IP: {ip}")

        return user
```

```python
# project/container.py
container.add_scoped(IDatabaseSession, DatabaseSession)
container.add_scoped(IEmailService, EmailService)
container.add_singleton(ILogger, Logger)
container.add_scoped(IUserManagementService, UserManagementService)
```

No `__init__` needed - all dependencies are automatically available!

## Advanced: Instance-Based Dependencies

!!! note "Callable Instance Dependency Resolution"
    When using [callable class instances](register.md#callable-class-instances-advanced) (classes with `__call__`), only the **`__call__` method parameters** are injectified, **not** `__init__` or class-level type hints.

    This is because the actual dependency is the **instance**, not the class itself.

    ```python
    class RequestTracker:
        db: IDatabaseSession  # ❌ NOT injected (instance-based dependency)

        def __init__(self):
            # ❌ Parameters here are NOT injected
            self.count = 0

        def __call__(self, db: IDatabaseSession) -> dict:
            # ✅ Parameters here ARE injected
            self.count += 1
            return {"count": self.count, "db": db}

    tracker = RequestTracker()  # Create instance
    container.add_scoped(TrackerData, tracker)  # Register instance
    ```

## Lifetime Rules in Dependency Chains

When dependencies depend on other dependencies, their lifetimes must follow specific rules:

### Transient ✅ Can Depend on Anything

Transient dependencies can depend on **any** lifetime:

```python
class TransientService:
    def __init__(
        self,
        singleton: ISingletonService,    # ✅ OK
        scoped: IScopedService,           # ✅ OK
        transient: IAnotherTransient      # ✅ OK
    ):
        pass

container.add_transient(ITransientService, TransientService)
```

### Scoped ✅ Can Depend on Anything (with caution)

Scoped dependencies can technically depend on any lifetime, but be careful with transient:

```python
class ScopedService:
    def __init__(
        self,
        singleton: ISingletonService,    # ✅ OK
        scoped: IAnotherScoped,          # ✅ OK
        transient: ITransientService     # ⚠️ Works, but watch behavior!
    ):
        pass
```

**When depending on transient:** The transient dependency is created once when the scoped dependency is created, then reused for the request duration. It effectively becomes scoped. Make sure this is what you want!

### Singleton ⚠️ Can ONLY Depend on Singleton

Singletons **cannot** depend on scoped or transient dependencies:

```python
class SingletonService:
    def __init__(
        self,
        singleton: IAnotherSingleton,    # ✅ OK
        scoped: IScopedService           # ❌ ERROR!
    ):
        pass

container.add_singleton(ISingletonService, SingletonService)
# Raises SingletonLifetimeViolationError!
```

**Why?** A singleton lives for the entire application lifetime. If it depended on a scoped (per-request) or transient dependency, the singleton would capture the first instance and keep it forever, violating the intended lifetime.

### SingletonLifetimeViolationError

When you try to register a singleton that depends on a non-singleton, FastIoC raises `SingletonLifetimeViolationError`:

```python
from fastioc.errors import SingletonLifetimeViolationError

class UserService:
    def __init__(self, db: IDatabaseSession):  # Scoped!
        self.db = db

try:
    container.add_singleton(IUserService, UserService)
except SingletonLifetimeViolationError as e:
    print(f"Cannot register singleton: {e}")
    # Error: Singleton 'IUserService' cannot depend on scoped 'IDatabaseSession'
```

**Solution:** Register the dependency with a compatible lifetime:

```python
# Option 1: Make the service scoped too
container.add_scoped(IUserService, UserService)  # ✅ OK

# Option 2: Make the database singleton (if appropriate)
container.add_singleton(IDatabaseSession, DatabasePool)  # ✅ OK
```

## Advanced: Scoped Proxy Pattern

!!! info "Using Other Lifetimes for Scoped Proxy Behavior"
    If you need a singleton that can access scoped dependencies, use [callable instance dependencies](lifetime.md#advanced-callable-class-instances-with-lifetimes) with scoped lifetime.

    This creates a "scoped proxy" pattern (similar to Spring Boot):
    - The instance persists (singleton-like)
    - `__call__` is invoked per request (can access request context)
    - Can depend on scoped dependencies

    ```python
    class UserContextProxy:
        def __init__(self):
            self.request_count = 0  # Persists

        def __call__(self, db: IDatabaseSession) -> dict:  # Scoped!
            self.request_count += 1
            return {
                "count": self.request_count,
                "user": db.get_current_user()
            }

    proxy = UserContextProxy()
    container.add_scoped(UserContext, proxy)
    ```

    See [Callable Class Instances with Lifetimes](lifetime.md#advanced-callable-class-instances-with-lifetimes) for details.

## Dependency Chain Example

Here's a complete example showing a multi-level dependency chain:

```python
# Level 1: Database connection (singleton)
class ConnectionPool:
    def get_connection(self):
        return create_connection()

container.add_singleton(IConnectionPool, ConnectionPool)

# Level 2: Database session (scoped, depends on pool)
class DatabaseSession:
    pool: IConnectionPool  # Resolved via class hint!

    def query(self, sql: str):
        conn = self.pool.get_connection()
        return conn.execute(sql)

container.add_scoped(IDatabaseSession, DatabaseSession)

# Level 3: Repository (scoped, depends on session)
class UserRepository:
    db: IDatabaseSession

    def get_user(self, id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {id}")

container.add_scoped(IUserRepository, UserRepository)

# Level 4: Service (scoped, depends on repository)
class UserService:
    repo: IUserRepository
    logger: ILogger

    def get_user_with_logging(self, id: int):
        self.logger.info(f"Fetching user {id}")
        return self.repo.get_user(id)

container.add_singleton(ILogger, Logger)
container.add_scoped(IUserService, UserService)
```

```python
@app.get('/user/{user_id}')
def get_user(user_id: int, service: IUserService):
    # Entire chain is resolved automatically:
    # UserService � UserRepository � DatabaseSession � ConnectionPool + Logger
    return service.get_user_with_logging(user_id)
```

## Related Topics

- **[Dependency Lifetimes](lifetime.md)** - Understand singleton, scoped, and transient lifetimes
- **[Callable Class Instances](register.md#callable-class-instances-advanced)** - Advanced pattern for stateful dependencies
- **[SingletonLifetimeViolationError](reference/exceptions.md#singletonlifetimeviolationerror)** - API reference for lifetime violation errors

## Next Steps

- Learn about [Dependency Overrides](override.md) - replacing dependencies for testing
- Explore [Dispose](dispose.md) - cleaning up singleton resources
- Understand [Testing](testing.md) - testing with dependency injection
