from typing import Any, Annotated

from fastapi import Depends, APIRouter as _APIRouter, FastAPI as _FastAPI
from fastapi.testclient import TestClient

from fastdi.integrations import FastAPI, APIRouter
from fastdi.container import Container

from .dependencies import State, IGlobalService, set_global_usual_number, IGlobalService2, INumberService, LazyNumber, get_lazy_number, get_function_number, FunctionNumber
from .constants import QUERY_TEXT, GLOBAL_SERVICE_NUMBER, GLOBAL_SERVICE_NUMBER2, SERVICE_NUMBER, LAZY_NUMBER, FUNCTION_NUMBER, GLOBAL_USUAL_NUMBER


# --- Application Instance Test
def test_app(state: State, container: Container):

    router = _APIRouter()
    @router.get('/test2')
    def endpoint2(text: str, number: int = Depends(get_function_number)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'num': number,
        }

    app = FastAPI(container=container, dependencies=[IGlobalService, Depends(set_global_usual_number)])  # pyright: ignore[reportArgumentType]
    client = TestClient(app)

    app.add_scoped(LazyNumber, get_lazy_number)

    @app.get('/test', dependencies=[IGlobalService2])  # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INumberService, number: Annotated[int, LazyNumber]) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'num': service.get_number(),
            'lzy': number
        }
    
    app.include_router(router)
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()

    response2 = client.get('/test2', params={'text': QUERY_TEXT})
    data2 = response2.json()
    
    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT # Simple query parameter
    assert data['num'] == SERVICE_NUMBER # Simple dependency
    assert data['lzy'] == LAZY_NUMBER # Added afterwards dependency
    assert state.get().global_service_number == GLOBAL_SERVICE_NUMBER # Global application dependecny (FastDI)
    assert state.get().global_service_number_2 == GLOBAL_SERVICE_NUMBER2 # Endpoint passive dependecny
    assert state.get().global_usual_number ==  GLOBAL_USUAL_NUMBER # Global application dependency (FastAPI)

    # Make sure simple router works correctly
    assert response2.status_code == 200
    assert data2['txt'] == QUERY_TEXT
    assert data2['num'] == FUNCTION_NUMBER


# --- Router Instance Test
def test_router(state: State, app: _FastAPI, router: _APIRouter, client: TestClient, container: Container):

    irouter = APIRouter(container = container, dependencies=[IGlobalService, Depends(set_global_usual_number)]) # pyright: ignore[reportCallIssue]
    irouter.add_scoped(LazyNumber, get_lazy_number)

    @irouter.get('/test', dependencies=[IGlobalService2] ) # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INumberService, number: Annotated[int, LazyNumber]) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'srv': service.get_number(),
            'num': number
        }
    
    app.include_router(irouter)

    @app.get('/test2')
    def endpoint2(text: str, number: int = Depends(get_function_number)) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'num': number
        }
    
    iapp = FastAPI()
    iapp.add_scoped(FunctionNumber, get_function_number)
    iapp.include_router(irouter)

    @iapp.get('/test2')
    def endpoint3(text: str, number: Annotated[int, FunctionNumber]) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'num': number
        }
    
    iclient = TestClient(iapp)

    response = client.get('/test', params= {'text': QUERY_TEXT})
    response2 = client.get('/test2', params= {'text': QUERY_TEXT})
    data = response.json()
    data2 = response2.json()

    iresponse = iclient.get('/test', params= {'text': QUERY_TEXT})
    iresponse2 = iclient.get('/test2', params= {'text': QUERY_TEXT})
    idata = iresponse.json()
    idata2 = iresponse2.json()

    assert response.status_code == response2.status_code == 200
    assert iresponse.status_code == iresponse2.status_code == 200
    assert data['txt'] == data2['txt'] == idata['txt'] == idata2['txt'] == QUERY_TEXT
    assert data['num'] == idata['num'] == LAZY_NUMBER
    assert data['srv'] == idata['srv'] == SERVICE_NUMBER
    assert data2['num'] == idata2['num'] == FUNCTION_NUMBER
    assert state.get().global_service_number == GLOBAL_SERVICE_NUMBER
    assert state.get().global_usual_number == GLOBAL_USUAL_NUMBER

# --- Container Replacement Test
def test_change_container(container: Container):

    app = FastAPI(container = container)
    client = TestClient(app)

    @app.get('/test')
    async def endpoint(service: INumberService) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'srv': service.get_number()
        }

    new_container = Container()

    new_container.add_scoped(LazyNumber, get_lazy_number)

    app.container = new_container

    @app.get('/test2')
    async def endpoint2(number: Annotated[int, LazyNumber]) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'num': number
        }
    
    response = client.get('/test')
    response2 = client.get('/test2')
    data = response.json()
    data2 = response2.json()

    assert response.status_code ==  response2.status_code == 200
    assert data['srv'] == SERVICE_NUMBER
    assert data2['num'] == LAZY_NUMBER