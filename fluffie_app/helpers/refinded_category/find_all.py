from typing import Optional

from beanie import PydanticObjectId

from ...models.refined_category import RefinedCategoryModel

def query_list_refined_category(
  currentpage: Optional[int] = None,
  pagesize: int = 10,
  master_category: Optional[str] = None,
):
  builder = RefinedCategoryModel.find().sort(-RefinedCategoryModel.created_at)

  if currentpage is not None:
    builder.skip(pagesize * (currentpage - 1)).limit(pagesize)

  if master_category is not None:
    builder.find({ RefinedCategoryModel.master_category_id: { '$regex': '.*' + master_category + '.*' } })

  return builder

def query_refined_category_by_master_category(master_id: PydanticObjectId):
  return RefinedCategoryModel.find(
    RefinedCategoryModel.master_category_id == str(master_id),
  )
