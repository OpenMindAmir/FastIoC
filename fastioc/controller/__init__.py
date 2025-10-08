'''
This module serves as the main public interface for FastIoC's controller system.

It re-exports the core `APIController` base class and all FastIoC-compatible 
route decorators (`get`, `post`, `put`, `patch`, `head`, `options`, `delete`, `trace`, `websocket`) 
to provide a clean and unified import path for building dependency-injected FastAPI controllers.

By using these exports, developers can easily define fully type-hinted, dependency-injected 
controllers that integrate seamlessly with FastAPI's routing system while leveraging 
FastIoC's inversion of control (IoC) container.

Example:
--------
```python
from fastioc.controller import APIController, get
from my_app.interfaces import IUserService, ILoggingService

class UserController(APIController):
    config = {
        "prefix": "/users",
        "container": app_container
    }

    logger: ILoggingService

    @get("/")
    def list_users(self, service: IUserService):
        self.logger.log('get users')
        return service.get_all()

router = UserController.router()
app.include_router(router)
```

This module is intended to be the primary import surface for most applications
using FastIoC's controller architecture.
'''

from fastioc.controller.controller import APIController
from fastioc.controller.definitions import get, post, put, patch, head, options, delete, trace, websocket

__all__ = [
    'APIController',
    'get',
    'post',
    'put',
    'patch',
    'head',
    'options',
    'delete',
    'trace',
    'websocket',
]