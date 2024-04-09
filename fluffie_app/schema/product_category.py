from typing import Optional

from pydantic import BaseModel as PydaBaseModel

from .base import BaseModel

class ProductCategorySchema(BaseModel):
  product_category: Optional[str]

class CategoryWithProductBody(PydaBaseModel):
  category: list[str]
