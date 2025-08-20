import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from fastdi import Container, Injectify
from fastdi.custom_types import LifeTime

from typing import Protocol, TypedDict

class IService(Protocol):

    def GetValue(self) -> int: ...

class ServiceSingleton(IService):
    def __init__(self):
        self.counter = 0

    def GetValue(self) -> int:
        self.counter += 1
        return self.counter
class ServiceFactory(IService):
    def __init__(self):
        self.counter = 0

    def GetValue(self) -> int:
        self.counter += 1
        return self.counter
class ServiceScoped(IService):
    def __init__(self):
        self.counter = 0

    def GetValue(self) -> int:
        self.counter += 1
        return self.counter
class ReturnValue(TypedDict):
    ServiceNumber: int
    NormalDependencyText: str
    ParameterText: str

NormalText = "Normal"
def NormalDependency() -> str:
    return NormalText

ParamText1 = 'Hi'
ParamText2 = 'Bye'
    
@pytest.mark.parametrize('lifeTime, implementation', [
    (LifeTime.SINGLETON, ServiceSingleton),
    (LifeTime.FACTORY, ServiceFactory),
    (LifeTime.SCOPED, ServiceScoped)  
])
def test_ContainerLifeTimes(lifeTime: LifeTime, implementation: type):
    app = FastAPI()
    container = Container()
    container.Register(IService, implementation, lifeTime)

    # dependable: FastAPIDependable = container.Resolve(IService)

    @app.get('/test', response_model=None)
    def route(text: str, service: IService, normal: str = Depends(NormalDependency)): # type: ignore[unused]
        return {
            'ServiceNumber': service.GetValue(),
            'NormalDependencyText': normal,
            'ParameterText': text
        }
    
    Injectify(app, container)
    
    client = TestClient(app)

    r1: ReturnValue = client.get('/test', params={'text': ParamText1}).json()
    r2: ReturnValue = client.get('/test', params={'text': ParamText2}).json()

    if lifeTime is LifeTime.SINGLETON:
        assert r2["ServiceNumber"] > r1['ServiceNumber']
        assert r1['NormalDependencyText'] == r2['NormalDependencyText'] == NormalText
        assert r1['ParameterText'] == ParamText1
        assert r2['ParameterText'] == ParamText2
    
    if lifeTime is LifeTime.FACTORY:
        assert r2["ServiceNumber"] == r1['ServiceNumber']
        assert r1['NormalDependencyText'] == r2['NormalDependencyText'] == NormalText
        assert r1['ParameterText'] == ParamText1
        assert r2['ParameterText'] == ParamText2

    if lifeTime is LifeTime.SCOPED:
        assert r2["ServiceNumber"] == r1['ServiceNumber']
        assert r1['NormalDependencyText'] == r2['NormalDependencyText'] == NormalText
        assert r1['ParameterText'] == ParamText1
        assert r2['ParameterText'] == ParamText2
