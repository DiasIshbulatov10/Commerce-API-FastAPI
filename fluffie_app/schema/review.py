from pydantic import BaseModel

from ..models.review import _ReviewLabel

class ReviewInput(BaseModel):
  review_id: str
  title: str
  name: str
  age: list[int]
  desc: str
  rating: int
  country: str
  sentiment: bool
  labels: list[_ReviewLabel]
