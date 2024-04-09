from typing import Optional
from math import ceil

from fastapi import Query

from .route import router
from ...models.review import ReviewModel
from ...middleware.custom_response import build_paging_return, PagingResponse

@router.get('/', response_model=PagingResponse)
async def get_review_aggr(
  page: int = Query(1),
  pagesize: int = Query(10),
):
  count = await ReviewModel.count()

  results = await ReviewModel.aggregate(
    [
      {
        '$lookup': {
          'from': "labels",
          'localField': "labels.label",
          'foreignField': "id",
          'as': "labels",
        },
      },
      { '$skip': pagesize * (page - 1) },
      { '$limit': pagesize }
    ],
    allowDiskUse=True
  ).to_list()

  return PagingResponse(
    data=results,
    count=count,
    page=page,
    limit=pagesize,
    pages=ceil(count / pagesize),
  )
