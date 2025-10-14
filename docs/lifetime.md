# Dependency Lifetimes

Dependency lifetimes control how long a dependency instance lives and when it gets created. FastIoC provides three lifetime options: **Scoped**, **Transient**, and **Singleton**.

Understanding lifetimes is crucial for managing resources, state, and performance in your application.

## Scoped

**Created once per request**. This is equivalent to FastAPI's `Depends(...)`.

```python
container.add_scoped(IUserService, UserService)
```

**When to use:**
- Database connections/sessions
- Request-specific state
- User context for the current request
- Services that need isolation between requests

**Behavior:**
- Created once at the start of each request
- Same instance throughout **one request**
- Different instance for **each request**
- Disposed at the end of the request

### Class Example

```python
# project/services.py
class DatabaseSession(IDatabaseSession):
    def __init__(self):
        self.connection = create_connection()
        print(f"DatabaseSession created: {id(self)}")

    def query(self, sql: str):
        return self.connection.execute(sql)

# project/container.py
container.add_scoped(IDatabaseSession, DatabaseSession)
```

```python
# When you make requests:
# Request 1: DatabaseSession created: 140234567890  ← New instance
#            (same instance used throughout request 1)
# Request 2: DatabaseSession created: 140234599999  ← New instance
#            (same instance used throughout request 2)
```

**Note:** For classes, the **instance** is cached per request.

### Function Example

```python
# project/dependencies.py
def get_current_user_id() -> int:
    # Simulate expensive operation
    user_id = extract_from_token()
    print(f"Extracted user_id: {user_id}")
    return user_id

# project/container.py
container.add_scoped(CurrentUserId, get_current_user_id)
```

```python
@app.get('/profile')
def get_profile(user_id1: CurrentUserId, user_id2: CurrentUserId):
    # Extracted user_id: 42  ← Called once per request
    # user_id1 and user_id2 are the same cached value
    assert user_id1 == user_id2  # ✅ True
    return {"user_id": user_id1}
```

**Note:** For functions, the **return value** is cached per request, not the function instance.

### Generator Example

Generators are perfect for scoped dependencies when you need setup and teardown:

```python
# project/dependencies.py
from typing import Generator

def get_db_session() -> Generator[DatabaseSession, None, None]:
    print("Opening database connection")
    session = create_session()

    try:
        yield session  # Provided to the endpoint
    finally:
        print("Closing database connection")
        session.close()  # Cleanup runs at request end

# project/container.py
container.add_scoped(IDatabaseSession, get_db_session)
```

```python
# Request lifecycle:
# 1. "Opening database connection"  ← Setup (before endpoint)
# 2. Endpoint executes with session
# 3. "Closing database connection"  ← Cleanup (after endpoint)
```

**Both sync and async generators are supported** - FastAPI handles them automatically:

```python
async def get_async_session() -> AsyncGenerator[Session, None]:
    print("Opening async connection")
    session = await create_async_session()

    try:
        yield session
    finally:
        print("Closing async connection")
        await session.close()
```

## Transient

**Created every time** it's requested. This is equivalent to FastAPI's `Depends(..., use_cache=False)`.

```python
container.add_transient(IEmailService, EmailService)
```

**When to use:**
- Lightweight services
- Stateless operations
- Services used once and discarded
- When you need a fresh instance every time

**Behavior:**
- Created **every time** it's injected
- Different instance **even within the same request**
- Multiple injections = multiple instances
- Disposed immediately after use

### Class Example

```python
# project/services.py
class EmailService:
    def __init__(self):
        print(f"EmailService created: {id(self)}")

    def send(self, to: str, message: str):
        print(f"Sending email to {to}")

# project/container.py
container.add_transient(IEmailService, EmailService)
```

```python
@app.get('/send')
def send_emails(
    email1: IEmailService,
    email2: IEmailService
):
    # EmailService created: 140234567890  ← First injection
    # EmailService created: 140234599999  ← Second injection (different instance!)
    email1.send("user1@example.com", "Hello")
    email2.send("user2@example.com", "World")
    return {"sent": 2}
```

**Note:** For classes, a **new instance** is created every time.

### Function Example

```python
# project/dependencies.py
import uuid

def generate_request_id() -> str:
    request_id = str(uuid.uuid4())
    print(f"Generated request_id: {request_id}")
    return request_id

# project/container.py
container.add_transient(RequestId, generate_request_id)
```

```python
@app.get('/track')
def track(id1: Annotated[str, RequestId], id2: Annotated[str, RequestId]):
    # Generated request_id: abc-123  ← First call
    # Generated request_id: def-456  ← Second call (different value!)
    return {"id1": id1, "id2": id2}
```

