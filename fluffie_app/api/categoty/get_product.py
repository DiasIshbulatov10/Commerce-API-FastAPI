from typing import Optional

from fastapi import Query
from beanie import operators
from bson import ObjectId

from .route import router
from ...core.exceptions import NotFoundItem
from ...models.product_category import ProductCategoryModel
from ...models.single_product import ProductModel
from ...schema.product_category import CategoryWithProductBody

@router.get(
  '/product/{id}',
  summary='get product by category id',
  response_model=ProductModel,
  responses=dict(
    (NotFoundItem.openapi_schema,),
  )
)
async def get_category_with_product_1(id: str):
  category = await ProductCategoryModel.get(id)

  result = await _get_product_by_category(category)

  return result

@router.get('/product')
async def get_category_with_product_2(category: str = Query()):
  category = await ProductCategoryModel.get(category)

  result = await _get_product_by_category(category)

  return result

@router.post('/product')
async def get_category_with_product_3(body: CategoryWithProductBody):
  category = await ProductCategoryModel.find_one(
    operators.In(ProductCategoryModel.id, tuple(map(ObjectId, body.category)))
  )

  result = await _get_product_by_category(category)

  return result

async def _get_product_by_category(category: Optional[ProductCategoryModel]):
  if category is None:
    raise NotFoundItem()

  product = await ProductModel.find_one(ProductModel.category == str(category.id))

  if product is None:
    raise NotFoundItem()

  return product
