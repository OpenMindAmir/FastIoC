from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastioc.container import Container
from fastioc.controller import APIController, get

from .dependencies import State, INumberService, IGlobalService
from .constants import SERVICE_NUMBER, GLOBAL_SERVICE_NUMBER


# --- Controller Test
def test_controller(state: State, app: FastAPI, client: TestClient, container: Container):

    class TestController(APIController):
        prefix = '/ctrl'
        __router_params__= {'container': container}

        @get('/test', dependencies=[IGlobalService])  # pyright: ignore[reportArgumentType]
        async def endpoint(self, service: INumberService) -> int:
            return service.get_number()

    app.include_router(TestController.create_router())

    response = client.get('/ctrl/test')

    assert response.status_code == 200
    assert response.json() == SERVICE_NUMBER
    assert state.get().global_service_number == GLOBAL_SERVICE_NUMBER
