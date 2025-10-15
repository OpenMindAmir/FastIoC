# Passing Data to Dependencies

When building applications, you often need to pass configuration data, settings, or runtime parameters to your dependencies. This guide shows three common patterns for accomplishing this in FastIoC.

## Pattern 1: FastAPI Native Dependencies

FastIoC is fully compatible with FastAPI's native [dependency injection system](https://fastapi.tiangolo.com/tutorial/dependencies/#create-a-dependency-or-dependable). You can use FastAPI's features to pass data from requests directly to your dependencies.

### In Functions and Generators

You can receive request data as parameters in function or generator dependencies, exactly like in FastAPI:

```python
from fastapi import FastAPI, Query, Header, Path
from fastioc import Container
from typing import Annotated

app = FastAPI()
container = Container()

# Function dependency that receives request data
def get_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
) -> dict:
    return {
        "skip": (page - 1) * page_size,
        "limit": page_size
    }

# Service that uses pagination
class DataService:
    def __init__(self, pagination: Annotated[dict, Depends(get_pagination)]):
        self.pagination = pagination

    def fetch_data(self):
        return f"Fetching data with skip={self.pagination['skip']}, limit={self.pagination['limit']}"

container.add_scoped(DataService, DataService)
container.injectify(app)

@app.get("/data")
async def get_data(service: DataService):
    return {"result": service.fetch_data()}
```

### In Class `__init__` Parameters

In class `__init__` parameters, FastAPI features work just like they do in regular FastAPI dependencies:

```python
from fastapi import Query, Header, Cookie
from typing import Annotated

class AuthenticatedService:
    def __init__(
        self,
        # FastAPI features work directly
        api_key: Annotated[str, Header()],
        user_id: Annotated[int, Query()],
        session: Annotated[str, Cookie()] = "default",

        # You can also mix with FastIoC dependencies
        db: IDatabaseService
    ):
        self.api_key = api_key
        self.user_id = user_id
        self.session = session
        self.db = db

    def get_user_data(self):
        return self.db.query(self.user_id)

container.add_scoped(IDatabaseService, DatabaseService)
container.add_scoped(AuthenticatedService, AuthenticatedService)
```

### In Class Type Hints (FastIoC's Special Feature)

