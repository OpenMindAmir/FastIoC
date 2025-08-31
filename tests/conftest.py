import pytest

from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from fastdi.container import Container
from fastdi.injectify import Injectify

from .dependencies import State, state as _state, IGlobalService, INumberService, GlobalService, NumberService, DirectNumber, GetDirectNumber, GlobalDirectNumber, SetGlobalDirectNumber, GeneratorDependency, GeneratorDependencyType


@pytest.fixture
def container():
    container = Container()
    container.AddScoped(INumberService, NumberService)
    container.AddScoped(IGlobalService, GlobalService)
    container.AddScoped(DirectNumber, GetDirectNumber)
    container.AddScoped(GlobalDirectNumber, SetGlobalDirectNumber)
    container.AddScoped(GeneratorDependencyType, GeneratorDependency)
    return container


@pytest.fixture
def router(container: Container):
    router = APIRouter()
    Injectify(router, container)
    return router


@pytest.fixture
def app(container: Container):
    app = FastAPI()
    Injectify(app, container)
    return app


@pytest.fixture
def client(app: FastAPI):
    return TestClient(app)


@pytest.fixture
def state():
    return _state


@pytest.fixture(autouse=True)
def reset(state: State):
    state.reset()
