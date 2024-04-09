import pinecone
from tenacity import retry, wait_random_exponential, stop_after_attempt

from ..core.config import pinecone_settings
from ..utils.async_wrap import to_async

index_name = 'semantic-search-openai-labels'

pinecone.init(
  api_key=pinecone_settings.api_key,
  environment=pinecone_settings.environment  # find next to api key in console
)

search_index = pinecone.Index(index_name)

query_search_index = to_async(
  retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
  (search_index.query)
)

scan_search_index = to_async(
  retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
  (search_index.describe_index_stats)
)
