from typing import Any, Annotated

from fastapi import FastAPI, APIRouter, Depends
from fastapi.testclient import TestClient

from .dependencies import State, IGlobalService, INumberService, FunctionNumber, GlobalFunctionNumber, GetFunctionNumber, SetGlobalUsualNumber, GeneratorDependencyType
from .constants import QUERY_TEXT, SERVICE_NUMBER, GENERATOR_NUMBER, FUNCTION_NUMBER, GENERATOR_EXIT_NUMBER, GLOBAL_FUNCTION_NUMBER, GLOBAL_SERVICE_NUMBER, GLOBAL_USUAL_NUMBER

# --- Application Endpoint Test (Async) ---
def test_AppEndpoint(app: FastAPI, client: TestClient, state: State):

    @app.get('/test', dependencies=[IGlobalService, GlobalFunctionNumber, Depends(SetGlobalUsualNumber)])  # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INumberService, generator: GeneratorDependencyType, number: FunctionNumber, number2: Annotated[int, FunctionNumber], number3: int = Depends(GetFunctionNumber)) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'srv': service.GetNumber(),
            'gnr': generator, 
            'n1': number,
            'n2': number2,
            'n3': number3
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()

    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT  # Get & parse query parameter correctly (alongside dependencies)
    assert data['srv'] == SERVICE_NUMBER  # Inject class instance as dependency 
    assert data['gnr'] == GENERATOR_NUMBER  # Inject generator as dependency
    assert data['n1'] == data['n2'] == data['n3'] == FUNCTION_NUMBER  # Inject function as dependency (n1) + Resolve dependency from annotations (n2) + Use FastAPI dependencies alongside FastDI deps (n3)
    assert state.get().GlobalServiceNumber == GLOBAL_SERVICE_NUMBER  # Class instance injection in POD (Path Operation Decorator) 
    assert state.get().GlobalDirectNumber == GLOBAL_FUNCTION_NUMBER  # Function injection in POD
    assert state.get().GlobalUsualNumber == GLOBAL_USUAL_NUMBER  # Use FastAPI dependencies in POD alongside FastDI deps 
    assert state.get().GeneratorExitNumber == GENERATOR_EXIT_NUMBER  # Ensure that clean-up block of generator works


# --- Router Endpoint Test (Sync) ---
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
    assert state.get().GlobalServiceNumber == GLOBAL_SERVICE_NUMBER