from bson import ObjectId

from .route import router
from ...models.review import ReviewModel
from ...core.exceptions import NotFoundItem

@router.delete(
  '/{id}',
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def delete_review(id: str):
  result = await ReviewModel.get(id)

  if result is None:
    raise NotFoundItem()

  await result.delete()

  return result
