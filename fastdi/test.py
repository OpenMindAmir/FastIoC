from fastapi import FastAPI, Depends
from fastapi.params import Depends as Dependancy
import random

app = FastAPI()

class Number:
    def __init__(self):
        self.value = random.randint(1, 100)
        print(f"INIT {self.value}")

    def get(self):
        return self.value

def get_number():
    return Number()

def Transient(factory):
    def _inner():
        return factory()
    return _inner

# Use like this => Depends(Transient(Number))

factory = Dependancy(dependency=Number, use_cache=False)
scoped = Dependancy(dependency=Number, use_cache=True)
# -------------------------
@app.get("/transient")
def transient(
    n1: Number = factory,
    n2: Number = factory
):
    return {"n1": n1.get(), "n2": n2.get()}

# -------------------------
# Cached → تابع عادی
# -------------------------
@app.get("/cached")
def cached(
    n1: Number = scoped,
    n2: Number = scoped,
):
    return {"n1": n1.get(), "n2": n2.get()}


# ---


# TODO Remove file