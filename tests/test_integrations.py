from typing import Any, Annotated

from fastapi import Depends
from fastapi.testclient import TestClient

from fastdi.integrations import FastAPI, APIRouter
from fastdi.container import Container

from .dependencies import State, IGlobalService, SetGlobalUsualNumber, IGlobalService2, INumberService, LazyNumber, GetLazyNumber, IGlobalService3, GlobalService3
from .constants import QUERY_TEXT, GLOBAL_SERVICE_NUMBER, GLOBAL_SERVICE_NUMBER2, SERVICE_NUMBER, LAZY_NUMBER, GLOBAL_SERVICE_NUMBER3


# --- Application instance test
def test_app(state: State, container: Container):

    app = FastAPI(container=container, dependencies=[IGlobalService, Depends(SetGlobalUsualNumber)])  # pyright: ignore[reportArgumentType]
    client = TestClient(app)

    app.AddScoped(LazyNumber, GetLazyNumber)
    app.AddScoped(IGlobalService3, GlobalService3)

    app.AddGlobalDependency(IGlobalService3)

    @app.get('/test', dependencies=[IGlobalService2])  # pyright: ignore[reportArgumentType]
    def endpoint(text: str, service: INumberService, number: Annotated[int, LazyNumber]) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'num': service.GetNumber(),
            'lzy': number
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    
    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT # Simple query parameter
    assert data['num'] == SERVICE_NUMBER # Simple dependency
    assert data['lzy'] == LAZY_NUMBER # Added afterwards dependency
    assert state.get().GlobalServiceNumber == GLOBAL_SERVICE_NUMBER # Global application dependecny
    assert state.get().GlobalServiceNumber2 == GLOBAL_SERVICE_NUMBER2 # Endpoint passive dependecny
    assert state.get().GlobalServiceNumber3 == GLOBAL_SERVICE_NUMBER3 # Added & requested afterwards global application dependency