from typing import Optional
from asyncio import gather

from fastapi import Query

from .route import router
from ...schema.master_categories import MasterAndRefinedCategory
from ...helpers.master_categories.find_all import query_list_master_categories
from ...helpers.refinded_category.find_all import query_refined_category_by_master_category

@router.get('/', response_model=list[MasterAndRefinedCategory])
async def get_master_category(currentpage: Optional[int] = Query(None), pagesize: int = Query(10)):
  builder = query_list_master_categories(currentpage, pagesize)

  list_master_cate = await builder.to_list()

  results = await gather(*map(_fetch_refined_category, list_master_cate))

  return results

async def _fetch_refined_category(master_cate):
  m_cate = master_cate.dict(by_alias=True)

  m_cate['refind_category'] = await query_refined_category_by_master_category(master_cate.id).to_list()

  return m_cate
