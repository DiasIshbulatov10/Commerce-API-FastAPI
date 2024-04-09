from typing import Optional
from math import ceil

from fastapi import Query

from .route import router
from ...helpers.product_category.find_all import query_list_product_categories
from ...models.product_category import ProductCategoryModel
from ...middleware.custom_response import build_paging_return, PagingResponse

@router.get('/', response_model=build_paging_return(ProductCategoryModel))
async def get_product_category(
  page: Optional[int] = Query(None),
  pagesize: int = Query(10),
  title: Optional[str] = Query(None),
):
  builder = query_list_product_categories(page, pagesize, title)

  results = await builder.to_list()

  if page is None:
    return results

  count = await builder.count()

  return PagingResponse(
    data=results,
    count=count,
    page=page,
    limit=pagesize,
    pages=ceil(count / pagesize)
  )