When using [class-level type hints](nested.md#method-2-resolution-in-class-type-hints) (FastIoC's unique feature), you **MUST** use FastAPI's annotations explicitly:

```python
from fastapi import Query, Header, Cookie, Request
from typing import Annotated

class SearchService:
    # ❌ WRONG: Simple types don't work in class hints
    # query: str  # This won't receive query parameter!

    # ✅ CORRECT: Must use FastAPI annotations
    query: Annotated[str, Query()]
    page: Annotated[int, Query(default=1)]
    api_key: Annotated[str, Header()]

    # ✅ FastAPI special types work directly
    request: Request

    # ✅ FastIoC dependencies work as usual
    db: IDatabaseService

    def search(self):
        return self.db.search(
            query=self.query,
            page=self.page,
            user_agent=self.request.headers.get("user-agent")
        )

container.add_scoped(IDatabaseService, DatabaseService)
container.add_scoped(SearchService, SearchService)
```

**Important**: The difference between `__init__` and class type hints:

```python
class ServiceA:
    # In __init__: Works like normal FastAPI
    def __init__(
        self,
        user_id: int = Query()  # ✅ Works
    ):
        self.user_id = user_id

class ServiceB:
    # In class hints: MUST use Annotated
    user_id: Annotated[int, Query()]  # ✅ Works
    # user_id: int = Query()          # ❌ Won't work!
```

See [Nested Dependencies - Class Type Hints](nested.md#method-2-resolution-in-class-type-hints) for more details.

### Complete Example

```python
from fastapi import FastAPI, Query, Header, Depends
from fastioc import Container
from typing import Annotated

app = FastAPI()
container = Container()

# Function dependency
def get_auth_header(authorization: str = Header()) -> str:
    return authorization.replace("Bearer ", "")

# Class with __init__ parameters
class UserService:
    def __init__(
        self,
        user_id: int = Query(),
        token: Annotated[str, Depends(get_auth_header)] = None,
        db: IDatabaseService = None
    ):
        self.user_id = user_id
        self.token = token
        self.db = db

# Class with type hints
class AdminService:
    # Must use Annotated for request data in class hints
    admin_key: Annotated[str, Header()]
    action: Annotated[str, Query()]

    # FastIoC dependencies work as usual
    db: IDatabaseService

container.add_scoped(IDatabaseService, DatabaseService)
container.add_scoped(UserService, UserService)
container.add_scoped(AdminService, AdminService)
container.injectify(app)

@app.get("/user")
async def get_user(service: UserService):
    return {"user_id": service.user_id, "authenticated": bool(service.token)}

@app.get("/admin")
async def admin_action(service: AdminService):
    return {"action": service.action, "key_valid": bool(service.admin_key)}
```

## Pattern 2: Options Pattern

The Options Pattern involves registering a dependency that contains shared or required data (like configuration, settings, or context), and then using it as a nested dependency in your services.

### Example 1: Configuration Class

```python
from dataclasses import dataclass
from fastioc import Container
from fastapi import FastAPI

# Options/Configuration class
@dataclass
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str

# Service that depends on the configuration
class DatabaseService:
    
    config: DatabaseConfig

    def get_connection_string(self) -> str:
        return f"postgresql://{self.config.username}@{self.config.host}:{self.config.port}/{self.config.database}"

# Setup
app = FastAPI()
container = Container()

# Register the configuration as a singleton
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    username="user",
    password="pass",
    database="mydb"
)
container.add_singleton(DatabaseConfig, lambda: db_config)

# Register the service - it will automatically receive the config
container.add_scoped(DatabaseService, DatabaseService)
container.injectify(app)

@app.get("/connection")
async def get_connection(db: DatabaseService):
    return {"connection_string": db.get_connection_string()}
```

### Example 2: Dictionary Provider

```python
from typing import Dict, Any
from fastioc import Container
from fastapi import FastAPI

# Function that returns configuration as a dictionary
def get_app_settings() -> Dict[str, Any]:
    return {
        "api_key": "secret-key-123",
        "max_connections": 100,
        "timeout": 30,
        "feature_flags": {
            "new_ui": True,
            "beta_features": False
        }
    }

# Service that uses the configuration
class ApiClient:
    def __init__(self, settings: Dict[str, Any]):
        self.api_key = settings["api_key"]
        self.timeout = settings["timeout"]

    def make_request(self) -> str:
        return f"Making request with API key: {self.api_key[:10]}..."

# Setup
app = FastAPI()
container = Container()

# Register the settings provider
container.add_singleton(Dict[str, Any], get_app_settings)

# Register the service
container.add_scoped(ApiClient, ApiClient)
container.injectify(app)

@app.get("/api-call")
async def call_api(client: ApiClient):
    return {"result": client.make_request()}
```

### Example 3: Updatable Configuration

```python
from fastioc import Container
from fastapi import FastAPI

# Configuration manager that can be updated
class AppSettings:
    def __init__(self):
        self._settings = {
            "theme": "dark",
            "language": "en",
            "notifications": True
        }

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def update(self, key: str, value: Any):
        self._settings[key] = value

    def get_all(self) -> dict:
        return self._settings.copy()

# Service that uses settings
class UIService:
    settings: AppSettings

    def get_theme(self) -> str:
        return self.settings.get("theme")

# Setup
app = FastAPI()
container = Container()

# Register settings as singleton (shared across requests)
container.add_singleton(AppSettings, AppSettings)
container.add_scoped(UIService, UIService)
container.injectify(app)

@app.get("/theme")
async def get_theme(ui: UIService):
    return {"theme": ui.get_theme()}

@app.post("/theme/{theme}")
async def update_theme(theme: str, settings: AppSettings):
    settings.update("theme", theme)
    return {"message": "Theme updated", "theme": theme}
```

## Pattern 3: Factory Pattern

The Factory Pattern involves wrapping your dependency with a function that creates its instance or calls it with specific parameters. This is useful when you need to pass configuration data or create customized instances at registration time.

### Example 1: Simple Factory Function

```python
from fastioc import Container
from fastapi import FastAPI

# Original service that needs parameters
class EmailService:
    def __init__(self, smtp_host: str, smtp_port: int, sender: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender = sender

    def send(self, to: str, message: str) -> str:
        return f"Sending from {self.sender} to {to} via {self.smtp_host}:{self.smtp_port}"

# Factory function that creates the service with specific configuration
def create_email_service() -> EmailService:
    return EmailService(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender="noreply@myapp.com"
    )

# Setup
app = FastAPI()
container = Container()

# Register using the factory
container.add_scoped(EmailService, create_email_service)
container.injectify(app)

@app.post("/send-email")
async def send_email(email: EmailService, to: str, message: str):
    result = email.send(to, message)
    return {"status": result}
```

### Example 2: Factory with Nested Dependencies

```python
from fastioc import Container
from fastapi import FastAPI
from dataclasses import dataclass

# Configuration
@dataclass
class LoggerConfig:
    log_level: str
    format: str

# Service that needs both config and custom parameters
class Logger:
    def __init__(self, name: str, config: LoggerConfig):
        self.name = name
        self.log_level = config.log_level
        self.format = config.format

    def log(self, message: str) -> str:
        return f"[{self.name}] [{self.log_level}] {message}"

# Factory that receives config from DI and adds custom parameters
def create_logger(config: LoggerConfig) -> Logger:
    # Custom logic to determine the logger name or other parameters
    app_name = "MyApplication"
    return Logger(name=app_name, config=config)

# Setup
app = FastAPI()
container = Container()

# Register configuration
logger_config = LoggerConfig(log_level="INFO", format="json")
container.add_singleton(LoggerConfig, lambda: logger_config)

# Register logger using factory (factory receives config automatically)
container.add_scoped(Logger, create_logger)
container.injectify(app)

@app.get("/log")
async def log_message(logger: Logger, message: str):
    result = logger.log(message)
    return {"logged": result}
```

## Choosing Between Patterns

### Use **Pattern 1: FastAPI Native Dependencies** when:
- You need to access request-specific data (query params, headers, cookies, etc.)
- Working with path parameters, request bodies, or uploaded files
- Need data that varies per request
- Want to use FastAPI's built-in validation and documentation features

### Use **Pattern 2: Options Pattern** when:
- You have configuration that multiple services need to share
- Settings need to be updated at runtime
- You want to keep configuration centralized and reusable
- Multiple services depend on the same configuration data
- Configuration is independent of individual requests

### Use **Pattern 3: Factory Pattern** when:
- You need to pass specific parameters during dependency registration (not per request)
- Dependencies require complex initialization logic
- You need to create different instances with different configurations
- You want to combine DI-provided dependencies with custom parameters
- Configuration is static and determined at startup time