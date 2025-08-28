# from fastapi import FastAPI, Depends
# from fastapi.params import Depends as Dependancy
# import random

# app = FastAPI()

# class Number:
#     def __init__(self):
#         self.value = random.randint(1, 100)
#         print(f"INIT {self.value}")

#     def get(self):
#         return self.value

# def get_number():
#     return Number()

# def Transient(factory):
#     def _inner():
#         return factory()
#     return _inner

# # Use like this => Depends(Transient(Number))

# factory = Dependancy(dependency=Number, use_cache=False)
# scoped = Dependancy(dependency=Number, use_cache=True)
# # -------------------------
# @app.get("/transient")
# def transient(
#     n1: Number = factory,
#     n2: Number = factory
# ):
#     return {"n1": n1.get(), "n2": n2.get()}

# # -------------------------
# # Cached → تابع عادی
# # -------------------------
# @app.get("/cached")
# def cached(
#     n1: Number = scoped,
#     n2: Number = scoped,
# ):
#     return {"n1": n1.get(), "n2": n2.get()}


# # ---

import inspect
from typing import Any, get_type_hints

def override_param(base_cls, method_name: str, **overrides: Any):
    """
    دکوراتور برای بازنویسی تایپ یک یا چند پارامتر
    بدون نیاز به نوشتن کل سینگنیچر دوباره.
    """
    def decorator(func):
        base_method = getattr(base_cls, method_name)
        sig = inspect.signature(base_method)
        hints = get_type_hints(base_method)

        # تغییر تایپ‌ها مطابق ورودی کاربر
        for param, new_type in overrides.items():
            hints[param] = new_type

        # بازسازی __annotations__ برای تابع جدید
        func.__annotations__ = hints
        # همینطور return type
        if "return" in base_method.__annotations__:
            func.__annotations__["return"] = base_method.__annotations__["return"]

        # تزریق سینگنیچر والد روی تابع جدید
        func.__signature__ = sig
        return func
    return decorator


class Base:
    def process(self, name: str, age: int, city: str) -> None:
        ...

class Sub(Base):
    @override_param(Base, "process", name=str | int)
    def process(self, *args, **kwargs):   # فقط یه تابع خالی
        print("called process")


a = Sub()
a.process(name)



# TODO Remove file