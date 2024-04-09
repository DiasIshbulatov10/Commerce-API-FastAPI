from .base import BaseModel

class BrandModel(BaseModel):
  brand: str

  class Settings:
    name = 'brands'
