import pytest

from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from fastdi.container import Container
from fastdi.injectify import Injectify

from .dependencies import State, state as _state, IGlobalService, INumberService, GlobalService, NumberService, FunctionNumber, GetFunctionNumber, GlobalFunctionNumber, SetGlobalFunctionNumber, GeneratorDependency, GeneratorDependencyType, DependentNestedNumber, GetDependentNestedNumber, INestedService, NestedService, IGlobalNestedNumber, GlobalNestedNumber, IGlobalNestedService, GlobalNestedService, ILifetimeServiceSingleton, ILifetimeServiceScoped, ILifetimeServiceFactory, LifetimeServiceSingleton, LifetimeServiceScoped, LifetimeServiceFactory


@pytest.fixture
def container():
    container = Container()
    # General (Injection)
    container.AddScoped(INumberService, NumberService)
    container.AddScoped(IGlobalService, GlobalService)
    container.AddScoped(FunctionNumber, GetFunctionNumber)
    container.AddScoped(GlobalFunctionNumber, SetGlobalFunctionNumber)
    container.AddScoped(GeneratorDependencyType, GeneratorDependency)
    # Nested
    container.AddScoped(DependentNestedNumber, GetDependentNestedNumber)
    container.AddScoped(IGlobalNestedNumber, GlobalNestedNumber)
    container.AddScoped(IGlobalNestedService, GlobalNestedService)
    container.AddScoped(INestedService, NestedService)
    # Lifetime
    container.AddSingleton(ILifetimeServiceSingleton, LifetimeServiceSingleton)
    container.AddScoped(ILifetimeServiceScoped, LifetimeServiceScoped)
    container.AddFactory(ILifetimeServiceFactory, LifetimeServiceFactory)

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
