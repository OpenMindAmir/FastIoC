# from typing import Any
# from fastapi import FastAPI as _FastAPI, APIRouter as _APIRouter
# from fastdi import Container
# from fastdi.utils import pretendSignatureOf

# class FastAPI(_FastAPI):

#     container: Container

#     @pretendSignatureOf(_FastAPI.__init__)
#     def __init__(self, *args: Any, container: Container = Container(), **kwargs: Any):
#         super().__init__(*args, **kwargs)
#         self.container = container


# a = FastAPI()

# a.container = 
