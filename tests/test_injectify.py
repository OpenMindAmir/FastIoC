import pytest
from typing import Protocol, Any

from fastapi import FastAPI, APIRouter, Depends
from fastapi.testclient import TestClient

from fastdi.container import Container
from fastdi.injectify import Injectify


# Dependencies
class INumberService(Protocol):
    def GetNumber(self) -> int: ...
class NumberService(INumberService):
    def __init__(self) -> None:
        self.number = 5

    def GetNumber(self) -> int:
        return self.number
    
def GetMessage() -> str:
    return 'message'

text = 'text'

number1 = 0
number2 = 0
class IGlobalNumber(Protocol):
    ...

class GlobalNumber(IGlobalNumber):
    def __init__(self) -> None:
        global number1
        number1 += 2

def IncreaseNumber2():
    global number2
    number2 += 3

# ---

number3 = 0
number4 = 0

class IGlobalNumber2(Protocol):
    ...

class GlobalNumber2(IGlobalNumber2):
    def __init__(self) -> None:
        global number3
        number3 += 4

def IncreaseNumber4():
    global number4
    number4 += 5

# Setup container
container = Container()
container.AddFactory(INumberService, NumberService)
container.AddFactory(IGlobalNumber, GlobalNumber)
container.AddFactory(IGlobalNumber2, GlobalNumber2)

# Fixtures
@pytest.fixture
def app():
    app = FastAPI()
    Injectify(app, container)
    return app

@pytest.fixture
def client(app: FastAPI):
    return TestClient(app)

# --- Test 1: Application Endpoints ---
def test_AppEndpoint(app: FastAPI, client: TestClient):

    @app.get('/test', dependencies=[IGlobalNumber, Depends(IncreaseNumber2)]) # pyright: ignore[reportArgumentType]
    def endpoint(text: str, service: INumberService, message: str = Depends(GetMessage)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {'number': service.GetNumber(), 'message': message, 'text': text}
    
    response = client.get('/test', params={'text': text})
    data = response.json()
    assert response.status_code == 200
    assert data['number'] == 5
    assert data['message'] == GetMessage()
    assert data['text'] == text
    assert number1 == 2
    assert number2 == 3

# --- Test 2: Router Endpoints ---
def test_RouterEndpoint(app: FastAPI, client: TestClient):
    router = APIRouter(dependencies=[Depends(IncreaseNumber4)]) # pyright: ignore[reportArgumentType]
    Injectify(router, container)

    @router.get('/test', dependencies=[Depends(IncreaseNumber4), IGlobalNumber2])  # pyright: ignore[reportArgumentType]
    def endpoint(text: str, service: INumberService) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {'number': service.GetNumber(), 'text': text}
    
    app.include_router(router)
    response = client.get('/test', params={'text': text})
    assert response.status_code == 200
    assert response.json() == {'number': 5, 'text': text}
    assert number3 == 4
    assert number4 == 5