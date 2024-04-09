from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
import asyncio


# Generate combined filter criteria
def generate_combined_filters(metadata_key, desired_value, filter_criteria):
    combined_filters = [
        {metadata_key: {"$eq": desired_value}}
    ]
    for key, value in filter_criteria.items():
        if key == 'price' and isinstance(value, tuple):
            if value[0] is not None and value[1] is not None:
                combined_filters.append({key: {"$gte": value[0], "$lte": value[1]}})
            elif value[0] is not None:
                combined_filters.append({key: {"$gte": value[0]}})
            elif value[1] is not None:
                combined_filters.append({key: {"$lte": value[1]}})
        else:
            combined_filters.append({key: {"$eq": value}})
    return combined_filters

# General search function that handles reviews, products, and labels
def search(index, query_vector, metadata_key, desired_value, top_k, filter_criteria, namespace, prod_id=None, include_metadata=False):
    combined_filters = generate_combined_filters(metadata_key, desired_value, filter_criteria)

    if prod_id:
        combined_filters.append({"prod_id": {"$eq": prod_id}})

    results = index.query(
        vector=query_vector,
        filter={"$and": combined_filters},
        top_k=top_k,
        includeValues=False,
        namespace = namespace,
        include_metadata=include_metadata
    )
    return results

# Parallel search for products
def parallel_search(index, query_vector, top_k_values, filter_criteria, metadata_key='type', desired_value='prod', namespace=''):
    with ThreadPoolExecutor() as executor:
        # metadata_key and desired_value are now parameters
        search_futures = [
            executor.submit(search, index, query_vector, metadata_key, desired_value, top_k, filter_criteria, namespace) 
            for top_k in top_k_values
        ]
        search_results = [future.result() for future in search_futures]
    return search_results

async def async_parallel_search(index, query_vector, top_k_values, filter_criteria, metadata_key='type', desired_value='prod', namespace=''):
    search_results = await asyncio.gather(*[asyncio.to_thread(search, index, query_vector, metadata_key, desired_value, top_k, filter_criteria, namespace) for top_k in top_k_values])
    return search_results

def search_queries(index, query_vector, top_k_values, filter_criteria, metadata_key='type', desired_value='prod', namespace='', include_metadata=False):
    return [asyncio.to_thread(search, index, query_vector, metadata_key, desired_value, top_k, filter_criteria, namespace, include_metadata) for top_k in top_k_values]

def parallel_search_with_score_by_vector(vectorstore, embedding: List[float], top_k_values: List[int], filter_criteria: Optional[dict] = None, score_threshold: float = 0.0, namespace: str = ''):
    with ThreadPoolExecutor() as executor:
        search_futures = [
            executor.submit(vectorstore.similarity_search_by_vector_with_score, embedding, k=top_k, filter=filter_criteria, namespace=namespace)
            for top_k in top_k_values
        ]
        
        search_results = [future.result() for future in search_futures]
    
    # Filter results based on score_threshold and convert to metadata
    filtered_results = [[doc.metadata for doc, score in res if score >= score_threshold] for res in search_results]
    
    return filtered_results