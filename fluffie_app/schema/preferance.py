from pydantic import BaseModel
from beanie import PydanticObjectId
from typing import Optional

class PreferanceSchema(BaseModel):
  phone_number: int
  sensitive_skin: str
  skin_type: str
  skin_concerns: list[str]
  skincare_price_range_preference: list[int]
  skin_tone: str
  skincare_product_preferences: str
  skincare_insights: Optional[str]
