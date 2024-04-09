from typing import Optional, TypedDict
import time

from .analyze_query import extract_dictionary_and_age_group
from ...services.openai.embeddings import get_embeddings
from .custom_score import custom_score
from .pcsearch import search_reviews, search_products
from fluffie_app.core.logger import logger
import asyncio

# Get the filtered product results by using metadata filter 'type': 'prod'
metadata_key = 'type'
desired_value = 'prod'

class QueueProductData(TypedDict):
  search_query: str
  search_query_dict: dict
  age_group: Optional[str]
  query_vector: list[float]
  filter_criteria: dict

def get_query_product_data(search_query: str) -> QueueProductData:
  #extract the key information from the search query as a dictionary, including the age group as a string, e.g. '18-24'
  search_query_dict, age_group = extract_dictionary_and_age_group(search_query)
  search_query_dictionary_string = str(search_query_dict) + search_query

  query_vector = get_embeddings([search_query_dictionary_string])[0]

  filter_criteria = {}
  if 'price' in search_query_dict:
      filter_criteria['price'] = search_query_dict['price']

  return {
    'search_query': search_query,
    'search_query_dict': search_query_dict,
    'age_group': age_group,
    'query_vector': query_vector,
    'filter_criteria': filter_criteria,
  }


async def query_product_by_vector(query_data: QueueProductData, top_k: int = 20, yield_count: int = 20, exclude_products = None):
  start_time = time.time()
  filtered_res = await search_products(query_data['query_vector'], metadata_key, desired_value, top_k, query_data['filter_criteria'], exclude_products)


  # Create a list to store products with no reviews
  no_reviews_products = []

  # Use a set to store the encountered prod_ids
  encountered_prod_ids = set()

  # Create a list to store the final results (API URI version)
  api_results = []
  # Get all reviews for the current product
  prod_ids = [ result['metadata']['_id'] for result in filtered_res["matches"] ]
  logger.warning("--- prod_ids %s" % prod_ids)


  for result in filtered_res['matches']:
    result_count = len(api_results)
    if result_count != 0 and result_count % yield_count == 0:
      yield encountered_prod_ids, api_results

    prod_id = result['metadata']['_id']

    # Skip the product if it has already been processed
    if prod_id in encountered_prod_ids:
      continue

    # Add the current prod_id to the encountered set
    encountered_prod_ids.add(prod_id)

    all_reviews = await search_reviews(query_data['query_vector'], prod_id, metadata_key='type', desired_value='review', top_k=3)
    logger.warning("--- all_reviews %s" % all_reviews['matches'])
    # all_reviews = {'matches': None}
    if not all_reviews['matches']:
      no_reviews_products.append(result['metadata'])

    else:
      product_data = {
        "brand": result['metadata'].get('brand', 'N/A'),
        "title": result['metadata'].get('title', 'N/A'),
        "master_category": result['metadata'].get('master_category', 'N/A'),
        "refined_category": result['metadata'].get('refined_category', 'N/A'),
        "price": result['metadata'].get('price', 'N/A'),
        "id": result['metadata'].get('_id', 'N/A'),
        "reviews": []
      }

      # Calculate the custom scores for each review and store them in the reviews dictionary
      scored_reviews = []

      for review in all_reviews['matches']:
        review_score, matched_data = custom_score(review, query_data['search_query_dict'], query_data['age_group'])

        review_data = {
          "score": review_score,
          "matched_data": matched_data,
          "text": review['metadata']
        }
        scored_reviews.append(review_data)

      # Sort the scored_reviews by custom_score in descending order and take the top 3
      product_data['reviews'] = sorted(scored_reviews, key=lambda x: x['score'], reverse=True)[:3]

      api_results.append(product_data)

  # Add products without reviews to the api_results list
  for product_metadata in no_reviews_products:
    result_count = len(api_results)
    if result_count != 0 and result_count % yield_count == 0:
      yield encountered_prod_ids, api_results

    product_data = {
        "brand": product_metadata.get('brand', 'N/A'),
        "title": product_metadata.get('title', 'N/A'),
        "master_category": product_metadata.get('master_category', 'N/A'),
        "refined_category": product_metadata.get('refined_category', 'N/A'),
        "price": product_metadata.get('price', 'N/A'),
        "id": product_metadata.get('_id', 'N/A'),
        "reviews": []
    }
    api_results.append(product_data)

  yield encountered_prod_ids, api_results
