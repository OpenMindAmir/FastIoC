# FastIoC

**IoC/DI container for [FastAPI](https://fastapi.tiangolo.com) with automatic type-based dependency injection**

[![PyPI - Version](https://img.shields.io/pypi/v/fastioc?logo=python&logoColor=yellow&label=PyPI&color=darkgreen)](https://pypi.org/project/fastioc/)
[![Documentation](https://img.shields.io/badge/Documentation-blue?style=flat&logo=readthedocs&logoColor=white)](https://openmindamir.github.io/FastIoC)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Support](https://img.shields.io/badge/Support-violet?style=flat&logo=githubsponsors&logoColor=white&labelColor=black)](https://OpenMindAmir.ir/donate)

---

### Why FastIoC 🤔

FastIoC bridges the gap between Python’s dynamic nature and modern dependency injection patterns found in frameworks like .NET, Laravel, Spring Boot, and NestJS — with zero boilerplate and full FastAPI compatibility.


**Features:**

- 🧹 Write cleaner, loosely coupled code while staying true to the ⛓️‍💥 Dependency Inversion Principle (SOLID - D) — with **ABSOLUTELY ZERO** boilerplate! ⚡

- ⚙️ Enjoy hassle-free, automatic nested dependency resolution using Python type hints with flexible lifetimes: ♻️ Singleton, 🧺 Scoped, and ♨️ Transient (inspired by .NET)

- 🚀 Zero runtime overhead — everything is resolved at startup!

- 🤝 100% compatible & based on FastAPI’s native dependency injection — no black boxes, no magic 🪄

- ♻️ Singleton support with automatic cleanup on application shutdown 🧹

- 🧪 Full support for FastAPI's `dependency_overrides` using type annotations — even with mock containers 💉

- 📦 Comes with the amazing **`APIController`** — the best class-based view (CBV) system ever seen in Python 🏆

- 🔄 Two operation modes: **standalone** 🏕️ and **integrated** 🧩

- 🔧 Comes with customizable hooks, detailed logs & ... 📊

## Sponsors 💝

You can  [![Support](https://img.shields.io/badge/Support-violet?style=flat&logo=githubsponsors&logoColor=white&labelColor=black)](https://OpenMindAmir.ir/donate) us on a regular basis to become a sponsor. For more info, contact [OpenMindAmir@gmail.com](mailto:OpenMindAmir@gmailc.com).

## Installation 📥

```bash
$ pip install fastioc
```

## Usage 💡

Sample interface & implementation:

```python
from typing import Protocol

# Define the interfaces 📜

class INumberGenerator(protocol):

    def generate(self) -> int: ...


class IService(Protocol):
    
    def get_number(self) -> int: ...


# Implement concrete classes (Actual dependencies) 🏗️

class SimpleNumberGenerator(INumberGenerator):

    def generate(self) -> int:
        return 42

class ExampleService(IService):

    number_service: INumberGenerator # Nested dependency with type hints! ⚡

    def get_number(self) -> int:
        return self.number_service.generate()
```

### Standalone Mode 🏕️

```python
from fastapi import FastAPI

from fastioc import Container # Import the Container


# Create container and register dependency 📝
container = Container()
container.add_scoped(INumberGenerator, SimpleNumberGenetator)
container.add_scoped(IService, ExampleService) # Also available: add_singleton, add_transient


# Create FastAPI app and integrate it with the container 🪄
app = FastAPI()
container.injectify(app)


# Now your endpoints are injectified! 🎉
@app.get('/')
def index(service: IService) -> int: # Only use the interface - no 'Depends' needed
    return service.get_number() # 42 🤩
```

## APIController 📦

```python
from fastapi import FastAPI

from fastioc import Container
from fastioc.controller import APIController, get, post

# Create container & register dependencies 📝
container = Container()
container.add_scoped(IService, ExampleService)

# Define an example controller
class ExampleController(APIController):
    config = { # APIRouter parameters (+ IDE Autocomplete 🤩)
        "prefix": '/example',
        "tag": 'example',
        "container": container # ! DO NOT FORGET
    }

    service: IService # Available in all endpoints! ⚡

    @get('/read')
    def read_example(self) -> int:
        return self.service.get_number()

    @post('/set')
    def set_example(self) -> bool:
        # ...
        return True

app = FastAPI()
app.include_router(ExampleController.router()) # Get router from controller and include it
```

- APIController endpoints are injectified so you can also resolve dependencies in each endpoint separately.
- You can also resolve dependencies in `__init__` of your controller.
- Read more in the [APIController documentation](https://openmindamir.github.io/FastIoC/controller/)

## Learn More 📘

Check out the [full documentation](https://openmindamir.github.io/FastIoC/) for advanced examples, architecture guides, best practices, and more.

## Contributing 💬

Got an idea, found a bug, or want to improve FastIoC?  
Feel free to open an [issue](https://github.com/OpenMindAmir/FastIoC/issues) or submit a [pull request](https://github.com/OpenMindAmir/FastIoC/pulls) — contributions are always welcome 🤝

## License ⚖️
This project is licensed under the MIT License — see the [LICENSE](LICENSE.md) file for details.