from pydantic import BaseModel
from beanie import PydanticObjectId

from typing import Optional

class RegisterSchema(BaseModel):
  phone_number: int
  first_name: str
  date_of_birth: str
  password: str
  gender: Optional[str]


class UserInLogin(BaseModel):
  phone_number: int
  password: str
