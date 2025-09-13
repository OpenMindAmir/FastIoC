from fastapi.testclient import TestClient
from fastapi.params import Depends

from fastdi.integrations import FastAPI
from fastdi.definitions import Dependency

from .dependencies import INumberService, NumberService
from .constants import SERVICE_NUMBER

# --- Test hook
def test_hook():
    app = FastAPI()

    register_number: int = 0
    resolve_number: int = 0

    def register_hook(dependency: Dependency[INumberService]):
        nonlocal register_number
        register_number = dependency.implementation().get_number()
        return dependency
    
    def resolve_hook(dependency: Depends):
        nonlocal resolve_number
        resolve_number = dependency.dependency().get_number()  # pyright: ignore[reportOptionalCall]
        return dependency

    app.container.before_register_hook = register_hook
    app.container.before_resolve_hook = resolve_hook

    app.add_scoped(INumberService, NumberService)


    @app.get('/test')
    def endpoint(service: INumberService) -> int:  # pyright: ignore[reportUnusedFunction]
        return service.get_number()
    
    client = TestClient(app)

    response = client.get('/test')
    data = response.json()

    assert response.status_code == 200
    assert data == register_number == resolve_number == SERVICE_NUMBER