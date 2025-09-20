from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastdi.container import Container

from .dependencies import State
from .constants import DISPOSE_NUMBER

# --- Dispose Test
def test_dispose(state: State, container: Container):

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await container.dispose()

    app = FastAPI(lifespan=lifespan)

    container.injectify(app)

    @app.get('/')
    async def endpoint() -> int:  # pyright: ignore[reportUnusedFunction]
        return 1
    
    with TestClient(app) as client:
        response = client.get('/')

    assert response.status_code == 200
    assert state.get().dispose_number == DISPOSE_NUMBER