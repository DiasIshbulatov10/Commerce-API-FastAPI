from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str
    max_top_k: int
    top_k_labels_search: int