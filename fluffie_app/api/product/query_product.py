from typing import Optional
from uuid import uuid4
import time

from fastapi import Query
import ujson

from ...middleware.custom_response import PagingResponse
from ...helpers.product_category.query_vector import query_product_by_vector, get_query_product_data
from ...jobs.cache_query_product import background_query_product
from ...db.redis import redis_async_conn
from ...core.exceptions import NotFoundItem
from fluffie_app.core.logger import logger


from .route import router

@router.get(
  '/search_test',
  response_model=PagingResponse,
)
async def search_product_with_pinecone(
  query: str,
  # limit: Optional[int] = Query(500),
  brand: Optional[list[str]] = Query(None),
  master_category: Optional[list[str]] = Query(None),
  refined_category: Optional[list[str]] = Query(None),
  max_price: Optional[float] = Query(None, ge=0),
  min_price: Optional[float] = Query(None, ge=0),
  page: int = Query(1, ge=1),
  query_id: Optional[str] = Query(None)
):
  cache_id = query_id
  limit = 20
  start_time = time.time()

  if cache_id is None:
    cache_id = str(uuid4())

    query_data = get_query_product_data(query)
    logger.warning("--- get_query_product_data takes %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    if brand:
      query_data['filter_criteria']['brand'] = brand

    if master_category:
      query_data['filter_criteria']['master_category'] = master_category

    if refined_category:
      query_data['filter_criteria']['refined_category'] = refined_category

    if max_price or min_price:
      query_data['filter_criteria']['price'] = (min_price, max_price)

    prod_ids, results = None, None
    
    async for prod_ids, results in query_product_by_vector(query_data, limit):
      pass
    logger.warning("--- query_product_by_vector takes %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    background_query_product.delay(query_data, list(prod_ids), cache_id)

  else:
    raw_data = await redis_async_conn.get(f'query_product_cache/{cache_id}')

    if raw_data is None:
      raise NotFoundItem('Not found cache')

    cached_data = ujson.loads(raw_data)

    results = cached_data[(page-2)*limit: (page-1)*limit]

  return PagingResponse(
    data=results,
    query_id=cache_id,
    # count=count,
    page=page,
    limit=limit,
    # pages=ceil(count / limit)
  )
