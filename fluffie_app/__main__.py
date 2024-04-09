from .core.fastapi import app
from .core.config import settings

if __name__ == '__main__':
  from uvicorn import run

  run(app, port=settings.port)

