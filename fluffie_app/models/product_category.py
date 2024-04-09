from .base import BaseModel

class ProductCategoryModel(BaseModel):
  product_category: str

  class Settings:
    name = 'product_categories'
