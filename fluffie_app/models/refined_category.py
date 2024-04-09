from typing import Optional

from beanie import Link
from pydantic import validator

from .base import BaseModel, cast_string_to_id
from .master_categories import MasterCategoryModel

class RefinedCategoryModel(BaseModel):
  refined_category: str
  master_category_id: Optional[Link[MasterCategoryModel]]

  class Settings:
    name = 'refined_categories'

  _cast_id = validator('master_category_id', pre=True, allow_reuse=True)(cast_string_to_id)
