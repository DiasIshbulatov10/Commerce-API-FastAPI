import asyncio
from .pcsearch import search
from collections import defaultdict
import concurrent.futures
from ..db.pinecone import search_index


def extract_ids(results):
    """Extract IDs from the search results."""
    return [result['id'] for result in results['matches']]


def extract_id_label_pairs(results):
    """Extract pairs of IDs and labels from the search results."""
    return [(result['id'], result['metadata']['label']) for result in results['matches']]


def search_and_extract_product_labels(index, query_vector, metadata_key, desired_value, top_k, filter_criteria={}):
    """Search for labels based on the query vector and metadata, then extract product labels."""
    results = search(index, query_vector, metadata_key, desired_value, top_k, filter_criteria)
    return {match['metadata']['prod_id']: match['metadata']['labels'] for match in results['matches']}


def search_labels_for_vectorized_queries(index, vectorized_search_query_list, metadata_key, desired_value, top_k_labels, filter_criteria={}):
    """Perform search for multiple vectorized queries and extract their labels."""
    results = []
    for i, query_dict in enumerate(vectorized_search_query_list):
        if not isinstance(query_dict, dict):
            # print(f"Skipping item at index {i} because it's not a dictionary.")
            continue
        
        for key, vector in query_dict.items():
            if vector is None:
                # print(f"No vector found for key {key} in dictionary at index {i}.")
                continue
            
            result = search(index, vector, metadata_key, desired_value, top_k_labels, filter_criteria)
            
            results.append({"query": {key: vector}, "result": result})
            
    return results


def extract_ids_from_results_list(results_list):
    """Extract IDs from the results of multiple searches."""
    # extracted_ids = []
    for result_dict in results_list:
        ids = [match["metadata"]['_id'] for match in result_dict["matches"]]
        # extracted_ids.append({query_key: ids})
        
        # for query_key, query_results_list in result_dict.items():  # Iterate over keys in each dictionary in results_list
            # if isinstance(query_results_list, list):
                # for query_results in query_results_list:
                    # matches = query_results.get('matches', [])
                
            # else:
            #     matches = query_results_list.get('matches', [])
            #     ids = [match['id'] for match in matches]
            #     extracted_ids.append({query_key: ids})
    return ids


def extract_product_ids(filtered_res):
    """Extract product IDs from the filtered results."""
    # return [result['metadata']['_id'] for result in filtered_res['matches']] if filtered_res['matches'] else []
    return [result['id'] for result in filtered_res['matches']] if filtered_res['matches'] else []


def score_reviews(executor, custom_score, all_reviews, search_query_JSON_list):
    """Score the reviews based on custom logic."""
    scored_reviews_dict = {}
    for review in all_reviews['matches']:
        review_score, matched_data = executor.submit(custom_score, review, search_query_JSON_list).result()
        review['custom_score'] = review_score
        review['matched_data'] = matched_data
        scored_reviews_dict[review.get('id', '')] = review  # Using get() to avoid KeyError
    return scored_reviews_dict


def sort_and_filter_reviews(scored_reviews_dict, top_k=3):
    """Sort and filter the reviews based on their custom scores."""
    sorted_reviews = sorted(scored_reviews_dict.items(), key=lambda x: x[1].get('custom_score', 0), reverse=True)
    return dict(sorted_reviews[:top_k])

def divide_filter_results(results, chunk_size):
    resultant_arr = []

    # supportive divide
    def recursive_divide(arr):
        if len(arr) <= chunk_size:
            resultant_arr.append(arr)
        else:
            resultant_arr.append(arr[:chunk_size])
            recursive_divide(arr=arr[chunk_size:])
    
    recursive_divide(results)
    return resultant_arr

