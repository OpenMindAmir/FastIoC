from typing import Any, Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .dependencies import ILifetimeServiceSingleton, ILifetimeServiceScoped, ILifetimeServiceFactory, ILifetimeService
from .constants import NUMBERS

# --- Lifetime Test ---
def test_Lifetime(app: FastAPI, client: TestClient):

    @app.get('/test')
    async def endpoint(singleton: ILifetimeServiceSingleton, scoped: ILifetimeServiceScoped, _scoped: Annotated[ILifetimeService, ILifetimeServiceScoped], factory: ILifetimeServiceFactory, _factory: Annotated[ILifetimeService, ILifetimeServiceFactory]) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            's': singleton.get_current_item(),
            'r1': scoped.get_current_item(),
            'r2': _scoped.get_current_item(),
            'f1': factory.get_current_item(),
            'f2': _factory.get_current_item(),
        }
    
    response = client.get('/test')
    _response = client.get('/test')
    data = response.json()
    _data = _response.json()

    assert response.status_code == _response.status_code == 200
    assert data['f1'] == data['f2'] == _data['f1'] == _data['f2'] == data['r1'] == _data['r1'] == data['s'] == NUMBERS[1]
    assert data['r2'] == _data['r2'] == _data['s'] == NUMBERS[2]