from typing import Optional
from fastapi import Query

from .route import router
from ...helpers.refinded_category.find_all import query_list_refined_category
from ...models.refined_category import RefinedCategoryModel

@router.get('/', response_model=list[RefinedCategoryModel])
async def get_refined_category(
  currentpage: Optional[int] = Query(None),
  pagesize: int = Query(10),
  master_category: Optional[str] = Query(None),
):
  builder = query_list_refined_category(currentpage, pagesize, master_category)

  results = await builder.to_list()

  # results = []
  # async for refind in builder:
  #   json = refind.dict()

  #   results.append(json)

  return results
