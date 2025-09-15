from typing import Any, Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .dependencies import State, ExtraText, DeepService
from .constants import QUERY_TEXT

# --- Endpoint Parameters Test
def test_parameter(state: State, app: FastAPI, client: TestClient):

    @app.get('/test')
    async def endpoint(text: Annotated[str, ExtraText], service: DeepService) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {
            'txt': text,
            'srv': service.get_params()
        }
    
    response = client.get('/test', params={'extra': QUERY_TEXT}, cookies= {'test': 'test'})
    data = response.json()

    print(data)

    # cookie constant in constants
    # get from Cookie in ExtraText
    # Try to get Request, Security, ... in class annotations