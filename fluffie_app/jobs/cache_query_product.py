import asyncio
from datetime import datetime

import ujson
from fastapi.encoders import jsonable_encoder

from ..core.logger import logger
from ..db.redis import redis_async_conn
from ..services.queue_job.queues import queue_celery
from ..helpers.product_category.query_vector import query_product_by_vector, QueueProductData

# @job(normal_queue)
@queue_celery.task
def background_query_product(search_data: QueueProductData, exclude_products, cache_id):
  return asyncio.run(_run_task(search_data, exclude_products, cache_id))

async def _run_task(search_data: QueueProductData, exclude_products, cache_id):
  now = datetime.now()
  first_data = None
  async for _, results in query_product_by_vector(search_data, 1000, exclude_products=exclude_products):
    if first_data is None:
      first_data = datetime.now() - now
      logger.info(f'Time to yield first data {first_data}')

    await redis_async_conn.set(f'query_product_cache/{cache_id}', ujson.dumps(jsonable_encoder(results)), ex=1800)

  # logger.info(f'Job complete in {datetime.now() - now}')

  return 'ok'