async def search_and_sort_results(enumerate_list, **vector_params):
    weighted_query_vector = vector_params['weighted_query_vector']
    top_k = vector_params['top_k']

    result = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for _, data in enumerate(enumerate_list):  # Using get() to avoid KeyError
            prod = data['product_metadata']
            # Search for all reviews for a given product
            all_reviews = search(search_index, weighted_query_vector, metadata_key='type', desired_value='review', top_k=top_k, filter_criteria = {}, namespace ='reviews', prod_id = prod['id'])
            # print(f"all_reviews: {all_reviews}, type: {type(all_reviews)}")  # Debug statement
            
            if all_reviews is None:
                print("No reviews found. Skipping.")
                continue

            # Access the matches and metadata fields
            review_list = all_reviews.get('matches', [])
            metadata_dict = {review.get('id'): review.get('metadata', {}) for review in review_list}
            
            # To get top_k reviews, if there are at least that many
            top_k_reviews = {k: metadata_dict[k] for k in list(metadata_dict.keys())[:top_k]}
            
            result.append({prod['id']: top_k_reviews})
    return result
def calculate_custom_score_old(executor: concurrent.futures.Executor, filtered_res, prod_ids, search, weighted_query_vector, top_k=1):
    results = defaultdict(dict)
    with executor as executor:
        for i, match in enumerate(filtered_res):
            prod_id = match.get('product_metadata', {}).get('metadata', {}).get('_id')
            
            if prod_id is None:
                print("Product ID not found. Skipping.")
                continue
            
            print(f"Processing Product ID: {prod_id}")
            
            all_reviews = search(search_index, weighted_query_vector, metadata_key='type', desired_value='review', top_k=top_k, filter_criteria={}, namespace='reviews', prod_id=prod_id)
            
            # print(f"all_reviews: {all_reviews}, type: {type(all_reviews)}")  # Debug statement
            
            if all_reviews is None:
                print("No reviews found. Skipping.")
                continue

            # Access the matches and metadata fields
            review_list = all_reviews.get('matches', [])
            metadata_dict = {review.get('id'): review.get('metadata', {}) for review in review_list}
            
            # To get top_k reviews, if there are at least that many
            top_k_reviews = {k: metadata_dict[k] for k in list(metadata_dict.keys())[:top_k]}
            
            results[prod_id].update({
                'index': i,
                'reviews': top_k_reviews  # Store the reviews as a dictionary
            })

    return results

async def calculate_custom_score(filtered_res, weighted_query_vector, top_k=1):
    """Calculate custom scores for reviews and sort them for each product."""
    results = []
    enumerate_list = divide_filter_results(filtered_res, chunk_size=10)
    result_tasks = [asyncio.create_task(search_and_sort_results(list_data, weighted_query_vector=weighted_query_vector, top_k=top_k)) for list_data in enumerate_list]
    response = await asyncio.gather(*result_tasks)
    for data_list in response:
        for data_dict in data_list:
            for key, value in data_dict.items():
                results.append({"product_id": key, "review": value})
    return results

def sort_products_by_reviews(filtered_res, results):
    """Sort products by the presence or absence of reviews."""
    
    # Initialize lists to store sorted products
    products_with_reviews_present, products_with_reviews_absent = [], []
    
    # Loop through each product_metadata in filtered_res['matches']
    for product_metadata in filtered_res['matches']:
        product_id = get_product_id(product_metadata)  # Assuming this function exists and works correctly

        # Check if the product ID exists in results
        if product_id not in results:
            continue  # Skip this iteration and move to the next

        # Check if 'reviews' key exists in results[product_id]
        if 'reviews' not in results[product_id]:
            continue  # Skip this iteration and move to the next

        # Fetch the reviews for this product_id
        reviews = results[product_id]['reviews']

        # Depending on whether reviews exist or not, append them to the appropriate list
        if len(reviews) > 0:
            products_with_reviews_present.append((product_metadata, reviews))
        else:
            products_with_reviews_absent.append((product_metadata, reviews))
    
    # Sort the products_with_reviews_present list based on the number of reviews and index.
    # products_with_reviews_present.sort(key=lambda x: (len(results[get_product_id(x[0])]['reviews']) == 0, results[get_product_id(x[0])]['index']))
    
    return products_with_reviews_present, products_with_reviews_absent


def get_product_id(product_metadata):
    """Return the product ID from metadata."""
    # return product_metadata['metadata'].get('_id', 'N/A')
    return product_metadata['id']
