from .base import BaseModel

from typing import Optional

class RegisterModel(BaseModel):
  phone_number: int
  first_name: str
  date_of_birth: str
  password: str
  gender: Optional[str]

  class Settings:
    name = 'registers'
