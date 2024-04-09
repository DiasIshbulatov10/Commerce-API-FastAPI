from typing import Optional

from ...models.master_categories import MasterCategoryModel

def query_list_master_categories(
  currentpage: Optional[int] = None,
  pagesize: int = 10,
):
  builder = MasterCategoryModel.find().sort(-MasterCategoryModel.created_at)

  if currentpage is not None:
    builder.skip(pagesize * (currentpage - 1)).limit(pagesize)

  return builder
