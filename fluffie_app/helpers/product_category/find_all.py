from typing import Optional

from ...models.product_category import ProductCategoryModel

def query_list_product_categories(
  currentpage: Optional[int] = None,
  pagesize: int = 10,
  title: Optional[str] = None,
):
  builder = ProductCategoryModel.find().sort(-ProductCategoryModel.created_at)

  if currentpage is not None:
    builder.skip(pagesize * (currentpage - 1)).limit(pagesize)

  if title is not None:
    builder.find({ ProductCategoryModel.product_category: { '$regex': '.*' + title + '.*' } })

  return builder
