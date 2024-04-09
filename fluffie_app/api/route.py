from fastapi import APIRouter

from . import master_category
from . import refinded_category
from . import categoty
from . import review
from . import product
from . import filters
from . import search_queries
from . import user

api_router = APIRouter()

api_router.include_router(master_category.router, prefix="/master_categories", tags=["master categories"])

api_router.include_router(refinded_category.router, prefix="/refind_categories", tags=["refind categories"])

api_router.include_router(product.router, prefix="/products", tags=["products"])

api_router.include_router(review.router, prefix="/review", tags=["review"])

api_router.include_router(categoty.router, prefix="/categories", tags=["categories"])

api_router.include_router(filters.router, prefix="/filters", tags=["filters"])

api_router.include_router(search_queries.router, prefix="/search_queries", tags=["filters"])

api_router.include_router(user.router, prefix="/user", tags=["user"])