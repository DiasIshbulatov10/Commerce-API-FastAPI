from .base import BaseModel
from typing import Optional

class PreferanceModel(BaseModel):
  phone_number: int
  sensitive_skin: str
  skin_type: str
  skin_concerns: list[str]
  skincare_price_range_preference: list[int]
  skin_tone: str
  skincare_product_preferences: str
  skincare_insights: Optional[str]

  class Settings:
    name = 'preferances'
