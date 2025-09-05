from typing import Any
from typing_extensions import Self

from fastapi import FastAPI as _FastAPI, APIRouter as _APIRouter
from fastapi.params import Depends

from fastdi.container import Container
from fastdi.injectify import Injectify
from fastdi.definitions import FastDIConcrete

class FastAPI(_FastAPI):
    
    _container: Container
    _dependencies: list[type | Depends]

    def __new__(cls, *args: Any, container: Container = Container(), **kwargs: Any) -> Self:
        instance = super().__new__(cls)
        super(FastAPI, instance).__init__(*args, **kwargs)
        Injectify(instance, container)
        instance._container = container
        return instance

    # def AddSingleton(self, protocol: type, concrete: FastDIConcrete):
    #     self._container.AddSingleton(protocol, concrete)

    # def AddScoped(self, protocol: type, concrete: FastDIConcrete):
    #     self._container.AddScoped(protocol, concrete)

    # def AddFactory(self, protocol: type, concrete: FastDIConcrete):
    #     self._container.AddFactory(protocol, concrete)
    

    # TODO check before first load with global state or something like that, consider DX
