from pydantic import BaseModel

class AutocompleteInput(BaseModel):
  query: str
