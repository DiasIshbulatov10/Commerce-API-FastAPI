from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.constants import REF_PREFIX

def custom_openapi(app: FastAPI):
  if app.openapi_schema:
    return app.openapi_schema

  openapi_schema = get_openapi(
    title=app.title,
    version=app.version,
    description=app.description,
    routes=app.routes,
  )

  openapi_schema['servers'] = [
    {
      'url': "",
      'description': "Current server",
    },
    {
      'url': "http://ec2-52-193-219-106.ap-northeast-1.compute.amazonaws.com:5001",
      'description': "live server",
    },
  ]

  openapi_schema['components']['schemas']['HTTPValidationError'] = {
    "title": "HTTPValidationError",
    "type": "object",
    "properties": {
      'status': { 'type': 'boolean', 'defaule': False },
      'message': { 'type': 'string' },
      'type': { 'type': 'string', 'defaule': 'HTTPValidationError' },
      'errors': {
        "title": "Detail",
        "type": "array",
        "items": {"$ref": REF_PREFIX + "ValidationError"},
      },
    },
  }

  app.openapi_schema = openapi_schema
  return openapi_schema
