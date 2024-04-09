from datetime import datetime
from typing import Any, Optional

from beanie import PydanticObjectId, Link
from pydantic import BaseModel, Field

class BaseSchema(BaseModel):
  id: PydanticObjectId = Field(..., alias='_id')
  # id_x: Optional[PydanticObjectId] = Field(None, alias='id')

  # created_at: Optional[Any]
  # updated_at: Optional[Any]
  # created_at: datetime
  # updated_at: datetime

  # class Config:
  #   fields = {
  #     'id': ['_id', 'id']
  #   }

def cast_link_to_id(cls, v):
  if isinstance(v, Link):
    return v.ref.id

  return v

