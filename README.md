note to user lists are not thread safe be on alert when you are using them in singleton and multiple threeads
note last class will be used for interface
options pattern note in description

r&d multiprocessing.Manager

inject fastapi dependencies (like Request, ...) in type hints => Continue
وابستگی‌های امنیت (Security)

FastAPI ابزارهای خاص Security دارد که خودشان وابستگی‌اند یا برای تزریق داده‌های امنیتی، کاربر فعلی و احراز هویت کاربرد دارند:

fastapi.security شامل موارد زیر است: 
FastAPI

APIKeyHeader

APIKeyQuery

APIKeyCookie

HTTPBasic / HTTPBasicCredentials

HTTPBearer / HTTPAuthorizationCredentials

OAuth2 / OAuth2PasswordBearer

OAuth2AuthorizationCodeBearer

OAuth2PasswordRequestForm

OAuth2PasswordRequestFormStrict

OpenIdConnect

SecurityScopes 


علاوه بر این، Security() (که شبیه Depends() است اما برای ابزار امنیتی با قابلیت تعریف scope) 
FastAPI
+1

Request — برای دریافت کل درخواست HTTP و دسترسی به headers, body, cookies, etc. 
Escape
+1

Response — اگر بخوای پاسخ رو دستکاری کنی یا headerهایش تغییر بدی، یا پاسخ سفارشی بسازی 
FastAPI

HTTPException — برای پرتاب خطاهای HTTP در dependency یا خود endpoint 
FastAPI
+1

BackgroundTasks — امکان انجام کار پس‌زمینه برای هر درخواست 
FastAPI
+1

فایل‌ها (UploadFile) — وقتی endpoint بخواد فایلی دریافت کند، تزریق UploadFile یا File(...)

----

rename container & may be add factory

Interface
FastAPIController (see fastapi-controller)
Mediator
FastAPIEnterprize
correct names for generator (openapisimplification) see fastapi utils
Pascalcase





---------------------------


def resolve_forward_refs(annotation, globalns, localns):
    from typing import get_origin, get_args, Annotated, ForwardRef
    
    origin = get_origin(annotation)
    
    if origin is Annotated:
        base, *extras = get_args(annotation)
        resolved_base = resolve_forward_refs(base, globalns, localns)
        return Annotated[resolved_base, *extras]

    if origin is not None:  # Generic
        args = get_args(annotation)
        resolved_args = tuple(resolve_forward_refs(a, globalns, localns) for a in args)
        return origin[resolved_args]

    if isinstance(annotation, str):  # simple forward ref
        return ForwardRef(annotation)._evaluate(globalns, localns)

    return annotation
----
import sys
cls = Service
globalns = vars(sys.modules[cls.__module__])
localns = {}
localns = dict(vars(cls))