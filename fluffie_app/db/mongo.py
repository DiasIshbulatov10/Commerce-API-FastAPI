from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from dotenv import load_dotenv

from ..core.config import settings
from ..models.brand import BrandModel
from ..models.key_benefits import BenefitModel
from ..models.label import LabelModel
from ..models.master_categories import MasterCategoryModel
from ..models.product_category import ProductCategoryModel
from ..models.refined_category import RefinedCategoryModel
from ..models.review import ReviewModel
from ..models.search_query import SearchQueryModel
from ..models.single_product import ProductModel
from ..models.register import RegisterModel
from ..models.preferance import PreferanceModel


mongo_client = AsyncIOMotorClient(settings.mongo_uri)

load_dotenv()

async def init_mongo():
    # Create Motor client
    # db_name = settings.mongo_uri.path.replace('/', '')
    db_name = os.getenv('mongo_db_name')

    # Init beanie with the Product document class
    await init_beanie(
        database=mongo_client[db_name],
        document_models=[
            BrandModel,
            BenefitModel,
            LabelModel,
            MasterCategoryModel,
            ProductCategoryModel,
            RefinedCategoryModel,
            ReviewModel,
            SearchQueryModel,
            ProductModel,
            RegisterModel,
            PreferanceModel
        ] # type: ignore
    )

