"""
FastIoC: IoC/DI container for FastAPI with automatic type-based dependency injection.

FastIoC allows you to register dependencies with different lifetimes
(Singleton, Scoped, Factory) and automatically inject them into FastAPI
endpoints and route-level dependencies based on type hints.
It simplifies dependency management and promotes clean, modular code.
"""

from fastioc.container import Container  # pyright: ignore[reportUnusedImport]
from fastioc.integrations import FastAPI, APIRouter  # pyright: ignore[reportUnusedImport]
