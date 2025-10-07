"""
FastIoC: IoC/DI container for FastAPI with automatic type-based dependency injection.

FastIoC allows you to register dependencies with different lifetimes
(Singleton, Scoped, Factory) and automatically inject them into FastAPI
endpoints and route-level dependencies based on type hints.
It simplifies dependency management and promotes clean, modular code.
"""

from fastioc.container import Container
from fastioc.integrations import FastAPI, APIRouter
from fastioc.controller.controller import APIController
from fastioc.controller.definitions import *

class Actions:
    get = get
    post = post
    put = put
    patch = patch
    delete = delete
    head = head
    options = options
    trace = trace
    websocket = websocket

    __all__ = [
        'get',
        'post',
        'put',
        'patch',
        'delete',
        'head',
        'options',
        'trace',
        'websocket',
    ]


__all__ = [
    'Container',
    'FastAPI',
    'APIRouter',
    'APIController',
    'Actions'
]