from typing import Any, Annotated
import pytest

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from fastdi.container import Container
from fastdi.errors import SingletonLifetimeViolationError, SingletonGeneratorError

from .dependencies import State, INestedService, IGlobalNestedService, DependentNestedNumber, get_dependent_nested_number, NestedService, ISingletonNestedService
from .constants import QUERY_TEXT, SERVICE_NUMBER, NESTED_NUMBER, SERVICE_NUMBER_2

# --- Nested Dependencies Test
def test_nested(app: FastAPI, client: TestClient, state: State):
    
    @app.get('/test', dependencies=[IGlobalNestedService])  # pyright: ignore[reportArgumentType]
    async def endpoint(text: str, service: INestedService, nested: Annotated[int, DependentNestedNumber], usual: int = Depends(get_dependent_nested_number)) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'n1': service.get_number(),
            'n2': service.get_service_number(),
            'n3': service.get_nested_number(),
            'n4': nested,
            'n5': usual,
            'n6': service.get_service_number_2(),
            'txt': text
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    
    assert response.status_code == 200, data
    assert data['n2'] == SERVICE_NUMBER
    assert data['n1'] == data['n3'] == data['n4'] == data['n5'] == state.get().nested_number == NESTED_NUMBER
    assert data['n6'] == SERVICE_NUMBER_2
    assert data['txt'] == QUERY_TEXT

# --- Nested Singleton Test (+ Singleton Errors Test)
def test_nested_singleton(app: FastAPI, client: TestClient, container: Container):

    with pytest.raises(SingletonGeneratorError):
        def test_generator():
            yield 1
        container.add_singleton(type, test_generator)

    with pytest.raises(SingletonLifetimeViolationError):
        container.add_singleton(INestedService, NestedService)

    @app.get('/test',)
    async def endpoint(text: str, service: ISingletonNestedService) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'n1': service.get_service_number(),
            'n2': service.get_service_number_2(),
            'txt': text
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    
    assert response.status_code == 200
    assert data['n1'] == data['n2'] == SERVICE_NUMBER_2
    assert data['txt'] == QUERY_TEXT
