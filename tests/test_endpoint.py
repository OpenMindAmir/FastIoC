from typing import Any

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from .dependencies import State, IGlobalService, INumberService, DirectNumber, GlobalDirectNumber, GetDirectNumber, SetGlobalUsualNumbe
from .constants import *

# --- Application Endpoint Test ---
def test_AppEndpoint(app: FastAPI, client: TestClient, state: State):

    @app.get('/test', dependencies=[IGlobalService, GlobalDirectNumber, Depends(SetGlobalUsualNumbe)])  # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INumberService, number: DirectNumber, number2: int = Depends(GetDirectNumber)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            "txt": text,
            "srv": service,
            "n1": number,
            "n2": number2,
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT
    assert data['srv'] == SERVICE_NUMBER
    assert data['n1'] == data['n2'] == DIRECT_NUMBER
    assert state.GlobalServiceNumber == GLOBAL_SERVICE_NUMBER
    assert state.GlobalDirectNumber == GLOBAL_DIRECT_NUMBER
    assert state.GlobalUsualNumber == GLOBAL_USUAL_NUMBER

