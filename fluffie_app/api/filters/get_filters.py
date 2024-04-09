from asyncio import gather

from ...config.brand import BRANDS
from .route import router
from ...models.brand import BrandModel
from ..master_category.get_all import get_master_category

@router.get(
  '/',
  # response_model=ProductModel,
)
async def get_filters_data():
  master_category, brands = await gather(
    get_master_category(None, None),
    BrandModel.all().to_list()
  )

  return {
    'brands': brands,
    'master_category': master_category,
    "price_range": [0, 1000],
  }

