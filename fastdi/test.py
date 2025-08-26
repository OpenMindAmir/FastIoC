from fastapi import FastAPI, Depends
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
# -------------------------
@app.get("/transient")
def transient(
    n1: Number = Depends(Transient(Number)),
    n2: Number = Depends(Transient(Number))
):
    return {"n1": n1.get(), "n2": n2.get()}

# -------------------------
# Cached → تابع عادی
# -------------------------
@app.get("/cached")
def cached(
    n1: Number = Depends(get_number),
    n2: Number = Depends(get_number)
):
    return {"n1": n1.get(), "n2": n2.get()}

# TODO Remove file