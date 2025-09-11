from fastapi.testclient import TestClient
from fastapi.params import Depends

from fastdi.integrations import FastAPI
from fastdi.definitions import Dependency

from .dependencies import INumberService, NumberService
from .constants import SERVICE_NUMBER

# --- Test hook
def test_hook():
    App = FastAPI()

    RegisterNumber: int = 0
    ResolveNumber: int = 0

    def RegisterHook(dependency: Dependency[INumberService]):
        nonlocal RegisterNumber
        RegisterNumber = dependency.concrete().GetNumber()
        return dependency
    
    def ResolveHook(dependency: Depends):
        nonlocal ResolveNumber
        ResolveNumber = dependency.dependency().GetNumber()  # pyright: ignore[reportOptionalCall]
        return dependency

    App.container.BeforeRegisterHook = RegisterHook
    App.container.BeforeResolveHook = ResolveHook

    App.AddScoped(INumberService, NumberService)


    @App.get('/test')
    def endpoint(service: INumberService) -> int:  # pyright: ignore[reportUnusedFunction]
        return service.GetNumber()
    
    client = TestClient(App)

    response = client.get('/test')
    data = response.json()

    assert response.status_code == 200
    assert data == RegisterNumber == ResolveNumber == SERVICE_NUMBER