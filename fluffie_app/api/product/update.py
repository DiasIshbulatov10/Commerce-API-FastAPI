from datetime import datetime

from fastapi import Body

from .route import router
from ...models.single_product import ProductModel
from ...schema.single_product import ProductInput
from ...core.exceptions import NotFoundItem

@router.put(
  '/{id}',
  response_model=ProductModel,
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def update_product(id: str, input: ProductInput = Body(...)):
  result = await ProductModel.get(id)

  if result is None:
    raise NotFoundItem()

  set = input.dict()
  # set['updated_at'] = datetime.utcnow()

  await result.update({
    '$set': set
  })

  return result

