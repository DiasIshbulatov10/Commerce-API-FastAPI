import os
import json
import time
import concurrent.futures
import traceback
from numpy import ceil
import ujson
from fastapi.encoders import jsonable_encoder
from uuid import uuid4
from typing import Optional
from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse
from langchain.chat_models import ChatOpenAI
import asyncio
import time

from ...helpers.extract_labels import renormalize_labels, extract_master_label_weights_using_openAI
from ...helpers.search_helper import make_filters_criteria_filters
from ...helpers.boosters import CategoryBooster, TitleBooster, debug_print
from ...schema.skincare_labels import skincare_schema, skincare_labels
from ...openai_functions.extraction import create_extraction_chain
from ...openai_functions.openAIcompletion import fetch_vector_store
from ...db.pinecone import search_index
from ...middleware.custom_response import PagingResponse
from ...helpers.custom_score_final import custom_sort
from ...helpers.product_category.query_vector import get_query_product_data
from ...helpers.preprocess_search_query import preprocess_search_query
from ...helpers.pcsearch import parallel_search, search, parallel_search_with_score_by_vector, async_parallel_search, search_queries
from ...helpers.pinecone_helpers import extract_ids, extract_ids_from_results_list, extract_product_ids, calculate_custom_score, sort_products_by_reviews, calculate_custom_score_old
from ...helpers.mongo_helpers_v2 import retrieve_documents_summary, define_parameters_and_rerank_labels, process_label_name_list, perform_fuzzy_matching_for_attributes, process_product, extract_product_data, extract_sorted_labels, process_reviews, get_weighted_unique_list, get_products
from ...db.redis import redis_async_conn
from ...core.exceptions import NotFoundItem

from .route import router

