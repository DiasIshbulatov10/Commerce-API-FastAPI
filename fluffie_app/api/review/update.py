from datetime import datetime

from fastapi import Body

from .route import router
from ...models.review import ReviewModel
from ...core.exceptions import NotFoundItem
from ...schema.review import ReviewInput

@router.put(
  '/{id}',
  response_model=ReviewModel,
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def update_review(id: str, input: ReviewInput = Body(...)):
  result = await ReviewModel.get(id)

  if result is None:
    raise NotFoundItem()

  set = input.dict()
  # set['updated_at'] = datetime.utcnow()

  await result.update({
    '$set': set
  })

  return result

