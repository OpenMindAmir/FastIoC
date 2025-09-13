from typing import Any

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from fastdi.container import Container

from .dependencies import State, INumberService, IGlobalService, OverrideNumberSerivce, GlobalOverrideService, get_function_number, get_override_function_number
from .constants import OVERRIDE_NUMBER, OVERRIDE_SERVICE_NUMBER, GLOBAL_OVERRIDE_NUMBER


# --- Test override
def test_override(state: State, app: FastAPI, client: TestClient, container: Container):

    test_container = Container()
    test_container.add_scoped(IGlobalService, GlobalOverrideService)
    test_container.add_scoped(INumberService, OverrideNumberSerivce)

    dependency_overrides = {get_function_number: get_override_function_number}

    app.dependency_overrides = container.override(dependency_overrides, test_container)

    @app.get('/test', dependencies=[IGlobalService])  # pyright: ignore[reportArgumentType]
    async def endpoint(service: INumberService, number: int = Depends(get_function_number)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'srv': service.get_number(),
            'num': number
        }
    
    response = client.get('/test')
    data = response.json()

    assert response.status_code == 200
    assert data['srv'] == OVERRIDE_SERVICE_NUMBER
    assert data['num'] == OVERRIDE_NUMBER
    assert state.get().global_override_number == GLOBAL_OVERRIDE_NUMBER