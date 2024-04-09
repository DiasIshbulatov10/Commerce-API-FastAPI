from .base import BaseModel

class MasterCategoryModel(BaseModel):
  master_category: str

  class Settings:
    name = 'master_categories'
