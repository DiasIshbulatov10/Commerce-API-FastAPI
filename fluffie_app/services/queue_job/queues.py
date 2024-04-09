from celery import Celery

from ...core.config import settings

queue_celery = Celery('normal', broker=settings.redis_uri)
