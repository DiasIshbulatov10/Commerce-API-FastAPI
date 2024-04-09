from asyncio import gather
from bson import ObjectId
from typing import Optional

from fastapi import Body

from .route import router
from ...core.exceptions import NotFoundItem
from ...models.search_query import SearchQueryModel
from ...schema.autocomplete import AutocompleteInput

@router.post(
  '/autocomplete',
  response_model=list[str],
  responses=dict(
    (NotFoundItem.openapi_schema,),
  ),
)
async def get_search_queries(
  input: AutocompleteInput = Body()

):
    results = await SearchQueryModel.aggregate(
        [
            {
                "$search": {
                    "index": "search_queries_autocomplete",
                    "autocomplete": {
                        "query": input.query,
                        "path": "search_query"
                    }
                }
            },
            {"$limit": 5},
            {"$project": {"_id": 0, "search_query": 1}}
        ]
    ).to_list()

    return [result["search_query"] for result in results if result["search_query"]]