**Note:** For functions, the function is **called every time**, returning a fresh value.

### Generator Example

Transient generators are useful for one-time resource management:

```python
# project/dependencies.py
from typing import Generator

def get_temp_file() -> Generator[str, None, None]:
    filepath = create_temp_file()
    print(f"Created temp file: {filepath}")

    try:
        yield filepath
    finally:
        delete_temp_file(filepath)
        print(f"Deleted temp file: {filepath}")

# project/container.py
container.add_transient(TempFile, get_temp_file)
```

```python
@app.post('/process')
def process(file1: TempFile, file2: TempFile):
    # Created temp file: /tmp/abc  ← First injection
    # Created temp file: /tmp/def  ← Second injection
    # ... endpoint logic ...
    # Deleted temp file: /tmp/abc  ← Cleanup after endpoint
    # Deleted temp file: /tmp/def  ← Cleanup after endpoint
    return {"processed": 2}
```

**Both sync and async generators are supported** - FastAPI handles them automatically.

## Singleton

**Created once** for the entire application lifetime.

```python
container.add_singleton(IConfigService, ConfigService)
```

**When to use:**
- Configuration that doesn't change
- Shared caches
- Connection pools
- Application-wide state
- Services without request-specific state

**Behavior:**
- Created on first use
- Same instance for **every request**
- Lives until application shutdown
- Shared across all requests and users

### Class Example

```python
# project/services.py
class ConfigService(IConfigService):
    def __init__(self):
        self.config = load_config()
        print(f"ConfigService created: {id(self)}")

    def get_setting(self, key: str) -> str:
        return self.config.get(key)

# project/container.py
container.add_singleton(IConfigService, ConfigService)
```

```python
# When you make requests:
# Request 1: ConfigService created: 140234567890  ← Created once
# Request 2: (uses same instance)
# Request 3: (uses same instance)
```

**Note:** For classes, the **instance** is cached for the entire application lifetime.

### Function Example

```python
# project/dependencies.py
def load_app_config() -> dict:
    print("Loading configuration from file")
    config = read_config_file()
    return config

# project/container.py
container.add_singleton(AppConfig, load_app_config)
```

```python
# First request:
# Loading configuration from file  ← Called once
# ... returns config dict ...

# Subsequent requests:
# (returns cached config dict, function never called again)
```

**Note:** For functions, the **return value** is cached for the entire application lifetime.

### No Generators Allowed

Singletons **cannot** be generators or async generators:

```python
# ❌ WRONG: This will raise SingletonGeneratorError
def get_database() -> Generator[Database, None, None]:
    db = Database()
    try:
        yield db
    finally:
        db.close()

container.add_singleton(IDatabaseSession, get_database)  # ❌ Error!
```

**Why?** Generators can only be used once. After yielding a value and reaching the end, they cannot be reused. Since singletons are meant to be reused across the entire application, generators don't make sense as singletons.

