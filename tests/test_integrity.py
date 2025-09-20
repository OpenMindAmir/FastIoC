from typing import Any, Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .dependencies import ExtraText, DeepService, State
from .constants import QUERY_TEXT, COOKIE_NUMBER, BACKGROUND_NUMBER

# --- Endpoint Parameters Test
def test_parameter(state: State , app: FastAPI, client: TestClient):

    @app.get('/test')
    async def endpoint(text: Annotated[str, ExtraText], service: DeepService) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text[0],
            'id': text[1],
            'srv': service.get_id(),
            'dep': service.get_deep_id(),
            'cki': service.get_deep_cookie(),
            'ann': service.get_annotated_id()
        }
    
    response = client.get('/test', params={'extra': QUERY_TEXT}, cookies= {'id': str(COOKIE_NUMBER)})
    data = response.json()
    print(data)

    assert response.status_code == 200
    assert data['txt'] == QUERY_TEXT
    assert data['id'] == data['srv'] == data['dep'] == data['cki'] == data['ann'] == COOKIE_NUMBER
    assert state.get().background_number == BACKGROUND_NUMBER