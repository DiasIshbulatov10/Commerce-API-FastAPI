from pydantic import BaseModel as PyDaBaseModel
from beanie import Link

from .base import BaseModel
from .label import LabelModel

class _ReviewLabel(PyDaBaseModel):
  part: str
  label: str
  # label: Link[LabelModel]

class _LabelM(PyDaBaseModel):
  label: _ReviewLabel

class ReviewModel(BaseModel):
  review_id: str
  prod_id: str
  title: str
  name: str
  age: list[int]
  desc: str
  rating: int
  country: str
  sentiment: bool
  labels: list[_ReviewLabel]

  class Settings:
    name = 'reviews'
