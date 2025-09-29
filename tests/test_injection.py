from typing import Any, Annotated
import logging

from fastapi import FastAPI, APIRouter, Depends
from fastapi.testclient import TestClient

from .dependencies import (State, IGlobalService, INumberService, FunctionNumber, GlobalFunctionNumber,
                        get_function_number, set_global_usual_number, GeneratorDependencyType)
from .constants import (QUERY_TEXT, SERVICE_NUMBER, GENERATOR_NUMBER, FUNCTION_NUMBER, GENERATOR_EXIT_NUMBER,
                        GLOBAL_FUNCTION_NUMBER, GLOBAL_SERVICE_NUMBER, GLOBAL_USUAL_NUMBER)

# --- Application Endpoint Test (Async) ---
def test_app_endpoint(app: FastAPI, client: TestClient, state: State):

    logger = logging.getLogger("FastIoC")
    logger.setLevel(logging.INFO)

    @app.get('/test', dependencies=[IGlobalService, GlobalFunctionNumber, Depends(set_global_usual_number)])  # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INumberService, generator: GeneratorDependencyType, # pyright: ignore[reportUnusedFunction]
                        number: FunctionNumber, number2: Annotated[int, FunctionNumber], 
                        number3: int = Depends(get_function_number)) -> dict[str, Any]: 
        return {
            'txt': text,
            'srv': service.get_number(),
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
    assert data['n1'] == data['n2'] == data['n3'] == FUNCTION_NUMBER  # Inject function as dependency (n1) + Resolve dependency from annotations (n2) + Use FastAPI dependencies alongside FastIoC deps (n3)
    assert state.get().global_service_number == GLOBAL_SERVICE_NUMBER  # Class instance injection in POD (Path Operation Decorator) 
    assert state.get().global_direct_number == GLOBAL_FUNCTION_NUMBER  # Function injection in POD
    assert state.get().global_usual_number == GLOBAL_USUAL_NUMBER  # Use FastAPI dependencies in POD alongside FastIoC deps 
    assert state.get().generator_exit_number == GENERATOR_EXIT_NUMBER  # Ensure that clean-up block of generator works


# --- Router Endpoint Test (Sync) ---
def test_router_endpoint(app: FastAPI, router: APIRouter, client: TestClient, state: State):

    @router.get('/test', dependencies=[IGlobalService])  # pyright: ignore[reportArgumentType]
    def endpoint(text: str, service: INumberService) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'srv': service.get_number()
        }
    
    app.include_router(router)
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    
    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT # Query parameter
    assert data['srv'] == SERVICE_NUMBER # Simple dependency
    assert state.get().global_service_number == GLOBAL_SERVICE_NUMBER # Endpoint passive dependency