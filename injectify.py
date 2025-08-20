from typing import Any
import inspect

from fastapi import Depends, FastAPI
from typeguard import typechecked

from errors import InterfaceNotRegistered
from custom_types import FastAPIDependable
from container import Container

def inject(_list: list[Any], item: Any, container: Container):
    if isinstance(item, Depends): # type: ignore[assignment]
        _list.append(item)
        return

    try:
        dependable: FastAPIDependable = container.Resolve(item)
        _list.append(Depends(dependable))

    except InterfaceNotRegistered:
        _list.append(item)
    

@typechecked
def Injectify(app: FastAPI, container: Container):

    # --- Endpoint Level Dependencies ---

    for route in getattr(app, 'routes', []):
        if hasattr(route, 'endpoint'):
            endpoint = route.endpoint
            signature = inspect.signature(endpoint)
            params: list[inspect.Parameter] = []

            for name, param in signature.parameters.items(): # type: ignore[unused]
                if isinstance(param.default, Depends):  # type: ignore[assignment]
                    params.append(param)
                    continue

                try:
                    dependable: FastAPIDependable = container.Resolve(param.annotation)
                    newParam = param.replace(default=Depends(dependable))
                    params.append(newParam)

                except InterfaceNotRegistered:
                    params.append(param)

            route.endpoint.__signature__ = signature.replace(parameters=params)
        
        if hasattr(route, 'dependencies'):
            dependencies: list[Any] = []
            
            for dependancy in getattr(route, 'dependencies', []):
                inject(dependencies, dependancy, container)

            route.dependencies = dependencies


    # --- Router Level Dependencies ---

    for router in getattr(app, 'routers', []):
        dependencies: list[Any] = []

        for dependency in getattr(router, 'dependencies', []):
            inject(dependencies, dependency, container)

        router.dependencies = dependencies

    # --- Application Level Dependencies ---
    dependencies: list[Any] = []
    for dependency in getattr(app, 'dependencies', []):
        inject(dependencies, dependency, container)

    app.dependencies = dependencies # type: ignore[attr-defined]