from typing import Any
from fastapi import FastAPI as _FastAPI
from fastdi import Container
import uvicorn

class FastAPI(_FastAPI):
    _container: Container

    def __new__(cls, *args: Any, **kwargs: Any):
        instance = super().__new__(cls)
        super(FastAPI, instance).__init__(*args, **kwargs)
        instance._container = Container()
        return instance

    @property
    def container(self) -> Container:
        return self._container
    
    @container.setter
    def container(self, value: Container):
        if not isinstance(value, Container): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("value must be a Container")
        self._container = value

app = FastAPI(debug=True)
app.container.AddScoped(type, type)

app.get('/')
def test():
    return 'hi'