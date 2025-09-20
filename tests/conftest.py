"""Pytest fixtures for FastDI integration tests with FastAPI and APIRouter."""

import pytest

from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from fastdi.container import Container

from .dependencies import (State, state as _state, IGlobalService, INumberService, GlobalService,
                            NumberService, FunctionNumber, get_function_number, GlobalFunctionNumber,
                            set_global_function_number, generator_dependency, GeneratorDependencyType,
                            DependentNestedNumber, get_dependent_nested_number, INestedService,
                            NestedService, IGlobalNestedNumber, GlobalNestedNumber,
                            IGlobalNestedService, GlobalNestedService, ILifetimeServiceSingleton,
                            ILifetimeServiceScoped, ILifetimeServiceFactory, LifetimeServiceSingleton,
                            LifetimeServiceScoped, LifetimeServiceFactory, IGlobalService2, GlobalService2,
                            INumberService2, NumberService2, ExtraText, get_extra_text, DeepService,
                            DeeperSerivce, IDisposable, Disposable)


@pytest.fixture
def container():
    """Provide a DI container with common test dependencies registered."""
    container = Container()
    # General (Injection)
    container.add_scoped(INumberService, NumberService)
    container.add_scoped(IGlobalService, GlobalService)
    container.add_scoped(FunctionNumber, get_function_number)
    container.add_scoped(GlobalFunctionNumber, set_global_function_number)
    container.add_scoped(GeneratorDependencyType, generator_dependency)
    # Nested
    container.add_scoped(INumberService2, NumberService2)
    container.add_scoped(DependentNestedNumber, get_dependent_nested_number)
    container.add_scoped(IGlobalNestedNumber, GlobalNestedNumber)
    container.add_scoped(IGlobalNestedService, GlobalNestedService)
    container.add_scoped(INestedService, NestedService)
    # Lifetime
    container.add_singleton(ILifetimeServiceSingleton,LifetimeServiceSingleton)
    container.add_scoped(ILifetimeServiceScoped, LifetimeServiceScoped)
    container.add_transient(ILifetimeServiceFactory, LifetimeServiceFactory)
    # Integrations
    container.add_scoped(IGlobalService2, GlobalService2)
    # Integrity
    container.add_scoped(DeeperSerivce, DeeperSerivce)
    container.add_scoped(DeepService, DeepService)
    container.add_scoped(ExtraText, get_extra_text)
    # Dispose
    container.add_singleton(IDisposable, Disposable)

    return container


@pytest.fixture
def router(container: Container) -> APIRouter:
    router = APIRouter()
    container.injectify(router)
    return router


@pytest.fixture
def app(container: Container) -> FastAPI:
    app = FastAPI()
    container.injectify(app)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def state() -> State:
    return _state


@pytest.fixture(autouse=True)
def reset(state: State):
    state.reset()