See the [`SingletonGeneratorError` API reference](reference/exceptions#singletongeneratorerror) for more details.

**Solution 1:** Use a regular *class* or *function* for singletons:

```python
# ✅ CORRECT: Use a class
class DatabasePool:
    def __init__(self):
        self.pool = create_connection_pool()

    def get_connection(self):
        return self.pool.get_connection()

container.add_singleton(IDatabasePool, DatabasePool)  # ✅ OK
```

**Solution 2:** Use scoped/transient for generators:

```python
# ✅ CORRECT: Use scoped for generators
container.add_scoped(IDatabaseSession, get_database)  # ✅ OK
```

**⚡️Solution 3:** If you need cleanup for singleton resources, use the [dispose feature](dispose.md):

```python
# ✅ CORRECT: Use singleton with dispose for cleanup
class DatabasePool:
    def __init__(self):
        self.pool = create_connection_pool()

    def __dispose__(self): # also you can use `async def`, FastIoC will automatically handle it
        self.pool.close_all()

container.add_singleton(IDatabasePool, DatabasePool)
# Cleanup will run at application shutdown (see dispose documentation)
```
⚠️ **Note**: before using this feature you must config it first, see [here](dispose.md).

## Lifetime Comparison

| Lifetime | Created | Shared | Disposed | FastAPI Equivalent |
|----------|---------|--------|----------|-------------------|
| **Scoped** | Once per request | Within same request | At request end | `Depends(...)` |
| **Transient** | Every injection | Never shared | After use | `Depends(..., use_cache=False)` |
| **Singleton** | Once per application | Across all requests | At app shutdown | *(Not directly available in FastAPI)* |

## Visual Example

Here's how different lifetimes behave across requests:

```python
from project.interfaces import IConfigService, IDatabaseSession, IEmailService
from project.container import container

# Register with different lifetimes
container.add_singleton(IConfigService, ConfigService)
container.add_scoped(IDatabaseSession, DatabaseSession)
container.add_transient(IEmailService, EmailService)

@app.get('/example')
def example(
    config1: IConfigService,
    config2: IConfigService,
    db1: IDatabaseSession,
    db2: IDatabaseSession,
    email1: IEmailService,
    email2: IEmailService
):
    # Singleton: config1 and config2 are THE SAME instance
    assert config1 is config2  # ✅ True

    # Scoped: db1 and db2 are THE SAME instance (within this request)
    assert db1 is db2  # ✅ True

    # Transient: email1 and email2 are DIFFERENT instances
    assert email1 is not email2  # ✅ True

    return {"status": "ok"}
```

**Output across two requests:**

```
Request 1:
  ConfigService created: 12345      ← Singleton (created once)
  DatabaseSession created: 67890    ← Scoped (new for request 1)
  EmailService created: 11111       ← Transient (new for email1)
  EmailService created: 22222       ← Transient (new for email2)

Request 2:
  (ConfigService reused: 12345)     ← Singleton (same instance)
  DatabaseSession created: 99999    ← Scoped (new for request 2)
  EmailService created: 33333       ← Transient (new for email1)
  EmailService created: 44444       ← Transient (new for email2)
```

## Choosing the Right Lifetime

Use this decision tree:

```
Does it need to be shared across ALL requests?
├─ YES → Use Singleton
│         (config, caches, connection pools)
│
└─ NO → Does it need to be shared within ONE request?
         ├─ YES → Use Scoped
         │         (database sessions, request context)
         │
         └─ NO → Use Transient
                   (lightweight services, one-time operations)
```

**Common Patterns:**

```python
# Singleton: Application-wide shared state
container.add_singleton(IConfiguration, ProductionConfiguration)
container.add_singleton(ICache, RedisCache)
container.add_singleton(IConnectionPool, DatabasePool)

# Scoped: Per-request state
container.add_scoped(IDatabaseSession, AsyncPostgreSQLDatabaseSession)
container.add_scoped(ICurrentUser, CurrentUserContext)
container.add_scoped(IUnitOfWork, UnitOfWork)

# Transient: Stateless operations
container.add_transient(IEmailSender, GoogleEmailSender)
container.add_transient(IDataValidator, TransactionDataValidator)
container.add_transient(ILogger, InfluxDBLogger)
```

## Advanced: Callable Class Instances with Lifetimes

When using [callable class instances](register.md#callable-class-instances-advanced) (classes with `__call__` method), the lifetime behavior works differently because you're registering an **instance** rather than a class or function.

### ❌ With Singleton (Not Recommended)

When you register a callable instance as singleton, FastIoC calls `__call__` **once** and caches that **return value** for the entire application lifetime:

```python
class Counter:
    def __init__(self):
        self.count = 0

    def __call__(self) -> int:
        self.count += 1
        return self.count

counter_instance = Counter()
container.add_singleton(CounterValue, counter_instance)
```

```python
@app.get('/count1')
def get_count1(value: CounterValue):
    return {"count": value}  # Always returns 1

@app.get('/count2')
def get_count2(value: CounterValue):
    return {"count": value}  # Always returns 1 (same cached value!)
```

**What happens:**
1. First request: `__call__()` is invoked → returns `1` → cached
2. All subsequent requests: The cached value `1` is returned, `__call__()` is never called again

This is usually **not** what you want with callable instances. Only use singleton for callable instances if you fully understand this behavior and it's exactly what you need.

### ⚡️With Scoped (Recommended)

This is where callable instances shine! When registered as scoped, the **instance persists** but `__call__` is invoked once per request. This gives you a "scoped proxy" pattern (similar to Spring Boot), allowing you to:

- Maintain state across the application lifetime (the instance persists)
- Access request-specific context when `__call__` is invoked
- Combine singleton-like persistence with per-request execution

```python
class RequestContextTracker:
    def __init__(self):
        self.total_requests = 0  # Persists across all requests
        self.request_ids = []

    def __call__(self, request: Request) -> dict:
        # Called once per request - has access to request context!
        self.total_requests += 1
        request_id = request.headers.get("X-Request-ID")
        self.request_ids.append(request_id)

        return {
            "current_request_id": request_id,
            "total_requests": self.total_requests
        }

tracker = RequestContextTracker()
container.add_scoped(RequestContext, tracker)
```

```python
@app.get('/stats')
def get_stats(context: RequestContext):
    # Request 1: {"current_request_id": "abc", "total_requests": 1}
    # Request 2: {"current_request_id": "def", "total_requests": 2}
    # The instance state accumulates across requests!
    return context
```

**Thanks to Python's flexibility**, the instance can access both:
- **Application-wide state** (instance attributes persist)
- **Request-specific context** (when `__call__` is invoked per request)

### ⚡️With Transient

With transient lifetime, `__call__` is invoked **every time** the dependency is injected, even within the same request:

```python
class UniqueIdGenerator:
    def __init__(self):
        self.generated_count = 0  # Persists across all calls

    def __call__(self) -> str:
        # Called every injection
        self.generated_count += 1
        return f"id-{self.generated_count}"

id_gen = UniqueIdGenerator()
container.add_transient(UniqueId, id_gen)
```

```python
@app.get('/ids')
def get_ids(id1: UniqueId, id2: UniqueId):
    # id1: "id-1"  ← First injection
    # id2: "id-2"  ← Second injection (different value!)
    # Instance state persists: generated_count = 2
    return {"id1": id1, "id2": id2}
```

This pattern allows you to generate unique values while maintaining global state about how many have been generated.

## Related Topics

- **[Callable Class Instances](register.md#callable-class-instances-advanced)** - Learn about using callable instances as dependencies
- **[Nested Dependencies](nested.md)** - Understand lifetime rules when dependencies depend on other dependencies, including [`SingletonLifetimeViolationError`](nested.md#singleton-lifetime-violation)
- **[Dispose (Singleton Clean-up)](dispose.md)** - Learn how to properly dispose of singleton resources when the application shuts down

## Advanced: Singletons in Production Deployments

!!! warning "Multiprocessing and Thread Safety Considerations"
    When deploying FastAPI with multiple workers (using Gunicorn, Uvicorn workers, etc.), be aware of these singleton behaviors:

    ### One Singleton Per Worker Process
    When you deploy with multiple workers, **each worker process gets its own singleton instance**:

    ```bash
    # Running with 4 workers
    uvicorn main:app --workers 4
    ```

    This creates **4 separate singleton instances** - one per worker. Singletons are **not** shared across worker processes. Each worker has its own isolated Python interpreter and memory space.

    **Implications:**
    - Singleton state is not shared between workers
    - In-memory caches are duplicated across workers
    - Counters and statistics are per-worker, not global
    - If you need true application-wide state, use external storage (Redis, database, etc.)

    ### Thread Safety
    When using singleton dependencies in a multiprocessing/multithreaded environment, ensure your singleton objects are **thread-safe**:

    ```python
    # ❌ NOT thread-safe
    class UnsafeCounter:
        def __init__(self):
            self.count = 0

        def increment(self):
            self.count += 1  # Race condition!
            return self.count

    # ✅ Thread-safe
    from threading import Lock

    class SafeCounter:
        def __init__(self):
            self.count = 0
            self._lock = Lock()

        def increment(self):
            with self._lock:
                self.count += 1
                return self.count
    ```

    **Common non-thread-safe operations:**
    - Incrementing counters (`count += 1`)
    - Appending to lists (`list.append()`)
    - Modifying dictionaries (`dict[key] = value`)
    - File I/O without locks

    Use Python's `threading.Lock`, `threading.RLock`, or thread-safe data structures (like `queue.Queue`) when modifying singleton state from multiple threads.

## Advanced: How Lifetimes Work Internally

!!! info "Technical Details for Advanced Users"
    FastIoC handles caching differently based on the lifetime:

    ### Scoped & Transient (Classes)
    - **Scoped:** Instance is created once and cached per request
    - **Transient:** New instance created on every injection

    ### Scoped & Transient (Functions)
    - **Scoped:** Function called once, **return value** cached per request
    - **Transient:** Function called every time, returns fresh value

    This matches FastAPI's behavior exactly.

    ### Singleton (Classes)
    - FastIoC creates the **instance** once and stores it internally
    - The registered dependency becomes a function that returns the stored instance
    - This ensures the same instance is always returned

    ### Singleton (Functions)
    - FastIoC calls the function once and stores the **return value**
    - Subsequent resolutions return the cached value
    - The function is never called again

    **Example:**
    ```python
    container.add_singleton(IConfig, ServiceConfig)

    # Internally becomes something like:
    _instance = None
    def get_config():
        global _instance
        if _instance is None:
            _instance = ServiceConfig()  # Called once
        return _instance  # Always returns same instance
    ```

    This is why generators don't work as singletons.

## Next Steps

- Learn about [Nested Dependencies](nested.md) - how dependencies can depend on other dependencies
- Understand [Dependency Overrides](override.md) - replacing dependencies for testing
- Explore [Dispose (Singleton Clean-up)](dispose.md) - properly cleaning up singleton resources
