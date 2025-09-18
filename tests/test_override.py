from typing import Any, Annotated

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from fastdi.container import Container

from .dependencies import (State, INumberService, IGlobalService, OverrideNumberSerivce, GlobalOverrideService,
                            get_function_number, get_override_function_number, LifetimeOverrideServiceFactory, 
                            LifetimeOverrideServiceScoped, LifetimeOverrideServiceSingleton, ILifetimeServiceSingleton,
                            ILifetimeServiceScoped, ILifetimeServiceFactory, ILifetimeService)
from .constants import OVERRIDE_NUMBER, OVERRIDE_SERVICE_NUMBER, GLOBAL_OVERRIDE_NUMBER, OVERRIDE_NUMBERS


# --- Override Test
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

# --- Override with Lifetime Test
def test_override_lifetime(app: FastAPI, client: TestClient, container: Container):

    test_container = Container()
    test_container.add_singleton(ILifetimeServiceSingleton, LifetimeOverrideServiceSingleton)
    test_container.add_transient(ILifetimeServiceScoped, LifetimeOverrideServiceScoped)
    test_container.add_transient(ILifetimeServiceFactory, LifetimeOverrideServiceFactory)

    app.dependency_overrides = container.override(container=test_container)

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
    assert data['t1'] == data['t2'] == _data['t1'] == _data['t2'] == data['r1'] == _data['r1'] == data['s'] == OVERRIDE_NUMBERS[1]
    assert data['r2'] == _data['r2'] == _data['s'] == OVERRIDE_NUMBERS[2]