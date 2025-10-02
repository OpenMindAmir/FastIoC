"""
FastIoC: IoC/DI container for FastAPI with automatic type-based dependency injection.

FastIoC allows you to register dependencies with different lifetimes
(Singleton, Scoped, Factory) and automatically inject them into FastAPI
endpoints and route-level dependencies based on type hints.
It simplifies dependency management and promotes clean, modular code.
"""

from fastioc.container import Container
from fastioc.integrations import FastAPI, APIRouter
from fastioc.controller import APIController
from fastioc.controller import get, post, delete, put, patch, options, head, trace, websocket  # pyright: ignore[reportMissingTypeStubs]

__all__ = [
    'Container',
    'FastAPI',
    'APIRouter',
    'APIController',
    'get',
    'post',
    'delete',
    'put',
    'patch',
    'options',
    'head',
    'trace',
    'websocket'
]