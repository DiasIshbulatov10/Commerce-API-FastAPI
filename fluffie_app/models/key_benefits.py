from .base import BaseModel

class BenefitModel(BaseModel):
  benefit: str

  class Settings:
    name = 'benefits'
