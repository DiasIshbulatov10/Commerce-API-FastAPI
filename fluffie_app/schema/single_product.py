from pydantic import BaseModel
from beanie import PydanticObjectId

class ProductInput(BaseModel):
  title: str
  slug: str
  prod_link: str
  price: float
  img: str
  details: str
  usage: str
  category: list[PydanticObjectId]
  brand: PydanticObjectId
  refined_category: PydanticObjectId
  key_benefits: list[PydanticObjectId]
  ingredient: str
  prod_claims: list[PydanticObjectId]
