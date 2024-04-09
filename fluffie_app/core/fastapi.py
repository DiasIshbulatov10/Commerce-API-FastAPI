from functools import partial
from subprocess import call
from threading import Thread
import os
from dotenv import load_dotenv

from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .openapi import custom_openapi
from ..db.mongo import init_mongo
from ..api.route import api_router
from .config import settings

app = FastAPI(
  title='Product api',
  default_response_class=UJSONResponse,
)

load_dotenv()


app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_, exc: StarletteHTTPException):
    return JSONResponse(
      {
        'status': False,
        'message': exc.detail,
        'type': exc.__class__.__name__,
        'errors': getattr(exc, 'data', None)
      },
      status_code=exc.status_code
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
      {
        'status': False,
        'message': 'Validation error',
        'type': exc.__class__.__name__,
        'errors': exc.errors()
      },
      status_code=422
    )

app.include_router(api_router)

worker_thread = Thread(
  target=call,
  # args=(f'rq worker normal -u {settings.redis_uri}',),
  args=('python -m fluffie_app.services.queue_job.workers',),
  kwargs={'shell': True, 'env': os.environ}
)

@app.on_event("startup")
async def startup():
  worker_thread.start()
  app.mongodb_client = MongoClient(os.getenv("MONGO_URI"))
  app.database = app.mongodb_client['app_db']

  await init_mongo()

@app.on_event("shutdown")
async def shutdown():
  # worker.stop_scheduler()
  worker_thread.join()
  app.mongodb_client.close()

app.openapi = partial(custom_openapi, app)