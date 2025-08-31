from typing import Any, Annotated

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from .dependencies import State, INestedService, IGlobalNestedService, DependentNestedNumber, GetDependentNestedNumber
from .constants import *

# --- Nested Dependencies Test
def test_nested(app: FastAPI, client: TestClient, state: State):
    
    @app.get('/test', dependencies=[IGlobalNestedService])  # pyright: ignore[reportArgumentType]
    def endpoint(text: str, service: INestedService, nested: Annotated[int, DependentNestedNumber], usual: int = Depends(GetDependentNestedNumber)) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'n1': service.GetNumber(),
            'n2': service.GetServiceNumber(),
            'n3': service.GetNestedNumber(),
            'n4': nested,
            'n5': usual,
            'txt': text
        }
    
    response = client.get('/test', params={'text': QUERY_TEXT})
    data = response.json()
    assert response.status_code == 200
    assert data['n2'] == SERVICE_NUMBER
    assert data['n1'] == data['n3'] == data['n4'] == data['n5'] == state.NestedNumber == NESTED_NUMBER
    assert data['txt'] == QUERY_TEXT