# Container Hooks

FastIoC provides two powerful hooks that allow you to intercept and customize the dependency registration and resolution process. These hooks are useful for logging, validation, metrics, tracing, or applying custom behavior to your dependencies.

## Available Hooks

### 1. `before_register_hook`

This hook is executed **before a dependency is registered** in the container. It allows you to inspect, modify, or validate the dependency before it's stored.

**Signature:**
```python
def before_register_hook(self, dependency: Dependency[Any]) -> Dependency[Any]:
    ...
```

**Parameters:**
- `dependency.protocol` - The interface or protocol type
- `dependency.implementation` - The implementation or factory
- `dependency.lifetime` - The lifetime (SINGLETON, SCOPED, TRANSIENT)

**Returns:**
- The (optionally modified) dependency that will actually be registered

### 2. `before_resolve_hook`

This hook is executed **before a dependency is resolved** from the container. It allows you to inspect, wrap, or modify the dependency just before it's provided to a consumer.

**Signature:**
```python
def before_resolve_hook(self, dependency: Depends) -> Depends:
    ...
```

**Parameters:**
- `dependency.dependency` - The callable that will produce the actual instance
- `dependency.use_cache` - Whether the instance should be cached for reuse

**Returns:**
- The (optionally modified) Depends instance to be used in resolution

## How to Use Hooks

You can override these methods by **monkey patching** them on your container instance:

```python
from fastioc import Container

container = Container()

# Define your hook function
def my_register_hook(dependency):
    print(f"Registering {dependency.protocol.__name__} -> {dependency.implementation}")
    return dependency

# Monkey patch the hook
container.before_register_hook = my_register_hook

# Now all registrations will trigger the hook
container.add_scoped(IService, Service)
```

## Use Cases

### Logging Registration and Resolution

Track which dependencies are being registered and resolved:

```python
from fastioc import Container
from fastioc.definitions import Dependency
from fastapi.params import Depends

container = Container()

# Registration logging
def log_register(dependency: Dependency) -> Dependency:
    print(f"=� Registering: {dependency.protocol.__name__}")
    print(f"   Implementation: {dependency.implementation}")
    print(f"   Lifetime: {dependency.lifetime}")
    return dependency

# Resolution logging
def log_resolve(dependency: Depends) -> Depends:
    print(f"=
 Resolving: {dependency.dependency.__name__}")
    return dependency

container.before_register_hook = log_register
container.before_resolve_hook = log_resolve

# Now watch the logs as you register and use dependencies
container.add_scoped(IUserService, UserService)
```

**Output:**
```
=� Registering: IUserService
   Implementation: <class 'UserService'>
   Lifetime: LifeTime.SCOPED
```

### Validation

Ensure dependencies meet certain criteria before registration:

```python
from fastioc.definitions import Dependency, LifeTime

def validate_register(dependency: Dependency) -> Dependency:
    # Ensure singleton implementations have __dispose__ method
    if dependency.lifetime == LifeTime.SINGLETON:
        if not hasattr(dependency.implementation, '__dispose__'):
            print(f"Warning: {dependency.implementation} is a singleton without __dispose__")

    # Ensure protocol names start with 'I'
    if not dependency.protocol.__name__.startswith('I'):
        raise ValueError(f"Protocol {dependency.protocol.__name__} must start with 'I'")

    return dependency

container.before_register_hook = validate_register
```

### Metrics and Tracing

Track dependency resolution for performance monitoring:

```python
import time
from collections import defaultdict

resolution_count = defaultdict(int)
resolution_times = defaultdict(list)

def track_resolve(dependency: Depends) -> Depends:
    original_callable = dependency.dependency
    name = original_callable.__name__

    def timed_callable(*args, **kwargs):
        start = time.time()
        result = original_callable(*args, **kwargs)
        duration = time.time() - start

        resolution_count[name] += 1
        resolution_times[name].append(duration)

        return result

    # Wrap the callable
    dependency.dependency = timed_callable
    return dependency

container.before_resolve_hook = track_resolve

# After running your app
print(f"Resolution stats: {dict(resolution_count)}")
print(f"Average times: {dict(resolution_times)}")
```

### Modifying Dependencies

Change the implementation or lifetime at registration time:

```python
from fastioc.definitions import LifeTime

def modify_register(dependency: Dependency) -> Dependency:
    # Force all services to be singletons in production
    if "Service" in dependency.protocol.__name__:
        print(f"=' Changing {dependency.protocol.__name__} to SINGLETON")
        dependency.lifetime = LifeTime.SINGLETON

    return dependency

container.before_register_hook = modify_register
```

