# Project Structure at Scale

As your FastAPI application grows, organizing your code becomes crucial for maintainability, testability, and team collaboration. This guide presents a Clean Architecture approach using FastIoC and APIController to structure large-scale applications.

## Recommended Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app & startup
│   └── container.py          # Container & dependency registrations
│
├── core/                     # Domain layer (business logic)
│   ├── __init__.py
│   ├── entities/             # Domain models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   │
│   └── interfaces/           # Abstract protocols
│       ├── __init__.py
│       ├── repositories.py
│       └── services.py
│
├── services/                 # Application services
│   ├── __init__.py
│   ├── user_service.py
│   ├── auth_service.py
│   └── email_service.py
│
├── infrastructure/           # External dependencies
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   └── product_repository.py
│   │
│   ├── external/
│   │   ├── __init__.py
│   │   └── email_client.py
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py
│
├── controllers/              # API Controllers
│   ├── __init__.py
│   ├── user_controller.py
│   ├── product_controller.py
│   └── auth_controller.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
└── requirements.txt
```

## Architecture Layers

### 1. Core Layer (`core/`)

The innermost layer containing your business domain. It has **no dependencies** on outer layers.

**`core/entities/user.py`** - Domain models:
```python
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    is_active: bool | None = None
```

**`core/interfaces/repositories.py`** - Repository protocols:
```python
from typing import Protocol, List, Optional
from app.core.entities.user import User, UserCreate, UserUpdate

class IUserRepository(Protocol):
    """Protocol for user data access"""

    def get_by_id(self, user_id: int) -> Optional[User]:
        ...

    def get_by_email(self, email: str) -> Optional[User]:
        ...

    def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        ...

    def create(self, user: UserCreate) -> User:
        ...

    def update(self, user_id: int, user: UserUpdate) -> Optional[User]:
        ...

    def delete(self, user_id: int) -> bool:
        ...
```

**`core/interfaces/services.py`** - Service protocols:
```python
from typing import Protocol

class IEmailService(Protocol):
    """Protocol for email operations"""

    def send_welcome_email(self, email: str, username: str) -> bool:
        ...

    def send_password_reset(self, email: str, token: str) -> bool:
        ...

class IAuthService(Protocol):
    """Protocol for authentication"""

    def hash_password(self, password: str) -> str:
        ...

    def verify_password(self, plain: str, hashed: str) -> bool:
        ...

    def create_access_token(self, user_id: int) -> str:
        ...
```

### 2. Services Layer (`services/`)

Application services implementing business logic using core interfaces.

First, let's add a protocol for UserService in **`core/interfaces/services.py`**:
```python
from typing import Protocol, List, Optional
from app.core.entities.user import User, UserCreate, UserUpdate

class IUserService(Protocol):
    """Protocol for user business logic"""

    def get_user(self, user_id: int) -> Optional[User]:
        ...

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        ...

    def create_user(self, user_data: UserCreate) -> User:
        ...

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        ...

    def delete_user(self, user_id: int) -> bool:
        ...

class IEmailService(Protocol):
    """Protocol for email operations"""

    def send_welcome_email(self, email: str, username: str) -> bool:
        ...

    def send_password_reset(self, email: str, token: str) -> bool:
        ...

class IAuthService(Protocol):
    """Protocol for authentication"""

    def hash_password(self, password: str) -> str:
        ...

    def verify_password(self, plain: str, hashed: str) -> bool:
        ...

    def create_access_token(self, user_id: int) -> str:
        ...
```

**`services/user_service.py`**:
```python
from typing import List, Optional
from app.core.entities.user import User, UserCreate, UserUpdate
from app.core.interfaces.repositories import IUserRepository
from app.core.interfaces.services import IUserService, IEmailService, IAuthService

