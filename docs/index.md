# FastIoC

**IoC/DI container for [FastAPI](https://fastapi.tiangolo.com) with automatic type-based dependency injection**

[![PyPI - Version](https://img.shields.io/pypi/v/fastioc?logo=python&logoColor=yellow&label=PyPI&color=darkgreen)](https://pypi.org/project/fastioc/)
[![Documentation](https://img.shields.io/badge/Documentation-blue?style=flat&logo=readthedocs&logoColor=white)](https://openmindamir.github.io/FastIoC)
[![Support](https://img.shields.io/badge/Support-violet?style=flat&logo=githubsponsors&logoColor=white&labelColor=black)](https://OpenMindAmir.ir/donate)

---

**Features:**

- Write cleaner, loosely coupled code while staying true to the **Dependency Inversion Principle (SOLID - D)**
- Enjoy hassle-free, automatic nested dependency resolution using Python type hints with flexible lifetimes: **Singleton**, **Scoped**, and **Transient** (inspired by .NET)
- **Zero runtime overhead** — everything is resolved at startup
- 100% compatible & based on FastAPI’s native dependency injection — no black boxes, no magic, **no boilerplate**
- Singleton support with automatic cleanup on application shutdown
- Full support for FastAPI's `dependency_overrides` using type annotations — even with mock containers
- Two operation modes: **standalone** and **integrated**
- Open standard and fully customizable, with hooks and standardized error handling
- Detailed multi-level logging