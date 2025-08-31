from typing import Any

from fastapi import FastAPI, APIRouter, Depends
from fastapi.testclient import TestClient

from .dependencies import State, IGlobalService, INumberService, DirectNumber, GlobalDirectNumber, GetDirectNumber, SetGlobalUsualNumber, GeneratorDependencyType
from .constants import *

# --- Application Endpoint Test ---
def test_AppEndpoint(app: FastAPI, client: TestClient, state: State):

    @app.get('/test', dependencies=[IGlobalService, GlobalDirectNumber, Depends(SetGlobalUsualNumber)])  # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INumberService, generator: GeneratorDependencyType, number: DirectNumber, number2: int = Depends(GetDirectNumber)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'srv': service.GetNumber(),
            'gnr': generator, 
            'n1': number,
            'n2': number2,
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT  # Get & parse query parameter correctly (alongside dependencies)
    assert data['srv'] == SERVICE_NUMBER  # Inject class instance as dependency 
    assert data['gnr'] == GENERATOR_NUMBER  # Inject generator as dependency
    assert data['n1'] == data['n2'] == DIRECT_NUMBER  # Inject function as dependency + Use FastAPI dependencies alongside FastDI deps
    assert state.GlobalServiceNumber == GLOBAL_SERVICE_NUMBER  # Class instance injection in POD (Path Operation Decorator) 
    assert state.GlobalDirectNumber == GLOBAL_DIRECT_NUMBER  # Function injection in POD
    assert state.GlobalUsualNumber == GLOBAL_USUAL_NUMBER  # Use FastAPI dependencies in POD alongside FastDI deps 
    assert state.GeneratorExitNumber == GENERATOR_EXIT_NUMBER  # Ensure that clean-up block of generator works


# --- Router Endpoint Test ---
def test_RouterEndpoint(app: FastAPI, router: APIRouter, client: TestClient, state: State):

    @router.get('/test', dependencies=[IGlobalService])  # pyright: ignore[reportArgumentType]
    def endpoint(text: str, service: INumberService) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'srv': service.GetNumber()
        }
    
    app.include_router(router)
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT
    assert data['srv'] == SERVICE_NUMBER
    assert state.GlobalServiceNumber == GLOBAL_SERVICE_NUMBER