from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from beanie import Document, PydanticObjectId, Link
from pydantic import Field
from pydantic.json import ENCODERS_BY_TYPE

# fix beanie convert in line .venv/Lib/site-packages/beanie/odm/fields.py:215
ENCODERS_BY_TYPE[Link] = lambda v: str(v.ref.id)
ENCODERS_BY_TYPE[ObjectId] = lambda v: str(v)

class BaseModel(Document):
  '''
    other id
  '''
  # id_x: Optional[str] = Field(alias='id')

  # created_at: Optional[Any]
  # updated_at: Optional[Any]
  # created_at: datetime = Field(default_factory=datetime.utcnow)
  # updated_at: datetime = Field(default_factory=datetime.utcnow)

def cast_string_to_id(cls, v):
  if isinstance(v, str):
    if len(v) == 0: return None

    return PydanticObjectId(v)

  return v

