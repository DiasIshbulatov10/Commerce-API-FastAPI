from .base import BaseModel

class LabelModel(BaseModel):
  label: str
  category: str
  displaylabel: str

  class Settings:
    name = 'labels'
