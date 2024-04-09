from fastapi import Body

from .route import router
from ...models.review import ReviewModel
from ...models.single_product import ProductModel
from ...schema.review import ReviewInput
from ...core.exceptions import NotFoundItem

@router.post(
  '/{productId}',
  response_model=ReviewModel,
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def create_review(productId: str, input: ReviewInput = Body(...)):
  product = await ProductModel.get(productId)

  if product is None:
    raise NotFoundItem('Product not found')

  review = ReviewModel(
    prod_id=productId,
    **input.dict(),
  )

  return await review.save()
