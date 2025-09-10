from typing import Any, Annotated, Protocol

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastdi.container import Container

from .constants import PROVIDER_NUMBER

# --- Provider Test


def test_provider(app: FastAPI, client: TestClient, container: Container):

    # Get protocol from base class

    class IProviderService(Protocol):

        def ProvideNumber(self) -> int:
            ...

    @container.ProvideScoped()
    class ProviderService(IProviderService):  # pyright: ignore[reportUnusedClass]

        def ProvideNumber(self) -> int:
            return PROVIDER_NUMBER
        
    # Self-protocol class

    @container.ProvideScoped()
    class ProviderSelfService():

        def ProvideNumber(self) -> int:
            return PROVIDER_NUMBER
        
    # NonClass

    class ProvidedInt(int): ...

    @container.ProvideScoped(ProvidedInt)
    def GetProvidedInt() -> int:  # pyright: ignore[reportUnusedFunction]
        return PROVIDER_NUMBER
    
    # BEGIN Test

    @app.get('/test')
    def endpoint(service: IProviderService, selfed: Annotated[IProviderService, ProviderSelfService], nclass: Annotated[int, ProvidedInt]) -> dict[str, Any]: # pyright: ignore[reportUnusedFunction]
        return {
            'srv': service.ProvideNumber(),
            'slf': selfed.ProvideNumber(),
            'ncl': nclass
        }
    
    response = client.get('/test')
    data = response.json()

    assert response.status_code == 200
    assert data['srv'] == data['slf'] == data['ncl'] == PROVIDER_NUMBER
        
    