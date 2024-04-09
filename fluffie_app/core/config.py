import os
from pydantic import AnyUrl, BaseSettings
from dotenv import load_dotenv

from starlette.datastructures import CommaSeparatedStrings, Secret

from ..env import EnvData 

JWT_TOKEN_PREFIX = "Token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 days
SECRET_KEY = Secret(os.getenv("SECRET_KEY", "secret key for project"))
ALGORITHM = "HS256"

load_dotenv()

class _PineconeSettings(BaseSettings):
  api_key: str = EnvData.api_key
  environment: str = EnvData.environment

  class Config:
    env_prefix = 'pinecone_'

class _Settings(BaseSettings):
  port: int = 3000

  mongo_uri: AnyUrl = os.getenv("mongo_uri")

  redis_uri: AnyUrl = os.getenv("redis_uri")

  openai_key: str = os.getenv("openai_key")

  class Config:
      case_sensitive = False

settings = _Settings() # type: ignore

pinecone_settings = _PineconeSettings()
