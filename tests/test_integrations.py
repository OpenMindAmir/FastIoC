from typing import Any

from fastapi import FastAPI as _FastAPI, Depends
from fastapi.testclient import TestClient

from fastdi.integrations import FastAPI, APIRouter

from .dependencies import State
from .constants import QUERY_TEXT


# --- Application instance test
def test_app(state: State):
    ...