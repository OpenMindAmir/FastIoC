from typing import Any, Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .dependencies import ILifetimeServiceSingleton, ILifetimeServiceScoped, ILifetimeServiceFactory, ILifetimeService
from .constants import NUMBERS

# --- Lifetime Test
def test_lifetime(app: FastAPI, client: TestClient):

    @app.get('/test')
    async def endpoint(singleton: ILifetimeServiceSingleton, scoped: ILifetimeServiceScoped, _scoped: Annotated[ILifetimeService, ILifetimeServiceScoped], transient: ILifetimeServiceFactory, _transient: Annotated[ILifetimeService, ILifetimeServiceFactory]) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            's': singleton.get_current_item(),
            'r1': scoped.get_current_item(),
            'r2': _scoped.get_current_item(),
            't1': transient.get_current_item(),
            't2': _transient.get_current_item(),
        }
    
    response = client.get('/test')
    _response = client.get('/test')
    data = response.json()
    _data = _response.json()

    assert response.status_code == _response.status_code == 200
    assert data['t1'] == data['t2'] == _data['t1'] == _data['t2'] == data['r1'] == _data['r1'] == data['s'] == NUMBERS[1]
    assert data['r2'] == _data['r2'] == _data['s'] == NUMBERS[2]