from typing import TYPE_CHECKING
from .base import BaseSchema
from .refined_category import RefinedCategory

class MasterCategory(BaseSchema):
  master_category: str

class MasterAndRefinedCategory(MasterCategory):
  refind_category: list[RefinedCategory]