### Environment-Based Behavior

Switch implementations based on environment:

```python
import os

def env_based_register(dependency: Dependency) -> Dependency:
    # Use mock implementations in test environment
    if os.getenv("ENV") == "test":
        impl_name = dependency.implementation.__name__
        if impl_name.endswith("Service"):
            mock_name = f"Mock{impl_name}"
            # Assume mock classes are available
            if mock_class := globals().get(mock_name):
                print(f">� Using {mock_name} instead of {impl_name}")
                dependency.implementation = mock_class

    return dependency

container.before_register_hook = env_based_register
```

## Complete Example

Here's a complete example showing both hooks working together:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastioc import Container
from fastioc.definitions import Dependency
from fastapi.params import Depends

# Service definition
class INumberService:
    def get_number(self) -> int:
        ...

class NumberService(INumberService):
    def get_number(self) -> int:
        return 42

# Setup
app = FastAPI()
container = Container()

# Track hook calls
register_number: int = 0
resolve_number: int = 0

def register_hook(dependency: Dependency[INumberService]) -> Dependency[INumberService]:
    global register_number
    # Call implementation to get the number
    register_number = dependency.implementation().get_number()
    print(f"=� Registered: {dependency.protocol.__name__} (number: {register_number})")
    return dependency

def resolve_hook(dependency: Depends) -> Depends:
    global resolve_number
    # Call the dependency callable to get instance
    resolve_number = dependency.dependency().get_number()
    print(f"=
 Resolved: dependency (number: {resolve_number})")
    return dependency

# Apply hooks
container.before_register_hook = register_hook
container.before_resolve_hook = resolve_hook

# Register service
container.add_scoped(INumberService, NumberService)
container.injectify(app)

# Create endpoint
@app.get('/test')
async def endpoint(service: INumberService) -> int:
    return service.get_number()

# Test
client = TestClient(app)
response = client.get('/test')
data = response.json()

print(f"Response: {data}")
print(f"Register number: {register_number}")
print(f"Resolve number: {resolve_number}")

assert data == register_number == resolve_number == 42
```

**Output:**
```
=� Registered: INumberService (number: 42)
=
 Resolved: dependency (number: 42)
Response: 42
Register number: 42
Resolve number: 42
```

## Hook Execution Flow

```
1. container.add_scoped(IService, Service)
2. before_register_hook(Dependency(...)) -> Your custom logic
3. Dependency stored in container

---

4. Endpoint called, needs IService
5. container.resolve(IService)
6. before_resolve_hook(Depends(...)) -> Your custom logic
7. Dependency instance provided to endpoint
```

## Important Notes

- Hooks are **optional** - if not overridden, they do nothing
- `before_register_hook` runs once per dependency registration
- `before_resolve_hook` runs every time a dependency is resolved (first access per request for SCOPED)
- Hooks **must return** the dependency (modified or unmodified)
- You can modify the dependency object inside hooks
- ⚠️ Be careful with performance in `before_resolve_hook` - it runs frequently
- ⚠️ Errors in hooks will propagate and prevent registration/resolution

## Common Patterns

### Debug Mode Toggle

```python
DEBUG = True

def debug_register(dependency: Dependency) -> Dependency:
    if DEBUG:
        print(f"[DEBUG] Register: {dependency.protocol.__name__}")
    return dependency

def debug_resolve(dependency: Depends) -> Depends:
    if DEBUG:
        print(f"[DEBUG] Resolve: {dependency.dependency.__name__}")
    return dependency

if DEBUG:
    container.before_register_hook = debug_register
    container.before_resolve_hook = debug_resolve
```

### Audit Trail

```python
from datetime import datetime

audit_log = []

def audit_register(dependency: Dependency) -> Dependency:
    audit_log.append({
        "timestamp": datetime.now(),
        "action": "register",
        "protocol": dependency.protocol.__name__,
        "implementation": dependency.implementation.__name__,
        "lifetime": dependency.lifetime
    })
    return dependency

container.before_register_hook = audit_register

# Later, export audit log
import json
with open("audit.json", "w") as f:
    json.dump(audit_log, f, indent=2, default=str)
```

## Related Documentation

- [Container Registration](lifetime.md)
- [Dependency Resolution](nested.md)
- [Project Structure at Scale](scale.md)