class UserService(IUserService):
    """Business logic for user operations - implements IUserService"""

    def __init__(
        self,
        user_repo: IUserRepository,
        email_service: IEmailService,
        auth_service: IAuthService
    ):
        self.user_repo = user_repo
        self.email_service = email_service
        self.auth_service = auth_service

    def get_user(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.user_repo.list(skip, limit)

    def create_user(self, user_data: UserCreate) -> User:
        # Hash password
        hashed_password = self.auth_service.hash_password(user_data.password)

        # Create user
        user = self.user_repo.create(user_data)

        # Send welcome email
        self.email_service.send_welcome_email(user.email, user.username)

        return user

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        return self.user_repo.update(user_id, user_data)

    def delete_user(self, user_id: int) -> bool:
        return self.user_repo.delete(user_id)
```

**`services/auth_service.py`**:
```python
import bcrypt
import jwt
from datetime import datetime, timedelta
from app.core.interfaces.services import IAuthService

class AuthService(IAuthService):
    """Authentication service implementation - implements IAuthService"""

    def __init__(self, secret_key: str = "your-secret-key"):
        self.secret_key = secret_key

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def create_access_token(self, user_id: int) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
```

### 3. Infrastructure Layer (`infrastructure/`)

Implementations of external dependencies like databases, APIs, and configuration.

**`infrastructure/config/settings.py`**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/mydb"
    secret_key: str = "your-secret-key"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
```

**`infrastructure/database/connection.py`**:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.infrastructure.config.settings import Settings

class Database:
    """Database connection manager"""

    def __init__(self, settings: Settings):
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def __dispose__(self):
        """Cleanup on shutdown"""
        self.engine.dispose()
```

**`infrastructure/database/repositories/user_repository.py`**:
```python
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.entities.user import User, UserCreate, UserUpdate
from app.core.interfaces.repositories import IUserRepository
from app.infrastructure.database.connection import Database

class UserRepository(IUserRepository):
    """User repository implementation - implements IUserRepository"""

    def __init__(self, db: Database):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        with self.db.get_session() as session:
            # Query database and return User entity
            result = session.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
            row = result.fetchone()
            return User(**row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        with self.db.get_session() as session:
            result = session.execute("SELECT * FROM users WHERE email = :email", {"email": email})
            row = result.fetchone()
            return User(**row) if row else None

    def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        with self.db.get_session() as session:
            result = session.execute(
                "SELECT * FROM users LIMIT :limit OFFSET :skip",
                {"limit": limit, "skip": skip}
            )
            return [User(**row) for row in result]

    def create(self, user: UserCreate) -> User:
        with self.db.get_session() as session:
            # Insert and return created user
            result = session.execute(
                "INSERT INTO users (email, username) VALUES (:email, :username) RETURNING *",
                {"email": user.email, "username": user.username}
            )
            session.commit()
            return User(**result.fetchone())

    def update(self, user_id: int, user: UserUpdate) -> Optional[User]:
        # Implementation...
        pass

    def delete(self, user_id: int) -> bool:
        # Implementation...
        pass
```

**`infrastructure/external/email_client.py`**:
```python
import smtplib
from email.mime.text import MIMEText
from app.core.interfaces.services import IEmailService
from app.infrastructure.config.settings import Settings

class EmailService(IEmailService):
    """Email service implementation - implements IEmailService"""

    def __init__(self, settings: Settings):
        self.settings = settings

    def send_welcome_email(self, email: str, username: str) -> bool:
        msg = MIMEText(f"Welcome {username}!")
        msg['Subject'] = 'Welcome to Our App'
        msg['To'] = email

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_password_reset(self, email: str, token: str) -> bool:
        # Implementation...
        pass
```

### 4. Controllers Layer (`controllers/`)

API controllers using APIController for presentation logic.

**`controllers/user_controller.py`**:
```python
from fastapi import HTTPException, Query
from typing import Annotated
from fastioc.controller import APIController, get, post, put, delete
from app.core.entities.user import User, UserCreate, UserUpdate
from app.core.interfaces.services import IUserService

class UserController(APIController):
    config = {
        'prefix': '/users',
        'tags': ['Users']
        # Container will be set in main.py
    }

    # Shared dependency - injected into all endpoints
    user_service: IUserService

    @get('/', response_model=list[User])
    def list_users(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        """List all users with pagination"""
        return self.user_service.list_users(skip, limit)

    @get('/{user_id}', response_model=User)
    def get_user(self, user_id: int):
        """Get a specific user by ID"""
        user = self.user_service.get_user(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    @post('/', response_model=User, status_code=201)
    def create_user(self, user: UserCreate):
        """Create a new user"""
        # Check if email already exists
        existing = self.user_service.user_repo.get_by_email(user.email)
        if existing:
            raise HTTPException(400, "Email already registered")

        return self.user_service.create_user(user)

    @put('/{user_id}', response_model=User)
    def update_user(self, user_id: int, user: UserUpdate):
        """Update an existing user"""
        updated = self.user_service.update_user(user_id, user)
        if not updated:
            raise HTTPException(404, "User not found")
        return updated

    @delete('/{user_id}')
    def delete_user(self, user_id: int):
        """Delete a user"""
        success = self.user_service.delete_user(user_id)
        if not success:
            raise HTTPException(404, "User not found")
        return {"status": "deleted", "user_id": user_id}
```

**`controllers/auth_controller.py`**:
```python
from fastapi import HTTPException
from fastioc.controller import APIController, post
from pydantic import BaseModel
from app.core.interfaces.services import IAuthService
from app.core.interfaces.repositories import IUserRepository

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthController(APIController):
    config = {
        'prefix': '/auth',
        'tags': ['Authentication']
    }

    auth_service: IAuthService
    user_repo: IUserRepository

    @post('/login')
    def login(self, credentials: LoginRequest):
        """Authenticate user and return access token"""
        # Get user
        user = self.user_repo.get_by_email(credentials.email)
        if not user:
            raise HTTPException(401, "Invalid credentials")

        # Verify password (simplified - actual implementation would have hashed password)
        if not self.auth_service.verify_password(credentials.password, "hashed_password"):
            raise HTTPException(401, "Invalid credentials")

        # Generate token
        token = self.auth_service.create_access_token(user.id)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
```

### 5. Container Configuration (`container.py`)

**All dependency registrations in a single file:**

```python
from fastioc import Container
from app.core.interfaces.repositories import IUserRepository
from app.core.interfaces.services import IUserService, IEmailService, IAuthService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.infrastructure.database.connection import Database
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.external.email_client import EmailService
from app.infrastructure.config.settings import Settings, get_settings

def create_container() -> Container:
    """Create and configure the IoC container with all dependencies"""

    container = Container()

    # Configuration (Singleton)
    container.add_singleton(Settings, get_settings)

    # Infrastructure Layer (Singleton - shared resources)
    container.add_singleton(Database, Database)

    # Repositories (Scoped - per request)
    container.add_scoped(IUserRepository, UserRepository)

    # External Services (Singleton)
    container.add_singleton(IEmailService, EmailService)
    container.add_singleton(IAuthService, AuthService)

    # Application Services (Scoped - per request)
    container.add_scoped(IUserService, UserService)

    return container
```

### 6. Application Entry Point (`main.py`)

**FastAPI app initialization with lifespan and controller registration:**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.container import create_container
from app.controllers.user_controller import UserController
from app.controllers.auth_controller import AuthController

# Create container
container = create_container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    print("=> Application starting...")
    yield
    print("=> Application shutting down...")
    await container.dispose()
    print("=> Cleanup complete")

# Create FastAPI app
app = FastAPI(
    title="My Scalable API",
    version="1.0.0",
    lifespan=lifespan
)

# Inject container into app for dependency resolution
container.injectify(app)

# Register all controllers
app.include_router(UserController.router({'container': container}))
app.include_router(AuthController.router({'container': container}))

@app.get("/")
def root():
    return {"message": "Welcome to My Scalable API"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

## Key Principles

### 1. Dependency Flow

Dependencies flow **inward**:
```
Controllers -> Services -> Repositories -> Database
     |           |            |
  (HTTP)    (Business)   (Data Access)
```

Core layer (domain) has no dependencies on outer layers.

### 2. Single Container File

All dependency registrations live in `container.py`. This makes it easy to:
- See all your dependencies at a glance
- Understand the application structure
- Swap implementations for testing
- Manage lifetimes consistently

### 3. Protocol-Based Design

Use protocols (interfaces) for loose coupling and **have implementations inherit from protocols** for type safety:
```python
# Define protocol in core/interfaces/
class IUserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User: ...

# Implement in infrastructure/ - inherit from protocol
class UserRepository(IUserRepository):
    def get_by_id(self, user_id: int) -> User:
        # Implementation

# Register protocol → implementation in container.py
container.add_scoped(IUserRepository, UserRepository)

# Controllers depend on protocols, not implementations
class UserController(APIController):
    user_repo: IUserRepository  # ✅ Depend on protocol
    # user_repo: UserRepository  # ❌ Don't depend on implementation
```

This approach ensures:
- ✅ Type checkers verify implementations match protocols
- ✅ Easy to swap implementations (e.g., for testing)
- ✅ Clear separation between interface and implementation
- ✅ Controllers/services are decoupled from infrastructure details

### 4. Organized by Feature

For very large applications, consider organizing by feature instead:

```
app/
├── users/
│   ├── user_entity.py
│   ├── user_repository.py
│   ├── user_service.py
│   └── user_controller.py
│
├── products/
│   ├── product_entity.py
│   ├── product_repository.py
│   ├── product_service.py
│   └── product_controller.py
│
├── container.py
└── main.py
```

## Testing

With this structure, testing becomes straightforward:

**`tests/conftest.py`**:
```python
import pytest
from fastioc import Container
from app.core.interfaces.repositories import IUserRepository
from app.core.interfaces.services import IEmailService

# Mock implementations
class MockUserRepository:
    def get_by_id(self, user_id: int):
        return {"id": user_id, "email": "test@example.com"}

class MockEmailService:
    def send_welcome_email(self, email: str, username: str) -> bool:
        return True

@pytest.fixture
def test_container():
    """Create container with mock dependencies"""
    container = Container()
    container.add_scoped(IUserRepository, MockUserRepository)
    container.add_singleton(IEmailService, MockEmailService)
    return container
```

**`tests/unit/test_user_service.py`**:
```python
from app.services.user_service import UserService

def test_get_user(test_container):
    """Test user service with mocked dependencies"""
    # Get service with injected mocks
    user_service = test_container.resolve(UserService)

    # Test
    user = user_service.get_user(1)
    assert user["id"] == 1
    assert user["email"] == "test@example.com"
```

## Benefits of This Structure

- **Maintainable**: Clear separation of concerns
- **Testable**: Easy to mock dependencies
- **Scalable**: Organized for growth
- **Type-Safe**: Protocol-based with full typing
- **Clean**: Dependencies flow inward
- **Flexible**: Swap implementations easily
- **Documented**: Self-documenting structure

## Related Documentation

- [APIController](controller.md)
- [Dependency Lifetimes](lifetime.md)
- [Nested Dependencies](nested.md)
- [Singleton Cleanup](dispose.md)
