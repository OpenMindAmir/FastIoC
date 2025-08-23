import pytest
from typing import Protocol

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastdi import Container, Injectify


# Interfaces & Implementations
class IService(Protocol):
    def GetNumber(self) -> int: ...


class Service(IService):
    def __init__(self) -> None:
        self.number = 5

    def GetNumber(self) -> int:
        return self.number
    
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

# --- Test 1: Enpoint dependency injection ---
def test_simpleEndpoint(app: FastAPI, client: TestClient):

    @app.get('/test')
    def testEndpoint(service: IService): # pyright: ignore[reportUnusedFunction]
        return {'number': service.GetNumber()}
    
    response = client.get('/test')
    assert response.status_code == 200
    assert response.json() == {'number': 5}