from beanie import Link

from .base import BaseModel
from .product_category import ProductCategoryModel
from .brand import BrandModel
from .refined_category import RefinedCategoryModel
from .key_benefits import BenefitModel
from .label import LabelModel

class ProductModel(BaseModel):
  title: str
  slug: str
  prod_link: str
  price: float
  img: str
  details: str
  usage: str
  category: list[Link[ProductCategoryModel]]
  brand: Link[BrandModel]
  refined_category: Link[RefinedCategoryModel]
  key_benefits: list[Link[BenefitModel]]
  ingredient: str
  prod_claims: list[Link[LabelModel]]


  class Settings:
    name = 'products'
