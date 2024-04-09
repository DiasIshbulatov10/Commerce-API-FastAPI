from typing import Optional

from beanie import PydanticObjectId
from pydantic import validator

from .base import BaseSchema, cast_link_to_id

class RefinedCategory(BaseSchema):
  refined_category: str
  master_category_id: Optional[PydanticObjectId]

  _cast_id = validator('master_category_id', pre=True, allow_reuse=True)(cast_link_to_id)
