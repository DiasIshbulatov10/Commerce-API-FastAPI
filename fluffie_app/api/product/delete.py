from bson import ObjectId

from .route import router
from ...models.single_product import ProductModel
from ...core.exceptions import NotFoundItem

@router.delete(
  '/{id}',
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def delete_product(id: str):
  result = await ProductModel.get(id)

  if result is None:
    raise NotFoundItem()

  await result.delete()

  return result
