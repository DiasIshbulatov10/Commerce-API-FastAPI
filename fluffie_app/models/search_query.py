from .base import BaseModel

class SearchQueryModel(BaseModel):
    search_query: str

    class Settings:
        name = 'search_queries'
