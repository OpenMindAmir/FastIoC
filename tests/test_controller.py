from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastioc.controller import APIController
from fastioc.container import Container
from fastioc import get

from .dependencies import State


# --- Controller Test
def test_controller(state: State, app: FastAPI, client: TestClient, container: Container):

    class TestController(APIController):
        prefix = '/ctrl'

        @get('/test')
        async def endpoint(self) -> int:
            return 1
        

    app.include_router(TestController.create_router())

    response = client.get('/ctrl/test')

    assert response.status_code == 200
    assert response.json() == 1