@router.get(
    '/search',
    response_model=PagingResponse,
)
async def search_product(
    request: Request,
    query: str,
    brand: Optional[list[str]] = Query(None),
    master_category: Optional[list[str]] = Query(None),
    refined_category: Optional[list[str]] = Query(None),
    pl_summary: Optional[list[str]] = Query(None),
    max_price: Optional[float] = Query(None, ge=0),
    min_price: Optional[float] = Query(None, ge=0),
    total_records_fetched: Optional[int] = Query(500), 
    limit: Optional[int] = Query(20),
    page: int = Query(1, ge=1),
    query_id: Optional[str] = Query(None),
    include_reviews: Optional[bool] = Query(False)
):
    cache_id = query_id
    load_dotenv()
    openai_api_key = os.environ['openai_key']
    # Connect MongoDB
        # Access your database and collections
    db = request.app.database
    product_label_summaries = db['product_label_summaries']


    debug_print("Successfully connected to MongoDB")
    # Initialize the language model
    # llm = ChatOpenAI(temperature=0, 
    #                 model="gpt-3.5-turbo-16k", 
    #                 openai_api_key=openai_api_key)
    start_time = time.time()
    start_time_1 = time.time()
    if cache_id is None:
        cache_id = str(uuid4())
        # Start the timer
        # Initialize your skincare-specific chain
        skincare_search_query_chain = None
        # skincare_search_query_chain = create_extraction_chain(skincare_schema, llm, verbose=True) # Need to inject my own prompt into here somehow for refined outputs
        # Use function which vectorizes each key within the skincare-specific chain.
        search_query_JSON_list, labels, weighted_query_vector, dynamic_labels_filter = await preprocess_search_query(query, skincare_search_query_chain)
        # 1. Set top_k_values and call parallel_search function
        top_k_values = [total_records_fetched]  # These are the amount of search results for each query
        filter_criteria = make_filters_criteria_filters(brand=brand, master_category=master_category, refined_category=refined_category, pl_summary=pl_summary, min_price=min_price, max_price=max_price)

        print("OpenAI: 2 requests", time.time() - start_time)
        after_search_start = time.time()
        # Get the search queries for the products to be run on a later step
        search_tasks = search_queries(search_index, weighted_query_vector, top_k_values, filter_criteria, metadata_key='type', desired_value='prod', namespace='products', include_metadata=False)

        # 2. Search for top labels relevant to search query
        # search_query_labels_task = asyncio.to_thread(search, search_index, weighted_query_vector, metadata_key, desired_value_label, top_k, filter_criteria_positive, namespace ='positive_skincare_labels')
        # search_tasks.append(search_query_labels_task)

        # 3. Search for top labels relevant to vectorized search queries
        top_k_labels_search_params = 40

        keys = ["search"]

        # for query_dict in vectorized_search_query_JSON_list:
        #     for key, query_vector in query_dict.items():
        #         search_tasks.append(asyncio.to_thread(search, search_index, query_vector, metadata_key, desired_value_label, top_k_labels_search_params, filter_criteria_positive, namespace ='positive_skincare_labels'))
        #         keys.append(key)

        results = await asyncio.gather(*search_tasks)
        search_results = results[0:len(top_k_values)]
        # Choose the search result with the desired top_k value
        # print(f"Search results: {search_results}")
        filtered_res = search_results[0]

        # Extract the list of ids
        # search_query_labels_id_list = extract_ids(results[len(top_k_values)])
        # debug_print(f"search_query_labels_id_list: {search_query_labels_id_list}")

        labels_name = [label["label"] for label in labels["label_weights"]] if labels["label_weights"] else []
        # Create a list of dictionaries, each containing the original query and extracted ids
        # results_list = [{i: j} for i, j in zip(keys, results[len(top_k_values) + 1:])]
        # search_query_params_ids = extract_ids_from_results_list(results)

        
        # Grab list of unique product ids from the results
        prod_ids = extract_product_ids(filtered_res)
        unique_prod_ids = list(set(prod_ids))

        if not unique_prod_ids:
            PagingResponse(
            data = {
                "products": [],
                "dynamic_labels_filters": [],
                "wighted_master_labels": []
            },
            query_id = cache_id,
            page = page,
            limit = limit,
            count = 0,
            pages=1
        )

        print("search from pinecone", time.time() - after_search_start)

        reviews = []
        if include_reviews:
            reviews_vectorstore = fetch_vector_store('semantic-search-openai-labels', text_key = 'title', namespace = "reviews")
            reviews = reviews_vectorstore.similarity_search_by_vector_with_score(weighted_query_vector, k = 10, filter = {}, namespace = "reviews")

        mongo_things_start = time.time()    

        # Builds a database of master label dictionaries and unique master labels for later use
        # Create a dictionary of products by calling the MongoDB collection using the unique product ids
        debug_print("Building base list of master labels and unique labels...\n")
        debug_print("Create a dictionary of products by calling the MongoDB collection using the unique product ids...\n")

        try:
            (master_label_dict, unique_master_labels), docs_summary_dict, products = await asyncio.gather(*[define_parameters_and_rerank_labels(db), retrieve_documents_summary(product_label_summaries, unique_prod_ids), get_products(db, unique_prod_ids)])
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            return JSONResponse({
                "error": "Internal Server Error"
            }, status_code=500)
        
        # Outputting processed information for debugging or logs
        debug_print(f"Master Label Dictionary in Database: {master_label_dict}")
        debug_print("=" * 70)
        debug_print(f"Unique Labels in Database: {unique_master_labels}")
        debug_print("=" * 70)

        # Processing label IDs related to the search query using the function from another file
        debug_print("Processing search query labels...\n")
        search_query_filtered_labels, search_query_master_label_list = await process_label_name_list(db, labels_name, master_label_dict, unique_master_labels)
        # Outputting processed information for debugging or logs
        debug_print(f"Search Query Master Label List: {search_query_master_label_list}")
        debug_print("=" * 70)
        debug_print(f"Search Query Filtered Labels: {search_query_filtered_labels}")
        debug_print("=" * 70)

        # Process search query parameters to perform label matching using function from another file

        debug_print("Processing search_query_params_flattened_unique_labels, list of label ids related to the search query parameters...\n")

        # Output processed information for debugging or logs
        debug_print("=" * 70)

        # Process fuzzy matching to perform label matching against all parameters from the search_query_dict
        debug_print("Performing fuzzy matching on search query parameters...\n")
        _, _, search_query_params_fuzzy_master_labels = perform_fuzzy_matching_for_attributes(search_query_JSON_list, search_query_filtered_labels, master_label_dict, threshold=95)

        print("mongo things", time.time() - mongo_things_start)
        labels_start = time.time()  

        # Output processed information for debugging or logs
        debug_print(f"Master Labels Based on Fuzzy-Matched Labels: {search_query_params_fuzzy_master_labels}")
        debug_print("=" * 70)

        # Get final list of labels and their weights, by using a custom weighted function
        final_list = get_weighted_unique_list(
            search_query_master_label_list,
            search_query_params_fuzzy_master_labels
        )

        final_list = [label for label in final_list if isinstance(label, str)]

        master_labels_extracted_using_AI_and_schema = []
        for label in labels_name:
            for search_query_label in search_query_filtered_labels:
                if label in search_query_label:
                        master_labels_extracted_using_AI_and_schema.append((search_query_label, 1,))
        
        master_labels_extracted_using_AI_and_schema = [extraction + ((1/len(master_labels_extracted_using_AI_and_schema)),) for extraction in master_labels_extracted_using_AI_and_schema]

        product_data_with_relevance = []  # Initialize an empty list to store processed product data
        product_search_results = filtered_res['matches']  # Assuming filtered_res['matches'] contains the list of dictionaries
        relevance_scores = []
        
        # for product_metadata in product_search_results:  # Loop over product_search_results 
        #     try:
        #         product_data_with_relevance_entry = process_product( # function contains several booster functions which boost products based on search_query_JSON_list
        #             product_metadata, 
        #             docs_dict, 
        #             master_labels_extracted_using_AI_and_schema, 
        #             search_query_JSON_list, 
        #             master_label_dict
        #         )
        #         if product_data_with_relevance_entry is not None:  # Removing products that don't have reviews (i.e. the ids don't appear in the mongoDB review_summaries collection)
        #             product_data_with_relevance.append(product_data_with_relevance_entry)
        #     except Exception as e:
        #         print(f"Error processing product {product_metadata.get('id', 'unknown_id')}: {e}")
        #         traceback.print_exc()
        #         return JSONResponse({
        #             "error": "Internal Server Error"
        #         }, status_code=500)

        # Processing the search results based on master_labels_extracted_using_AI_and_schema. Re-ranks the products based on its weights, and the presence of these master labels in the products

        # print("labels", time.time() - labels_start)
        rerank_start = time.time()

        # Get processed product data
        processed_product_list = await asyncio.gather(*[process_product(
            product_metadata, 
            docs_summary_dict,
            products,
            master_labels_extracted_using_AI_and_schema, 
            search_query_JSON_list, 
            master_label_dict,
        ) for product_metadata in product_search_results])

        # Execute process_product and collect relevance scores
        for idx, processed_product in enumerate(processed_product_list):
            try:
                if processed_product is not None:
                    product_data_with_relevance.append(processed_product)
                    relevance_scores.append(processed_product['relevance_score_with_boost'])
            except Exception as e:
                print(f"Error processing product {product_search_results[idx].get('id', 'unknown_id')}: {e}")
                import traceback
                traceback.print_exc()

        # Normalize the collected relevance scores
        min_score, max_score = min(relevance_scores), max(relevance_scores)

        for entry in product_data_with_relevance:
            normalized_score = (entry['relevance_score_with_boost'] - min_score) / (max_score - min_score) if max_score != min_score else 0.5
            entry['normalized_relevance_score'] = normalized_score
            debug_print(f"normalized score: {entry['normalized_relevance_score']}")
            
        # Apply title and category boosts to the normalized scores
        for entry in product_data_with_relevance:
            title_boost = TitleBooster.get_title_boost(entry['product_metadata'], search_query_JSON_list)
            category_boost = CategoryBooster.get_category_boost(entry['product_metadata'], search_query_JSON_list)
            debug_print(f"category_boost: {category_boost}")
            relevance_score = entry['normalized_relevance_score'] + title_boost + category_boost
            debug_print(f"relevance_score: {relevance_score}")
            entry['relevance_score'] = relevance_score
            
        # Sort by having "Relevant to You" data and by descending Relevance Score
        sorted_products = sorted(product_data_with_relevance, key=custom_sort, reverse=True)
        # start_time = time.time()
        # if include_reviews:
        #     prod_reviews = await calculate_custom_score(sorted_products, weighted_query_vector, top_k = 4) 
        # end_time = time.time()
        # print(f"Time taken to calculate custom score NEW: {end_time - start_time}")
        result = []
        if include_reviews:
            # Grabbing the reviews 1 by 1 from Pinecone, by using the ids from before as metadata filters and specifiying how many reviews to return
            try:
                # Order the results using the calculate custom score function
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    prod_reviews = calculate_custom_score_old(executor, sorted_products, unique_prod_ids, search, weighted_query_vector, top_k = 2) # top_k is the amount of reviews to grab
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
            # Loop through each product in sorted_products. Append each product in sorted_products with a 'reviews' key containing its dictionary of reviews.
            for product in sorted_products:
                # Extract the product ID from the nested metadata
                prod_id = product.get('product_metadata', {}).get('_id')
                
                # Check if 'prod_id' exists in the 'prod_reviews' dictionary
                if prod_id in prod_reviews:
                    # Extract reviews for the corresponding 'prod_id' from 'results'
                    reviews = prod_reviews.get(prod_id, {}).get('reviews', {})
                    
                    # Add the 'reviews' field to the product dictionary
                    product['reviews'] = reviews
        # Printing the results in a new, more ordered format. Each product will now have reviews, sorted 

        # Step 1: Initialization
        product_data_with_updated_scores = []

        # Step 2: Iterate Over Products
        for product_data in sorted_products:
            # Extract product details
            product_details = extract_product_data(product_data['product_metadata'])
            
            matched_skin_concerns = []
            sorted_top_3_reviews = []
            if include_reviews:
                # Validate and Process reviews
                reviews_dict = product_data.get('reviews', {})  # 'reviews' is now expected to be a dictionary
                if reviews_dict:  # Checking if it's not empty
                    matched_skin_concerns, sorted_top_3_reviews = process_reviews(reviews_dict, search_query_JSON_list)
                else:
                    print(f"No reviews found for product: {product_details.get('product_id')}")
                    continue  # Skip to the next iteration
            
            # Compute updated relevance score (NEW LOGIC)
            original_relevance_score = product_data['relevance_score_with_boost']
            updated_relevance_score = original_relevance_score + 0.05 * len(set(matched_skin_concerns))
            if matched_skin_concerns:
                updated_relevance_score += 0.5
            # Construct data dictionary
            product_details.update({
                'relevance_score': updated_relevance_score,
                'filtered_master_label_counts_using_AI_dict_str': extract_sorted_labels(product_data['filtered_master_label_counts_using_AI_dict_str']),
                'top_5_overview_labels': extract_sorted_labels(product_data['overview_str']),
                'top_5_master_labels': extract_sorted_labels(product_data['master_label_counts_str']),
                'sorted_top_3_reviews': sorted_top_3_reviews,
                'matched_skin_concerns': matched_skin_concerns,
                'wighted_labels': master_labels_extracted_using_AI_and_schema,
                'reviews_count': product_data['reviews_count'],
                # 'pl_summary': product_data['pl_summary']
            })
            product_data_with_updated_scores.append(product_details)
            # result.append(getList_Productdata(data, is_reviews_included=include_reviews))
        if include_reviews:
            # Sort the products by relevance score
            product_data_with_updated_scores.sort(key=lambda x: (-x['relevance_score'], -len(set(x['matched_skin_concerns'])), -len(x['matched_skin_concerns'])))
        # product_data_with_updated_scores = sorted(product_data_with_updated_scores, key=lambda x: x['relevance_score'], reverse=True)
        # Cache the result
        asyncio.create_task(
            redis_async_conn.set(
                f'query_product_cache/{cache_id}',
                ujson.dumps(jsonable_encoder(product_data_with_updated_scores)),
                ex=1800
            )
        )
        count = len(product_data_with_updated_scores)
        products = product_data_with_updated_scores[page - 1: limit]
        result = {
            "products": products,
            "dynamic_labels_filters": dynamic_labels_filter,
            "wighted_master_labels": master_labels_extracted_using_AI_and_schema
        }
        print(f"rerank: {time.time() - rerank_start}")
    else:
        raw_data = await redis_async_conn.get(f'query_product_cache/{cache_id}')
        if raw_data is None:
            raise NotFoundItem("Cache not found")
        cached_data = ujson.loads(raw_data)
        start_index = (page - 1) * limit
        end_index = (page + 1) * limit
        count = len(cached_data)
        result = cached_data[start_index:end_index]
    print("final", time.time() - start_time_1)

    return PagingResponse(
        data = result,
        query_id = cache_id,
        page = page,
        limit = limit,
        count = count,
        pages=ceil(count / limit)
    )