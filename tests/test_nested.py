from typing import Any, Annotated

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from .dependencies import State, INestedService, IGlobalNestedService, DependentNestedNumber, get_dependent_nested_number
from .constants import QUERY_TEXT, SERVICE_NUMBER, NESTED_NUMBER

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
            'txt': text
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    
    assert response.status_code == 200
    assert data['n2'] == SERVICE_NUMBER
    assert data['n1'] == data['n3'] == data['n4'] == data['n5'] == state.get().nested_number == NESTED_NUMBER
    assert data['txt'] == QUERY_TEXT