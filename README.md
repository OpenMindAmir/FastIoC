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

Query(...)	پارامترهای query string در URL 
Shane's Personal Blog
+3
FastAPI
+3
FastAPI
+3
Path(...)	پارامترهای مسیر URL (مثلاً {item_id}) 
FastAPI
Body(...)	بدنه‌ی درخواست، معمولاً JSON یا مدل‌های Pydantic 
FastAPI
+1
Header(...)	هدرهای HTTP 
FastAPI
+1
Cookie(...)	کوکی‌ها 
FastAPI
+1
Form(...)	فرم‌های ارسال شده (معمولاً برای application/x-www-form-urlencoded) 
FastAPI
File(...)	فایل‌هایی که از طرف کلاینت ارسال می‌شوند

----

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