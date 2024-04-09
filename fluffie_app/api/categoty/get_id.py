
from .route import router
from ...core.exceptions import NotFoundItem
from ...models.product_category import ProductCategoryModel

@router.get(
  '/{id}',
  response_model=ProductCategoryModel,
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def get_product_category_by_id(id: str):
  result = await ProductCategoryModel.get(id)

  if result is None:
    raise NotFoundItem()

  return result
