# Dependency Overrides

FastIoC provides full compatibility with FastAPI's [dependency override system](https://fastapi.tiangolo.com/advanced/testing-dependencies/), making it easy to replace dependencies during testing or other scenarios.

## The `Container.override()` Method

The `Container.override()` method generates an updated dictionary suitable for FastAPI's `app.dependency_overrides`. It supports two ways to override dependencies:

1. A dictionary of explicit dependency overrides
2. An optional mock container with alternative implementations

### Basic Usage with Dictionary

You can override registered dependencies by passing a dictionary where keys are protocol types and values are the replacement implementations:

```python
from fastapi import FastAPI, Depends
from fastioc import Container

app = FastAPI()
container = Container()

# Register original dependencies
container.add_scoped(INumberService, NumberService)
container.injectify(app)

# Create overrides
overrides = {
    INumberService: MockNumberService,
    get_function_number: get_mock_function_number
}

# Apply overrides
app.dependency_overrides = container.override(overrides)
```

**Important**: When overriding container-registered dependencies, use the **exact protocol type** as the key (e.g., `INumberService`), not `Annotated[SomeType, INumberService]`.

### Mixing FastAPI and FastIoC Dependencies

One powerful feature of `Container.override()` is that it seamlessly combines FastAPI's native dependencies with FastIoC dependencies. Keys that are not registered in the container remain unchanged, allowing you to mix both systems:

```python
overrides = {
    IService: MockService,           # FastIoC dependency
    get_user: get_mock_user,         # Regular FastAPI dependency
    some_function: mock_function     # Another FastAPI dependency
}

app.dependency_overrides = container.override(overrides)
```

### Using a Mock Container

For more complex testing scenarios, you can create a separate container with mock implementations and pass it to the `override()` method:

```python
# Create a test container with mock implementations
test_container = Container()
test_container.add_scoped(IGlobalService, MockGlobalService)
test_container.add_scoped(INumberService, MockNumberService)

# Apply all mock container dependencies as overrides
app.dependency_overrides = container.override(container=test_container)

# Or combine with explicit overrides
app.dependency_overrides = container.override(
    dependencies={get_function: mock_function},
    container=test_container
)
```

## Lifetime Preservation

**⚠️ IMPORTANT**: Always use the **same lifetime** in your mock container as in your main container. Mixing different lifetimes can lead to unexpected behavior and should be avoided in most cases.

The override system preserves the original container's lifetime to ensure your tests maintain realistic dependency lifecycles. Simply register your mocks with the same lifetime as the originals:

```python
# Main container
container = Container()
container.add_singleton(IGlobalService, GlobalService)
container.add_scoped(INumberService, NumberService)

# Test container - use the SAME lifetimes
test_container = Container()
test_container.add_singleton(IGlobalService, MockGlobalService)  # ✅ Same: SINGLETON
test_container.add_scoped(INumberService, MockNumberService)      # ✅ Same: SCOPED

app.dependency_overrides = container.override(container=test_container)
```

> **⚠️ Advanced: Lifetime Override Behavior**
>
> If you must use different lifetimes (not recommended), be aware of these rules:
>
> 1. **SCOPED or TRANSIENT in main container**: The original lifetime is always preserved, regardless of what is registered in the mock container (except when the mock is SINGLETON).
>
> 2. **SINGLETON in main container**:
>    - If the mock container has a different lifetime → the resulting lifetime will be **SCOPED**
>
> 3. **Non-SINGLETON in main container**:
>    - If the mock container registers it as SINGLETON → the resulting lifetime will be **SINGLETON**
>
> **Example with mixed lifetimes (not recommended)**:
> ```python
> # Main container
> container = Container()
> container.add_singleton(ILifetimeServiceSingleton, LifetimeService)
> container.add_scoped(ILifetimeServiceScoped, LifetimeService)
> container.add_transient(ILifetimeServiceFactory, LifetimeService)
>
> # Test container with DIFFERENT lifetimes
> test_container = Container()
> test_container.add_singleton(ILifetimeServiceSingleton, MockLifetimeService)
> test_container.add_transient(ILifetimeServiceScoped, MockLifetimeService)
> test_container.add_transient(ILifetimeServiceFactory, MockLifetimeService)
>
> # Apply overrides
> app.dependency_overrides = container.override(container=test_container)
>
> # Resulting lifetimes:
> # - ILifetimeServiceSingleton: SCOPED (singleton → different lifetime)
> # - ILifetimeServiceScoped: SCOPED (preserved from main)
> # - ILifetimeServiceFactory: TRANSIENT (preserved from main)
> ```

## Complete Testing Example

Here's a complete example showing how to use `Container.override()` in tests:

```python
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from fastioc import Container

# Original implementations
class NumberService:
    def get_number(self) -> int:
        return 42

class GlobalService:
    def __init__(self):
        self.value = 100

# Mock implementations
class MockNumberService:
    def get_number(self) -> int:
        return 999

class MockGlobalService:
    def __init__(self):
        self.value = 888

def get_function_number() -> int:
    return 42

def get_mock_function_number() -> int:
    return 777

# Setup
app = FastAPI()
container = Container()

container.add_scoped(IGlobalService, GlobalService)
container.add_scoped(INumberService, NumberService)
container.injectify(app)

# Create test container
test_container = Container()
test_container.add_scoped(IGlobalService, MockGlobalService)
test_container.add_scoped(INumberService, MockNumberService)

# Apply overrides
app.dependency_overrides = container.override(
    dependencies={get_function_number: get_mock_function_number},
    container=test_container
)

# Test endpoint
@app.get('/test', dependencies=[IGlobalService])
async def endpoint(
    service: INumberService,
    number: int = Depends(get_function_number)
):
    return {
        'service': service.get_number(),
        'number': number
    }

# Test
client = TestClient(app)
response = client.get('/test')
data = response.json()

assert data['service'] == 999  # From MockNumberService
assert data['number'] == 777   # From get_mock_function_number
```

## Key Takeaways

- `Container.override()` provides full compatibility with FastAPI's dependency override system
- Use exact protocol types (not `Annotated` types) as dictionary keys
- Combine FastAPI and FastIoC dependencies seamlessly in the same override dictionary
- Pass a mock container for complex testing scenarios
- Original lifetimes are preserved to maintain realistic behavior (with specific exceptions for SINGLETON overrides)
- Unregistered keys in the override dictionary are left unchanged, enabling flexible mixing of different dependency types
