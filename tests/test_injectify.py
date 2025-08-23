import pytest
from typing import Protocol, Any

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from fastdi import Container, Injectify


# Dependencies
class IService(Protocol):
    def GetNumber(self) -> int: ...


class Service(IService):
    def __init__(self) -> None:
        self.number = 5

    def GetNumber(self) -> int:
        return self.number
    
def GetMessage() -> str:
    return 'message'

text = 'text'
    
# Setup container
container = Container()
container.AddFactory(IService, Service)

# Fixtures
@pytest.fixture
def app():
    app = FastAPI()
    Injectify(app, container)
    return app

@pytest.fixture
def client(app: FastAPI):
    return TestClient(app)

# --- Test 1: Endpoint 1 layer dependency injection ---
def test_simpleEndpoint(app: FastAPI, client: TestClient):

    @app.get('/test')
    def testEndpoint(text: str, service: IService, message: str = Depends(GetMessage)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {'number': service.GetNumber(), 'message': message, 'text': text}
    
    response = client.get('/test', params={'text': text})
    data = response.json()
    assert response.status_code == 200
    assert data['number'] == 5
    assert data['message'] == GetMessage()
    assert data['text'] == text