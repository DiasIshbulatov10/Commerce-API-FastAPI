from fastapi import Body

from .route import router
from ...models.single_product import ProductModel
from ...schema.single_product import ProductInput

@router.post(
  '/',
  response_model=ProductModel,
)
async def create_product(input: ProductInput = Body(...)):
  product = ProductModel(
    **input.dict(),
  )

  return await product.save()
