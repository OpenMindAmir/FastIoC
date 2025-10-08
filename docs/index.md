# FastIoC

**IoC/DI container for [FastAPI](https://fastapi.tiangolo.com) with automatic type-based dependency injection**

[![PyPI - Version](https://img.shields.io/pypi/v/fastioc?logo=python&logoColor=yellow&label=PyPI&color=darkgreen)](https://pypi.org/project/fastioc/)
[![Documentation](https://img.shields.io/badge/Documentation-blue?style=flat&logo=readthedocs&logoColor=white)](https://openmindamir.github.io/FastIoC)
[![Support](https://img.shields.io/badge/Support-violet?style=flat&logo=githubsponsors&logoColor=white&labelColor=black)](https://OpenMindAmir.ir/donate)

---

**Features:**

- 🧹 Write cleaner, loosely coupled code while staying true to the ⛓️‍💥 Dependency Inversion Principle (SOLID - D) — with **ABSOLUTELY ZERO** boilerplate! ⚡

- ⚙️ Enjoy hassle-free, automatic nested dependency resolution using Python type hints with flexible lifetimes: ♻️ Singleton, 🧺 Scoped, and ♨️ Transient (inspired by .NET)

- 🚀 Zero runtime overhead — everything is resolved at startup!

- 🤝 100% compatible & based on FastAPI’s native dependency injection — no black boxes, no magic 🪄

- ♻️ Singleton support with automatic cleanup on application shutdown 🧹

- 🧪 Full support for FastAPI's `dependency_overrides` using type annotations — even with mock containers 💉

- 📦 Comes with the amazing **`APIController`** — the best class-based view (CBV) system ever seen in Python 🏆

- 🔄 Two operation modes: standalone 🏕️ and integrated 🧩

- 🔧 Comes with customizable hooks, detailed logs & ... 📊