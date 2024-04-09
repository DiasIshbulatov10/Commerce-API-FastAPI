from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel

class ErrorSchema(BaseModel):
  status: bool = False
  type: str
  message: str
  errors: Optional[dict] = None


class CustomApiException(HTTPException):
  def __init__(
    self,
    status_code: int,
    detail: Any = None,
    data: Optional[Any] = None,
    headers: Optional[dict[str, Any]] = None
  ) -> None:
    super().__init__(status_code, detail, headers)

    self.data = data

class NotFoundItem(CustomApiException):
  openapi_schema = (
    404,
    {
      'model': ErrorSchema,
      'description': 'NotFoundItem'
    }
  )

  def __init__(
    self,
    detail: Any = None,
    data: Optional[Any] = None,
    headers: Optional[dict[str, Any]] = None
  ) -> None:
    super().__init__(404, detail, data, headers)
