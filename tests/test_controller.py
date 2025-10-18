from typing import Any, Annotated
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastioc.container import Container
from fastioc.controller import APIController, get

from .dependencies import State, INumberService, IGlobalService, IGlobalService2, INestedService, FunctionNumber
from .constants import SERVICE_NUMBER, GLOBAL_SERVICE_NUMBER, GLOBAL_SERVICE_NUMBER2, NESTED_NUMBER, FUNCTION_NUMBER


# --- Controller Test
def test_controller(state: State, app: FastAPI, client: TestClient, container: Container):

    class TestController(APIController):
        config = {
            'prefix': '/ctrl',
            'dependencies': [IGlobalService2]
        }

        service: INestedService
        number: int

        def __init__(self, number: Annotated[int, FunctionNumber]):
            self.number = number

        @get('/test', dependencies=[IGlobalService])  # pyright: ignore[reportArgumentType]
        async def endpoint(self, service: INumberService) -> dict[str, Any]:
            return {
                'srv': service.get_number(),
                'nst': self.service.get_number(),
                'num': self.number
            }

    app.include_router(TestController.router({'container': container}))

    response = client.get('/ctrl/test')
    data = response.json()

    assert response.status_code == 200
    assert data['srv'] == SERVICE_NUMBER
    assert data['nst'] == NESTED_NUMBER
    assert data['num'] == FUNCTION_NUMBER
    assert state.get().global_service_number == GLOBAL_SERVICE_NUMBER
    assert state.get().global_service_number_2 == GLOBAL_SERVICE_NUMBER2
