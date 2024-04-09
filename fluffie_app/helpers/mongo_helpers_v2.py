from collections import Counter
import pandas as pd
from fuzzywuzzy import process
from collections import defaultdict
from fuzzywuzzy import fuzz
from scipy.stats import hmean
import numpy as np
from .extract_labels import extract_master_labels_using_openAI
from dateutil.parser import parse
from datetime import datetime, date
from .boosters import debug_print  # Make sure to import the appropriate classes from your boosters.py file
import pymongo
from pymongo.errors import PyMongoError
import asyncio
from bson.objectid import ObjectId

import fluffie_app.helpers.cache as cache

# Function to find top master label matches (returns top 3 by default if limit not called)
def get_top_master_label_matches(skin_concerns, master_label_list, limit=3):
    # Check if skin_concerns is None and return an empty list if it is
    if skin_concerns is None:
        return []

    master_check = []
    for concern in skin_concerns:
        matches = process.extract(concern, master_label_list, limit=limit)
        master_check.extend([match[0] for match in matches])
    return master_check

# Defining function for fuzzy scores
def get_fuzzy_scores(input_values, labels, min_score=50):
    if input_values is None:
        input_values = []
        
    fuzzy_scores = defaultdict(int)
    
    for concern in input_values:
        for label in labels:
            match_score = fuzz.token_set_ratio(label, concern)
            if match_score > min_score and match_score > fuzzy_scores[label]:
                fuzzy_scores[label] = match_score    

    return fuzzy_scores

def calculate_base_relevance_score(sorted_positive_labels_in_doc, reviews_count):
    total_label_count = sum(label_dict['reviews'] for label_dict in sorted_positive_labels_in_doc.values())
    base_relevance_score = total_label_count / reviews_count if reviews_count > 0 else 0
    return base_relevance_score

def get_master_label_counts(positive_labels_in_doc, master_label_dict):
    master_label_counts = {}
    for original_label, label_dict in positive_labels_in_doc.items():
        master_label = master_label_dict.get(original_label, original_label)
        if master_label not in master_label_counts:
            master_label_counts[master_label] = 0
        master_label_counts[master_label] += label_dict['reviews']

    # Create the string representation
    master_label_counts_str = ' • '.join(f'{key} ({value})' for key, value in master_label_counts.items())

    return master_label_counts, master_label_counts_str

def convert_label_totals_to_str(master_label_totals):
    master_label_total_labels = [{'label': master_label, 'reviews': count} for master_label, count in master_label_totals.items()]
    return " • ".join([f"{label_dict['label']} ({label_dict['reviews']})" for label_dict in master_label_total_labels])

def filter_label_counts(master_label_counts, matching_labels):
    return [{'label': key, 'reviews': value} for key, value in master_label_counts.items() if key in matching_labels]

def calculate_total_boost(filtered_label_counts, reviews_count, search_query_master_labels_weights=None):
    total_boost = 0

    # Check if search_query_master_labels_weights is a list of 3-tuples
    if all(isinstance(item, tuple) and len(item) == 3 for item in search_query_master_labels_weights or []):
        weight_dict = {label: weight for label, _, weight in search_query_master_labels_weights}
    elif search_query_master_labels_weights is None:
        weight_dict = {label_dict['label']: 1 for label_dict in filtered_label_counts}
    else:
        raise ValueError("search_query_master_labels_weights must be a list of 3-tuples.")
    
    # Ensure each item in filtered_label_counts is a dictionary with a 'label' key
    if not all(isinstance(label_dict, dict) and 'label' in label_dict for label_dict in filtered_label_counts):
        raise ValueError("Each item in filtered_label_counts must be a dictionary with a 'label' key.")

    for label_dict in filtered_label_counts:
        label = label_dict['label']
        label_weight = weight_dict.get(label, 1)  # Default to 1 if label has no weight
        label_percentage = label_dict['reviews'] / reviews_count
        harmonic_mean = hmean([label_dict['reviews'], 1 / (label_percentage + 1e-9)])
        
        # Print calculation details
        debug_print(f"Label: {label}")
        debug_print(f"Label Weight: {label_weight}")
        debug_print(f"Label Percentage: {label_percentage}")
        debug_print(f"Harmonic Mean: {harmonic_mean}")
        debug_print(f"Weighted Harmonic Mean: {harmonic_mean * label_weight}")
        debug_print("----------------------------")
        
        total_boost += harmonic_mean * label_weight  # Apply the weight here

    debug_print(f"Total Boost: {total_boost}")
    return total_boost

def filter_label_counts(overview_labels, label_list_most_relevant_to_search_concerns):
    return [{'label': label, 'reviews': overview_labels[label]} for label in label_list_most_relevant_to_search_concerns if label in overview_labels]

def get_mapped_labels(label_list_most_relevant_to_search_concerns, master_label_dict):
    # create a list of matched labels
    mapped_labels = [master_label_dict[label] for label in label_list_most_relevant_to_search_concerns if label in master_label_dict]

    # count the occurrence of each label
    label_counts = Counter(mapped_labels)

    # compute the total number of labels
    total_labels = sum(label_counts.values())

    # create a list of tuples where each tuple is (label, occurrence, weighting)
    # and sort the list by occurrence in descending order
    search_query_master_labels_weights = sorted([(label, count, count / total_labels) for label, count in label_counts.items()], key=lambda x: x[1], reverse=True)

    # create a list of just the labels
    search_query_master_labels = [label for label, count, weight in search_query_master_labels_weights]

    return search_query_master_labels_weights, search_query_master_labels

def get_original_labels_for_master_labels(master_labels, master_label_dict):
    original_labels_dict = {}
    for original, master in master_label_dict.items():
        for master_label in master_labels:
            # Check if master_label is a tuple, and if so, take the first element
            if isinstance(master_label, tuple):
                master_label = master_label[0]
            
            if master == master_label:
                if master not in original_labels_dict:
                    original_labels_dict[master] = []
                original_labels_dict[master].append(original)
    return original_labels_dict

def get_matching_labels(original_labels_dict, overview_labels):
    product_labels_matched_to_search_query = []
    for original_labels in original_labels_dict.values():
        for label in original_labels:
            if label in overview_labels:
                product_labels_matched_to_search_query.append((label, overview_labels[label]))
    return product_labels_matched_to_search_query

def extract_exact_master_labels(search_query_master_label_list, labels):
    extracted_labels = [label for label in search_query_master_label_list if label in labels]
    return extracted_labels

def unique_ordered(values):
    seen = set()
    unique_values = []
    for value in values:
        if value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values

def add_skin_type_labels_to_search_query_labels(extracted_labels_from_clustered_labels, master_label_counts, product_labels_matched_to_search_query):
    for label in extracted_labels_from_clustered_labels:
        if label in master_label_counts:
            # Accessing 'reviews' count from the inner dictionary of master_label_counts
            count = master_label_counts[label]['reviews']
            # Appending tuple (label, count) to product_labels_matched_to_search_query
            product_labels_matched_to_search_query.append((label, count))
    return product_labels_matched_to_search_query

def extract_matched_query_to_skin_type_overviews(clustered_labels, labels_in_doc):
    matched_labels = []
    for label in clustered_labels:
        for doc_label, associated_labels in labels_in_doc:
            if label == doc_label:
                matched_labels.append((doc_label, associated_labels))
    return matched_labels

from bson.objectid import ObjectId

async def get_labels_from_ids(db, collection_name, ids_input):
    """
    Given a database, collection name and a list or dictionary of ids, 
    fetches the corresponding labels from the database.

    Args:
    db (pymongo.database.Database): The database to fetch labels from.
    collection_name (str): The collection from which to fetch the labels.
    ids_input (list of str or dict of str: list of str): A list or dictionary where each value 
                                                         is a list of ids.

    Returns:
    list of str or dict of str: list of str: A list or dictionary where each key corresponds to a key from ids_input 
                                                   and each value is a list of 'label' values from the database for the corresponding ids.
    """
    query_options = {
        "projection": {"label": 1},
        "cursor_type": pymongo.CursorType.NON_TAILABLE,
        "max_time_ms": 5000
    }
    async def fetch_labels(id_list):
        labels = []
        query = {}
        q_list = []
        for id in id_list:
            q_list.append(
                {"_id": ObjectId(id)}
            )
        query["$or"] = q_list
        batch_size = 100
        page = 1
        batch = []
        total = len(id_list)
        while True:
            cursor = db[collection_name].find(query, **query_options)
            batchKwargs = {
                "cursor": cursor,
                "page": page,
                "batch_size": batch_size
            }
            batch.append(asyncio.create_task(fetch_collection_data(**batchKwargs)))
            if (page * batch_size) >= total:
                break
            page += 1
        response = await asyncio.gather(*batch)
        for docList in response:
            for doc in docList:
                labels.append(doc['label'])
        return labels

    # Initialize an empty dictionary to store the output labels
    labels_output = {}

    # Check if ids_input is a list of dictionaries
    if isinstance(ids_input, list) and all(isinstance(d, dict) for d in ids_input):
        for single_dict in ids_input:
            for key, id_list in single_dict.items():
                labels_output[key] = await fetch_labels(id_list)
    elif isinstance(ids_input, dict):
        labels_output = {key: await fetch_labels(id_list) for key, id_list in ids_input.items()}
    elif isinstance(ids_input, list):
        labels_output = await fetch_labels(ids_input)
    else:
        raise TypeError("Invalid type for ids_input. Must be a dictionary or a list.")

    return labels_output


def extract_cached_non_cached_labels(cached_labels, names_input):
    cached_labels = [cached_label for cached_label in cached_labels if cached_label is not None]
    cached_labels_keys = [el["key"] for el in cached_labels]
    cached_labels_data = [el["data"] for el in cached_labels]
    non_cached_labels = [name for name in names_input if name not in cached_labels_keys]
    cached_labels_name = []
    for cached_data in cached_labels_data:
        for el in cached_data:
            if "_id" in el:
                cached_labels_name.append(el["label"])
    return cached_labels_name, non_cached_labels

async def get_labels_from_name(db, collection_name, names_input):
    """
    Given a database, collection name and a list or dictionary of ids, 
    fetches the corresponding labels from the database.

    Args:
    db (pymongo.database.Database): The database to fetch labels from.
    collection_name (str): The collection from which to fetch the labels.
    ids_input (list of str or dict of str: list of str): A list or dictionary where each value 
                                                         is a list of ids.

    Returns:
    list of str or dict of str: list of str: A list or dictionary where each key corresponds to a key from ids_input 
                                                   and each value is a list of 'label' values from the database for the corresponding ids.
    """
    query_options = {
        "projection": {"label": 1},
        "cursor_type": pymongo.CursorType.NON_TAILABLE,
        "max_time_ms": 5000
    }
    async def fetch_labels(names_input):
        # get labels from the cache
        names_input = list(set(names_input))
        # get results from cache
        cached_labels = await cache.cache_get_mutli_label_by_name(names_input)
        # check results from the cache 
        # diff cached and non cached label
        cached_labels_name, non_cached_labels = extract_cached_non_cached_labels(cached_labels, names_input)
    
        if not non_cached_labels:
            return cached_labels_name

        labels = []
        query = {}
        q_list = []
        for name in non_cached_labels:
            q_list.append(
                {
                    "label": { "$regex": name}
                }
            )
        query["$or"] = q_list
        batch_size = 100
        page = 1
        batch = []
        total = len(names_input)
        while True:
            cursor = db[collection_name].find(query, **query_options)
            batchKwargs = {
                "cursor": cursor,
                "page": page,
                "batch_size": batch_size
            }
            batch.append(asyncio.create_task(fetch_collection_data(**batchKwargs)))
            if (page * batch_size) >= total:
                break
            page += 1
        response = await asyncio.gather(*batch)
        labels_added_to_cache = []
        for non_cached_label in non_cached_labels:
            labels_to_cache = []
            for docList in response:
                for doc in docList:
                    if non_cached_label in doc["label"]:
                        labels_to_cache.append(doc)
                        labels_added_to_cache.append(doc["label"])
            # save results in the cache
            cache.cache_set_label_by_name(non_cached_label, labels_to_cache)
        for docList in response:
            for doc in docList:
                labels.append(doc['label'])
        
        # save empty results in the cache also
        labels_added_to_cache = list(set(labels_added_to_cache))
        if not any((non_cached_label := requested_name) not in labels_added_to_cache for requested_name in non_cached_labels):
            cache.cache_set_label_by_name(non_cached_label, [{"label": non_cached_label}])

        return labels + cached_labels_name

    # Initialize an empty dictionary to store the output labels
    labels_output = {}

    # Check if ids_input is a list of dictionaries
    if isinstance(names_input, list) and all(isinstance(d, dict) for d in names_input):
        for single_dict in names_input:
            for key, names_input in single_dict.items():
                labels_output[key] = await fetch_labels(names_input)
    elif isinstance(names_input, dict):
        labels_output = {key: await fetch_labels(names_input) for key, names_input in names_input.items()}
    elif isinstance(names_input, list):
        labels_output = await fetch_labels(names_input)
    else:
        raise TypeError("Invalid type for ids_input. Must be a dictionary or a list.")
    return labels_output

async def create_label_master_dict(db, collection_name, query, type):
    """
    Create a dictionary for labels and their master labels based on the given query.

    Args:
    db (pymongo.database.Database): The database to fetch labels from.
    collection_name (str): The collection from which to fetch the labels.
    query (dict): The query to be executed on the MongoDB collection.

    Returns:
    dict: A dictionary mapping labels to their master labels.
    """
    # get cache results base on type
    cache_label_master, non_cached_label_master, new_query = await cache.cache_get_label_master(query, type)
    # handle list cached for by_label
    if type == "by_label":
        dict_master_label = {}
        for cached_master_label in cache_label_master:
            dict_master_label.update(cached_master_label)
        cache_label_master = {k: v for k, v in dict_master_label.items() if v is not ("" or None)}
    if cache_label_master and not non_cached_label_master:
        return cache_label_master
    label_master_dict = {}
    try:
        # Add a debug print statement
        debug_print("Executing query...")
        
        # Define the query options (projection, cursor type, and max time)
        query_options = {
            "projection": {"label": 1, "master_label": 1},
            "group": {
                    "_id": "$master_label",
                    "labels": {
                        "$addToSet": "$label"
                    }
                }
        }
        
        # Another debug print statement
        print("MongoDB Query executed, processing results...")
        # Process the result from MongoDB query, paginating through cursor
        label_master_dict = dict()
        label_master_name = []
        label_groups = list(db[collection_name].aggregate([
            { "$match": new_query },
            { "$project": query_options["projection"] },
            { "$group": query_options['group'] }
        ]))
        for group in label_groups:
            for label in group['labels']:
                label_master_dict[label] = group['_id']
                label_master_name.append(label)
        # cache also empty results
        for non_cached in  non_cached_label_master:
            if non_cached not in label_master_name:
                label_master_dict[non_cached] = ""
        # cache all results
        cache.cache_set_label_master(label_master_dict, type)
        # Debug print statement indicating end of processing
        print("Results processed.")
    except PyMongoError as e:
        print(f"An error occurred while fetching or processing data from MongoDB: {e}")
    # add results from db and cache and remove empty results
    label_master_dict.update(cache_label_master)
    return {k: v for k, v in label_master_dict.items() if v != ""}

async def fetch_collection_data(**batchKwargs):
    cursor = batchKwargs['cursor']
    page = batchKwargs['page']
    batch_size = batchKwargs['batch_size']
    result = list(cursor.skip((page -  1) * batch_size).limit(batch_size))
    return result

def get_unique_labels(master_label_dict, labels):
    """
    Create a list or dictionary of unique labels based on the master_label_dict and labels.

    Args:
    master_label_dict (dict): A dictionary mapping labels to their master labels.
    labels (list or dict): The list or dictionary of label categories, which may include tuples.

    Returns:
    list or dict: A list or dictionary of unique labels.
    """

    # Function to process label list or list of tuples
    def process_labels(label_list):
        # If the input is a list of tuples, extract only the label strings
        if all(isinstance(item, tuple) for item in label_list):
            label_list = [label for label, _ in label_list]

        # Use the master label if it exists; otherwise, use the original label
        clustered_labels = [master_label_dict.get(label, label) for label in label_list]

        # Get unique labels by converting the list to a dictionary and back to a list
        uni_labels = list(dict.fromkeys(clustered_labels))
        return [uni_lab for uni_lab in uni_labels if type(uni_lab) is str]

    # If labels is a dictionary, process each category separately
    if isinstance(labels, dict):
        unique_labels_by_category = {category: process_labels(category_labels) for category, category_labels in labels.items()}
        return unique_labels_by_category

    # If labels is a list, process the whole list
    else:
        return process_labels(labels)

def combine_and_average(lists, weights):
    combined_dict = {}
    for i, sublist in enumerate(lists):
        for label, num, weight in sublist:
            list_weight = weights[i]
            if label not in combined_dict:
                combined_dict[label] = [num, weight * list_weight, 1]
            else:
                combined_dict[label][0] += num
                combined_dict[label][1] += weight * list_weight
                combined_dict[label][2] += 1

    averaged = []
    for label, values in combined_dict.items():
        avg_weight = values[1] / values[2]
        averaged.append((label, values[0], avg_weight))

    # Sort the 'averaged' list in descending order of average weight
    averaged.sort(key=lambda x: x[2], reverse=True)

    # Generate 'labels_only' from 'averaged' to ensure the same order
    labels_only = [item[0] for item in averaged]

    return averaged, labels_only

def apply_weights_to_labels(label_input, weight_dict_labels=None, start_weight=1.0, decay_rate=0.8, min_weight=0.01, equal_weighting=False):
    # print(f"Debug: label_input = {label_input}")
    # print(f"Debug: weight_dict_labels = {weight_dict_labels}")
    # print(f"Debug: equal_weighting = {equal_weighting}")    
    weighted_labels = []

    if equal_weighting:
        # Extract labels whether input is dict or list
        if isinstance(label_input, dict):
            for key in label_input:
                for label in label_input[key]:
                    weighted_labels.append(label)
        elif isinstance(label_input, list):
            weighted_labels.extend(label_input)
        
        # Determine the equal weight for each label
        num_labels = len(weighted_labels)
        equal_weight = 1.0 / num_labels if num_labels != 0 else 0

        # Assign the equal weight to each label
        weighted_labels = [(label, 1, equal_weight) for label in weighted_labels]
        return weighted_labels

    # Original logic
    if isinstance(label_input, dict):  # For dictionary input
        for key in label_input:
            # Get the start_weight and decay_rate for this key, or use a default if it's not defined
            key_start_weight, key_decay_rate = weight_dict_labels.get(key, (0.5, 0.05))  
            weight = key_start_weight
            for label in label_input[key]:
                # Prevent weight from dropping below min_weight
                weight = max(weight, min_weight)
                weighted_labels.append((label, 1, weight))
                # Decrease the weight for the next iteration
                weight = max(weight - key_decay_rate, min_weight)
    elif isinstance(label_input, list):  # For list input
        weight = start_weight
        for label in label_input:
            # Prevent weight from dropping below min_weight
            weight = max(weight, min_weight)
            weighted_labels.append((label, 1, weight))
            # Decrease the weight for the next iteration
            weight = max(weight - decay_rate, min_weight)

    # Normalize the weights so they sum to 1
    total_weight = sum(x[2] for x in weighted_labels)
    weighted_labels = [(x[0], x[1], x[2]/total_weight) for x in weighted_labels]

    # You could sort the labels here by weight if you want
    weighted_labels.sort(key=lambda x: x[2], reverse=True)
    return weighted_labels


def filter_master_label_counts_vs_AI_search_weights(master_label_counts, weight_tuples):
    filtered_master_label_counts_using_AI_dict = []
    for weight_tuple in weight_tuples:
        label = weight_tuple[0]  # Accessing the first element of the tuple
        # Check if the label is found in master_label_counts
        if label in master_label_counts:
            count = master_label_counts[label]  # Directly get the count as it's an integer
            filtered_master_label_counts_using_AI_dict.append({'label': label, 'reviews': count})
    
    filtered_master_label_counts_using_AI_dict_str = ' • '.join([f"{item['label']} ({item['reviews']})" for item in filtered_master_label_counts_using_AI_dict])
    return filtered_master_label_counts_using_AI_dict, filtered_master_label_counts_using_AI_dict_str


def extract_cached_non_cached_based_on_id(cached_brands, product_ids):
    cached_brands_ids = [doc["_id"] for doc in cached_brands]
    non_cached_brands = [_id for _id in product_ids if _id not in cached_brands_ids]
    return non_cached_brands

async def get_products_brands_by_ids(db, brand_ids):
    brand_collections=db["brands"]
    cached_brands = await cache.cache_get_multi_brands_by_id(brand_ids)
    cached_brands = [cached_brand for cached_brand in cached_brands if cached_brand is not None]
    non_cached_brands = extract_cached_non_cached_based_on_id(cached_brands, brand_ids)
    if not non_cached_brands:
        brands = {}
        for cached_brand in cached_brands:
            brands[str(cached_brand['_id'])] = cached_brand
        return brands

    response = brand_collections.find( 
        {
            "_id" :
                {
                    "$in" : [ObjectId(_id) for _id in non_cached_brands if ObjectId.is_valid(_id)]
                }
        }
    )
    brands = {}
    for docList in response:
        brands[str(docList['_id'])] = docList
        cache.cache_set_brand_by_id(docList["_id"], docList) 

    for cached_brand in cached_brands:
        brands[str(cached_brand['_id'])] = cached_brand
    return brands


async def get_refined_categories_master_categories(db, master_category_ids):
    master_category_collection=db["master_categories"]
    cached_master_categories = await cache.cache_get_multi_master_categories_by_id(master_category_ids)
    cached_master_categories = [cached_category for cached_category in cached_master_categories if cached_category is not None]
    non_cached_master_categories = extract_cached_non_cached_based_on_id(cached_master_categories, master_category_ids)
    if not non_cached_master_categories:
        master_categories = {}
        for cached_category in cached_master_categories:
            master_categories[str(cached_category['_id'])] = cached_category
        return master_categories

    response = master_category_collection.find( 
        {
            "_id" :
                {
                    "$in" : [ObjectId(_id) for _id in non_cached_master_categories if ObjectId.is_valid(_id)]
                }
        }
    )
    master_categories = {}
    for docList in response:
        master_categories[str(docList['_id'])] = docList
        cache.cache_set_refined_category_by_id(docList["_id"], docList) 

    for cached_category in cached_master_categories:
        master_categories[str(cached_category['_id'])] = cached_category
    return master_categories


async def get_products_refined_categories_by_ids(db, refined_ids):
    refined_collections=db["refined_categories"]
    cached_refined = await cache.cache_get_multi_refined_categories_by_id(refined_ids)
    cached_refined = [cached_refined for cached_refined in cached_refined if cached_refined is not None]
    non_cached_refined = extract_cached_non_cached_based_on_id(cached_refined, refined_ids)
    if not non_cached_refined:
        refined_categories = {}
        for cached_r in cached_refined:
            refined_categories[str(cached_r['_id'])] = cached_r
        return refined_categories

    response = refined_collections.find( 
        {
            "_id" :
                {
                    "$in" : [ObjectId(_id) for _id in non_cached_refined if ObjectId.is_valid(_id)]
                }
        }
    )
    refined_categories = {}
    master_categories_id = []
    for docList in response:
        refined_categories[str(docList['_id'])] = docList
        master_categories_id.append(docList["master_category_id"])
    if master_categories_id:
        master_categories = await get_refined_categories_master_categories(db, master_categories_id)

    for refined_id in refined_categories:
        refined_categories[refined_id]["master_category"] = master_categories.get(refined_categories[refined_id]["master_category_id"], {})
        cache.cache_set_refined_category_by_id(refined_id, refined_categories[refined_id]) 


    for cached_refined in cached_refined:
        refined_categories[str(cached_refined['_id'])] = cached_refined
    return refined_categories

async def add_metadata_to_products(db, products):
    brands, refined_categories = await asyncio.gather(
        *[
            get_products_brands_by_ids(db, list(set([products[_id]["brand"] for _id in  products]))),
            get_products_refined_categories_by_ids(db, list(set([products[_id]["refined_category"] for _id in  products]))),
        ]
    )
    for product in products:
        brand_id = products[product].get("brand", None)
        refined_category_id = products[product].get("refined_category", None)
        if brand_id:
            products[product]["brand"] = brands.get(products[product]["brand"], {})
        if refined_category_id:
            products[product]["refined_category"] = refined_categories.get(products[product]["refined_category"], {})

    return products

async def get_products(db, unique_prod_ids):
    collection = db['products']
    cached_documents = await cache.cache_get_multi_document_by_id(unique_prod_ids)
    cached_documents = [cached_document for cached_document in cached_documents if cached_document is not None]
    non_cached_documents = extract_cached_non_cached_docs(cached_documents, unique_prod_ids, "_id")
    if not non_cached_documents:
        products = {}
        for cached_doc in cached_documents:
            products[str(cached_doc['_id'])] = cached_doc
        return await add_metadata_to_products(db, products)
    
    query_options = {
        "projection": {"img": 1, "title": 1, "price": 1, "brand": 1, "refined_category" :1},
        "cursor_type": pymongo.CursorType.NON_TAILABLE,
        "max_time_ms": 5000
    }
    products = {}
    query = {
        '_id': {
            '$in': [ObjectId(id) for id in non_cached_documents]
        }
    }
    batch_size = 100
    page = 1
    batch = []
    total = len(unique_prod_ids)
    while True:
        cursor = collection.find(query, **query_options)
        batchKwargs = {
            "cursor": cursor,
            "page": page,
            "batch_size": batch_size
        }
        batch.append(asyncio.create_task(fetch_collection_data(**batchKwargs)))
        if (page * batch_size) >= total:
            break
        page += 1
    response = await asyncio.gather(*batch)
    # saves 5 seconds
    for docList in response:
        for doc in docList:
            products[str(doc['_id'])] = doc
            cache.cache_set_document_by_id(doc["_id"], doc)
    # add cached docs
    for cached_doc in cached_documents:
        products[str(cached_doc['_id'])] = cached_doc
    # get products brands
    return await add_metadata_to_products(db, products)

def extract_cached_non_cached_docs(cached_documents, unique_prod_ids, key):
    cached_documents_ids = [doc[key] for doc in cached_documents]
    non_cached_documents = [_id for _id in unique_prod_ids if _id not in cached_documents_ids]
    return non_cached_documents

async def retrieve_documents_summary(collection, unique_prod_ids):
    # get results from the cache
    cached_documents = await cache.cache_get_multi_document_summary_by_id(unique_prod_ids)
    cached_documents = [cached_document for cached_document in cached_documents if cached_document is not None]
    # get cached and non cached documents
    non_cached_documents_id = extract_cached_non_cached_docs(cached_documents, unique_prod_ids, "prod_id")
    
    if not non_cached_documents_id:
        return {doc['prod_id']: doc for doc in cached_documents}

    query_options = {
        "projection": {"skin_type.positive_labels.review_ids": 0, "skin_type.positive_labels.master_label": 0, "skin_type.positive_labels.weight": 0, 
                       "skin_type.positive_labels_count": 0, "skin_type.positive_labels_clustered": 0},
        "cursor_type": pymongo.CursorType.NON_TAILABLE,
        "max_time_ms": 5000
    }
    labels = []
    query = {
        'prod_id': {
            '$in': non_cached_documents_id
        }
    }
    batch_size = 100
    page = 1
    batch = []
    total = len(unique_prod_ids)
    while True:
        cursor = collection.find(query, **query_options)
        batchKwargs = {
            "cursor": cursor,
            "page": page,
            "batch_size": batch_size
        }
        batch.append(asyncio.create_task(fetch_collection_data(**batchKwargs)))
        if (page * batch_size) >= total:
            break
        page += 1
    response = await asyncio.gather(*batch)
    # saves 5 seconds
    for docList in response:
        for doc in docList:
            labels.append(doc)
            # save results in the cache
            await cache.cache_set_document_summary_by_id(doc["prod_id"], doc)

    labels += cached_documents
    return  {doc['prod_id']: doc for doc in labels}
    # return {doc['prod_id']: doc for doc in collection.find({'prod_id': {'$in': unique_prod_ids}})}

############################ Weight application to labels & using AI to extract most relevant labels after MongoDB retrieval ##########################################

async def define_parameters_and_rerank_labels(db):
    """
    Define search parameters and rerank labels based on a database query.
    
    This function performs the following operations:
    1. Calls the create_label_master_dict function to build a master label dictionary from the database.
    2. Creates a unique list of master labels to be used later for ranking and filtering.
    
    Args:
        db: The database connection object.
        
    Returns:
        Tuple containing:
        - Dictionary of master labels mapped from the database ('master_label_dict').
        - List of unique master labels ('unique_master_labels').
    """
    
    # Create a master label dictionary from the database
    master_label_dict = await create_label_master_dict(
        db,
        'positive_labels',
        {
            "master_label": {"$not": {"$eq": np.nan}, "$exists": True, "$ne": None},
            "label": {"$exists": True, "$ne": None},
        },
        "all"
        )
    
    # Create a unique list of master labels
    unique_master_labels = list(set(master_label_dict.values()))

    return master_label_dict, unique_master_labels

async def process_label_name_list(db, labels_name, master_label_dict, unique_master_labels):
    # Get labels corresponding by name
    filtered_labels = await get_labels_from_name(db, 'positive_labels', labels_name)
    master_label_dict_label_search_query = []
    if len(filtered_labels):
        master_label_dict_label_search_query = await create_label_master_dict(db, 'positive_labels', {"label": {"$in": filtered_labels}}, "by_label")
    
    # Obtain unique labels from search query
    unique_labels_search_query = get_unique_labels(master_label_dict_label_search_query, filtered_labels)

    # Filter out unique labels that exist in unique_master_labels
    search_query_labels_in_master_label_dict = [label for label in unique_labels_search_query if label in unique_master_labels]

    return unique_labels_search_query, search_query_labels_in_master_label_dict


def perform_fuzzy_matching_for_attributes(search_query_dict, filtered_labels, master_label_dict, threshold=90):
    """
    Perform fuzzy matching on search query parameters to obtain relevant labels.

    This function takes a dictionary of search query parameters, a list of filtered labels,
    and a master label dictionary. It performs fuzzy matching to find the most relevant labels
    for each attribute in the search query.

    Steps:
    1. Iterates through each attribute-value pair in the search query dictionary.
    2. Performs fuzzy matching to find relevant labels for each attribute.
    3. Aggregates all the fuzzy-matched labels.2
    4. Calculates the master labels based on the aggregated list.

    Args:
        search_query_dict (dict): Dictionary containing search query parameters as keys and values.
        filtered_labels (list): List of pre-filtered labels to be matched.
        master_label_dict (dict): Master dictionary containing label mappings.
        threshold (int, optional): Minimum score for a label to be considered a match. Defaults to 90.

    Returns:
        Tuple containing:
        - Dictionary containing the fuzzy-matched labels for each attribute.
        - Aggregated list of all fuzzy-matched labels across attributes.
        - Master labels calculated based on the fuzzy-matched labels.
    """

    # Initialize dictionary to hold matched labels for each attribute
    results = {}
    
    # Initialize list to hold all labels matched across all attributes
    all_matched_labels = []

    def process_single_dict(search_query_dict):
        nonlocal results
        nonlocal all_matched_labels
        for attribute, value in search_query_dict.items():
            # Skip attributes if they're None or empty
            if not value:
                continue

            # Make sure the value is in list form to allow multi-string comparisons
            if not isinstance(value, list):
                value = [value]

            # Perform fuzzy matching to find labels that match with the current attribute
            label_list_fuzzy_matched_with_attribute = get_fuzzy_scores(value, filtered_labels, min_score=threshold)
            
            # Keep only labels with a match score greater than the threshold
            label_list_fuzzy_matched_with_attribute = [label for label, score in label_list_fuzzy_matched_with_attribute.items() if score > threshold]
            
            # Save the matched labels for the current attribute
            if attribute in results:
                results[attribute].extend(label_list_fuzzy_matched_with_attribute)
            else:
                results[attribute] = label_list_fuzzy_matched_with_attribute

            # Add the matched labels for the current attribute to the aggregated list
            all_matched_labels.extend(label_list_fuzzy_matched_with_attribute)

    if isinstance(search_query_dict, dict):
        process_single_dict(search_query_dict)
    elif isinstance(search_query_dict, list) and all(isinstance(d, dict) for d in search_query_dict):
        for single_dict in search_query_dict:
            process_single_dict(single_dict)
    else:
        raise TypeError("Invalid type for search_query_input. Must be a dictionary or a list of dictionaries.")
    
    # Deduplicate any duplicate labels in the results or all_matched_labels lists
    results = {k: list(set(v)) for k, v in results.items()}
    all_matched_labels = list(set(all_matched_labels))

    # Calculate master labels based on the aggregated list of matched labels
    _, label_list_most_relevant_to_search_concerns_master_labels = get_mapped_labels(all_matched_labels, master_label_dict)
    
    return results, all_matched_labels, label_list_most_relevant_to_search_concerns_master_labels


def get_weighted_unique_list(search_query_master_label_list,
                             search_query_params_fuzzy_master_labels):
    
    # The set ensures uniqueness
    seen = set()
    
    # Prioritized order
    final_list = []
    
    # Process search_query_master_label_dict first
    for item in search_query_master_label_list:
        if item not in seen:
            seen.add(item)
            final_list.append(item)
    
    # Finally, process search_query_params_fuzzy_master_labels
    for item in search_query_params_fuzzy_master_labels:
        if item not in seen:
            seen.add(item)
            final_list.append(item)
            
    return final_list



def multi_method_weighting(
    # Predefined dictionary of master labels retrieved from the database
    master_label_dict, 
    
    # Labels derived from the search query
    search_query_params_fuzzy_labels, 
    search_query_labels_in_master_label_dict, 
    search_query_param_labels_in_master_label_dict,
    
    # Dictionary returned from openAI 
    search_query_dict_final, 

    # Dictionary of labels used to weight search_query_param_labels_in_master_label_dict
    weight_dict_labels=None
):    
    # print("Debugging: weight_dict_labels =", weight_dict_labels)
    """
    Aggregates labels and their weights based on various sources related to the search query.
    
    This function uses three lists of labels: 
    - Fuzzy matched labels from search query parameters.
    - Directly matched labels from the search query.
    - Labels matched from each search query parameter.
    
    It performs several steps to calculate the final list of weighted labels:
    1. Retrieves the weights and master labels for fuzzy matched labels.
    2. Applies a decay function to the weights of labels.
    3. Assigns equal weights to labels directly related to the search query.
    4. Applies different decay functions to weights of labels from search query parameters.
    5. Combines and averages the weights of all labels.
    
    Args:
        master_label_dict (dict): Master dictionary containing label mappings.
        search_query_params_fuzzy_labels (list): Fuzzy matched labels related to the search query parameters.
        search_query_labels_in_master_label_dict (list): Labels directly matched to the search query.
        search_query_param_labels_in_master_label_dict (list): Labels matched to each search query parameter.
        
    Returns:
        Tuple containing:
        - Dictionary of master labels and their corresponding weighted average.
        - List of master labels best related to the search query.
    """    

    # 1. If weight_dict_labels is not provided, create a default one with equal weights for each key in search_query_dict_final
    if weight_dict_labels is None:
        print(f"weight dict labels is none")
        if isinstance(search_query_dict_final, dict):  # Handle single dictionary
            weight_dict_labels = {key: (1.0, 0.0) for key in search_query_dict_final.keys()}
        elif isinstance(search_query_dict_final, list) and all(isinstance(d, dict) for d in search_query_dict_final):  # Handle list of dictionaries
            weight_dict_labels = {key: (1.0, 0.0) for single_dict in search_query_dict_final for key in single_dict.keys()}
        else:
            raise TypeError("Invalid type for search_query_dicts_final. Must be a dictionary or a list of dictionaries.")

    # 2. Get weights and master labels 
    search_query_params_fuzzy_labels_weights, _ = get_mapped_labels(search_query_params_fuzzy_labels, master_label_dict)
    debug_print(f"search_query_params_fuzzy_labels_weights: {search_query_params_fuzzy_labels_weights}")

    # 3. Apply a decay function to the weights of labels. For labels directly related to the search query, we're just applying equal weighting, as these labels should be quite synonymous
    search_query_master_labels_weights_based_on_search_query_decayed = apply_weights_to_labels(
        search_query_labels_in_master_label_dict[:10], equal_weighting=True # apply equal weighting 
    )
    debug_print(f"search_query_master_labels_weights_based_on_search_query_decayed: {search_query_master_labels_weights_based_on_search_query_decayed}")

    # 4. Apply a decay function to the weights of labels. For the search query parameter dictionary, we'll apply the weights in weight_dict_labels. This is because there might be a few things we want to weight more
    search_query_master_labels_weights_based_on_search_query_params_decayed = apply_weights_to_labels(
        search_query_param_labels_in_master_label_dict, weight_dict_labels
    )
    debug_print(f"search_query_master_labels_weights_based_on_search_query_params_decayed: {search_query_master_labels_weights_based_on_search_query_params_decayed}")

    # 5. Combine and average the weights using a decayed weight
    search_query_param_master_labels_weights, search_query_param_master_labels = combine_and_average(
        [search_query_params_fuzzy_labels_weights, search_query_master_labels_weights_based_on_search_query_decayed, search_query_master_labels_weights_based_on_search_query_params_decayed], 
        [1, 1.25, 3]  # fixed predefined weights for each list
    )
    
    # Get final_list which uses the function get_weighted_unique_list
    # Step 1: Generate final_list
    final_list = get_weighted_unique_list(
        search_query_param_master_labels,
        search_query_param_labels_in_master_label_dict,
        search_query_params_fuzzy_labels
    )

    # Step 2: Assign New Weights Based on Order in final_list
    new_weights = {}
    max_weight = len(final_list)
    for i, label in enumerate(final_list):
        new_weights[label] = max_weight - i  # You can also use other decaying functions

    # Step 3: Combine Weights
    for i, (label, _, old_weight) in enumerate(search_query_param_master_labels_weights):
        new_weight = new_weights.get(label, 0)  # get the new weight, or 0 if label not in final_list
        combined_weight = (old_weight + new_weight) / 2  # averaging old and new weights
        search_query_param_master_labels_weights[i] = (label, new_weight, combined_weight)

    # Sort based on the updated combined weights
    search_query_param_master_labels_weights.sort(key=lambda x: x[2], reverse=True)

    # Extract only the labels to return in search_query_param_master_labels
    search_query_param_master_labels = [label for label, _, _ in search_query_param_master_labels_weights]

    return search_query_param_master_labels_weights, search_query_param_master_labels


def final_search_query_parameters(search_query, search_query_param_master_labels, search_query_master_labels_weights, master_label_dict, search_query_master_labels, labels, label_count=5):
    """
    Extracts and returns relevant search query parameters using AI.

    Parameters:
    - search_query (str): The search query string.
    - search_query_param_master_labels (list): Master labels specifically for search query parameterization.
    - search_query_master_labels_weights (list): List of master labels with their respective weights.
    - master_label_dict (dict): Dictionary mapping master labels to original labels.
    - search_query_master_labels (list): List of master labels extracted from search queries.
    - labels (list): Labels for skincare types.
    - label_count (int): Number of labels to return, defaults to 5.

    Returns:
    tuple: Contains the following 3 items.
    - master_labels_extracted_using_AI (list): Master labels extracted using AI from the final list.
    - final_labels_extracted_using_AI_weights (list): Extracted labels with normalized weights.
    - original_labels_search_dict_using_AI (dict): Dictionary of original labels based on extracted master labels.

    """
    
    # Use openAI to extract the master labels from the final list
    master_labels_extracted_using_AI = extract_master_labels_using_openAI(search_query, search_query_param_master_labels, label_count)

    # Filter labels to those extracted using AI and their corresponding weights
    final_labels_extracted_using_AI_weights = [item for item in search_query_master_labels_weights if item[0] in master_labels_extracted_using_AI]

    # Normalize weights of the final labels
    total_weight = sum([weight[2] for weight in final_labels_extracted_using_AI_weights])
    for i, item in enumerate(final_labels_extracted_using_AI_weights):
        label, count, weight = item
        normalized_weight = weight / total_weight
        final_labels_extracted_using_AI_weights[i] = (label, count, normalized_weight)

    # Map the final labels to their original labels
    original_labels_search_dict_using_AI = get_original_labels_for_master_labels(final_labels_extracted_using_AI_weights, master_label_dict)

    return master_labels_extracted_using_AI, final_labels_extracted_using_AI_weights, original_labels_search_dict_using_AI


############################ Retreival and re-ranking of products from MongoDB ##########################################


# Initialize Variables:
def initialize():
    # print(f"search_query_master_labels_weights: {search_query_master_labels_weights}")
    # print(f"final_labels_extracted_using_AI: {final_labels_extracted_using_AI}")
    labels_in_doc = []  
    total_label_counts = defaultdict(int)
    product_data_with_relevance = []  
    return labels_in_doc, total_label_counts, product_data_with_relevance

def extract_id_and_document(product_metadata, docs_dict):
    # id = product_metadata['metadata'].get('_id', None)
    id = product_metadata['id']
    if id is None:
        debug_print("Warning: Missing '_id' in product_metadata")
        return None, None
    
    doc = docs_dict.get(id, None)
    if doc is None:
        debug_print(f"Warning: ID '{id}' not found in docs_dict")
    
    debug_print(f"Debug: ID = {id}, Doc = {doc}")  # remove this line once debugging is done
    return id, doc

def extract_id_and_prodcut(product_metadata, product):
    # id = product_metadata['metadata'].get('_id', None)
    id = product_metadata['id']
    if id is None:
        debug_print("Warning: Missing '_id' in product_metadata")
        return None, None
    
    doc = product.get(id, None)
    if doc is None:
        debug_print(f"Warning: ID '{id}' not found in docs_dict")
    
    debug_print(f"Debug: ID = {id}, Doc = {doc}")  # remove this line once debugging is done
    return id, doc


def get_skin_type_overviews(doc):
    skin_type_overviews = {}
    for item in doc['skin_type']:
        name = item.get('name', 'N/A')
        positive_labels_aggregated = {}
        for label_item in item.get('positive_labels', []):
            label_name = label_item.get('label', 'N/A')
            reviews_count = label_item.get('reviews', 0)
            positive_labels_aggregated[label_name] = reviews_count
        skin_type_overviews[name] = positive_labels_aggregated
    return skin_type_overviews

def calculate_master_label_counts(positive_labels_in_doc, master_label_dict, total_label_counts=None):
    master_label_counts, master_label_counts_str = get_master_label_counts(positive_labels_in_doc, master_label_dict)
    
    if total_label_counts is not None:
        for label, count in master_label_counts.items():
            total_label_counts[label] += count
        return master_label_counts, total_label_counts, master_label_counts_str
    else:
        return master_label_counts, master_label_counts_str

 
def get_product_review_overviews(doc, master_label_dict):
    skin_type_overview = [item for item in doc['skin_type'] if item.get('name') == 'overview']
    positive_labels_list = skin_type_overview[0].get('positive_labels', []) if skin_type_overview else []

    # Convert list of dictionaries to dictionary of dictionaries
    positive_labels_in_doc = {item['label']: item for item in positive_labels_list}

    overview_str = " • ".join([f"{label} ({details['reviews']})" for label, details in positive_labels_in_doc.items()])
    master_label_counts, master_label_counts_str = calculate_master_label_counts(positive_labels_in_doc, master_label_dict)
    sorted_positive_labels_in_doc = dict(sorted(positive_labels_in_doc.items(), key=lambda item: item[1]['reviews'], reverse=True))

    return positive_labels_in_doc, overview_str, master_label_counts, master_label_counts_str, sorted_positive_labels_in_doc


def labels_fuzzy_after_cosine(search_query, id_label_list, positive_labels_in_doc):
    lower_label_set = {label.lower() for _, label in id_label_list}
    sorted_labels = sorted((label_dict for label_dict in positive_labels_in_doc if label_dict['label'].lower() in lower_label_set), key=lambda x: x['reviews'], reverse=True)
    cosine_id_label_list_to_product_labels = [label_dict['label'] for label_dict in sorted_labels]
    fuzzy_scores_after_cosine_matching_available_cosine_id_label_list = get_fuzzy_scores(search_query, cosine_id_label_list_to_product_labels)
    fuzzy_scores_after_cosine_matching_available_cosine_id_label_list = [label for label, score in fuzzy_scores_after_cosine_matching_available_cosine_id_label_list.items() if score > 80]
    return cosine_id_label_list_to_product_labels, fuzzy_scores_after_cosine_matching_available_cosine_id_label_list

def get_relevance_score_with_boost(base_relevance_score, total_boost_v2):
    return base_relevance_score + total_boost_v2

def get_relevent_summary(docs_summary_dict, id):
    # for each element in docs_summary get only {_id, insights}
    # print('sum', docs_summary_dict)
    if id in docs_summary_dict:
        init_capture = docs_summary_dict[id]
        sum_data = {
            "_id": init_capture["_id"] if init_capture["_id"] else '',
            "insights": init_capture["insights"] if init_capture["insights"] else [],
        }
        return sum_data
    else: 
        fail_data = {
            '_id': '',
            "insights": []
        } 
        return fail_data

async def process_product(product_metadata, docs_summary_dict, products, final_labels_extracted_using_AI, search_query_dict_final, master_label_dict, top_3_reviews=None):  

    _, doc_summary = extract_id_and_document(product_metadata, docs_summary_dict)
    _id, product = extract_id_and_prodcut(product_metadata, products)
    # add product details to product_metadata
    # product_metadata is the response from Pinecone
    # product is the response from mongodb
    if _id and product:
        refined_category = product.get("refined_category", {})
        product_metadata["_id"] = _id
        product_metadata["title"] = product.get("title", "")
        product_metadata["price"] = product.get("price", "")
        product_metadata["price"] = product.get("price", "")
        product_metadata["brand"] = product.get("brand", {}).get("brand", "")
        product_metadata["refined_category"] = refined_category.get("refined_category", "")
        product_metadata["master_category"] = refined_category.get("master_category", {}).get("master_category", "")
        product_metadata["img"] = product.get('img', '')
        product_metadata["pl_summary"] = get_relevent_summary(docs_summary_dict, _id)


    if not doc_summary:
        return None

    # Code is mainly using data from MongoDB collection product_review_summaries

    def get_total_product_reviews(doc):
        reviews_count = doc.get('total_reviews', 0)
        return reviews_count

    def get_overview_labels(doc, master_label_dict): 
        skin_type_overviews = get_skin_type_overviews(doc) 
        positive_labels_in_doc, overview_str, master_label_counts, master_label_counts_str, sorted_positive_labels_in_doc = get_product_review_overviews(doc, master_label_dict)
        return skin_type_overviews, overview_str, positive_labels_in_doc, master_label_counts, master_label_counts_str, sorted_positive_labels_in_doc

    def get_AI_extracted_labels(master_label_counts, final_labels_extracted_using_AI):
        filtered_master_label_counts_using_AI_dict, filtered_master_label_counts_using_AI_dict_str = filter_master_label_counts_vs_AI_search_weights(master_label_counts, final_labels_extracted_using_AI)
        return filtered_master_label_counts_using_AI_dict, filtered_master_label_counts_using_AI_dict_str

    def calculate_relevance_scores(sorted_positive_labels_in_doc, reviews_count, filtered_master_label_counts_using_AI_dict):
        base_relevance_score = calculate_base_relevance_score(sorted_positive_labels_in_doc, reviews_count)
        total_boost_v2 = calculate_total_boost(filtered_master_label_counts_using_AI_dict, reviews_count, final_labels_extracted_using_AI)
        relevance_score_with_boost = get_relevance_score_with_boost(base_relevance_score, total_boost_v2)
        return relevance_score_with_boost

    reviews_count = get_total_product_reviews(doc_summary)
    skin_type_overviews, overview_str, positive_labels_in_doc, master_label_counts, master_label_counts_str, sorted_positive_labels_in_doc = get_overview_labels(doc_summary, master_label_dict)
    filtered_master_label_counts_using_AI_dict, filtered_master_label_counts_using_AI_dict_str = get_AI_extracted_labels(master_label_counts, final_labels_extracted_using_AI)
    relevance_score_with_boost = calculate_relevance_scores(sorted_positive_labels_in_doc, reviews_count, filtered_master_label_counts_using_AI_dict) 
    # title_boost = TitleBooster.get_title_boost(product_metadata, search_query_dict_final)
    # print(f'Title Boost: {title_boost}')
    # category_boost = CategoryBooster.get_category_boost(product_metadata, search_query_dict_final)
    # print(f'Category Boost: {category_boost}')
    # final_relevance_score = relevance_score_with_boost + title_boost + category_boost
    # print(f'Score before Title and Category Boost: {relevance_score_with_boost}')
    # print(f'Score after Title and Category Boost: {final_relevance_score}')

    if top_3_reviews is None:
        top_3_reviews = "top 3 reviews have not been searched for or specified"

    return {
        'product_metadata': product_metadata, #dictionary of dictionaries
        'reviews_count': reviews_count, #float
        'top_3_reviews': top_3_reviews, #dictionary of dictionaries
        # 'relevance_score': final_relevance_score, #float
        'relevance_score_with_boost': relevance_score_with_boost, #float
        'skin_type_overviews': skin_type_overviews, #dictionary of dictionaries
        'overview_str': overview_str, #string
        'positive_labels_in_doc': positive_labels_in_doc, #list of dictionaries
        'master_label_counts': master_label_counts, #string 
        'master_label_counts_str': master_label_counts_str, #string 
        'filtered_master_label_counts_using_AI_dict_str': filtered_master_label_counts_using_AI_dict_str, #string
    }

def rerank_products(product_data_with_relevance):
    return sorted(product_data_with_relevance, key=lambda x: x['relevance_score'], reverse=True)


############################ Cleanup and displaying of data ##########################################

def format_date_difference(start_date, end_date):
    """Format the difference between two dates in terms of days, months, or years."""
    delta = end_date - start_date
    days = delta.days
    
    if days < 30:
        return f"{days} days ago"
    elif days < 365:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


def extract_sorted_labels(data_str, max_labels=5):
    labels = data_str.split(' • ')
    label_counts = [(label, int(label.split(' ')[-1].replace('(', '').replace(')', '')))
                    for label in labels if label.split(' ')[-1].replace('(', '').replace(')', '').isdigit()]
    return ', '.join(label for label, _ in sorted(label_counts, key=lambda x: x[1], reverse=True)[:max_labels])

def get_match_ratio(concern, review_text):
    return fuzz.token_set_ratio(concern.lower(), review_text)
    
def extract_product_data(metadata):
    # Check if metadata is a tuple
    if isinstance(metadata, tuple):
        metadata = metadata[0]  # Access the first element (the actual metadata)
    
    # Check if metadata contains the 'metadata' key
    if 'metadata' in metadata:
        metadata = metadata['metadata']
        
    return {
        'product_id': metadata.get('_id', 'N/A'),
        'brand': metadata.get('brand', 'N/A'),
        'title': metadata.get('title', 'N/A'),
        'master_category': metadata.get('master_category', 'N/A'),
        'refined_category': metadata.get('refined_category', 'N/A'),
        'price': metadata.get('price', 'N/A'),
        'img': metadata.get('img', 'N/A'),
        'pl_summary': metadata.get('pl_summary', 'N/A')
    }



def process_reviews(top_3_reviews, search_query_dict_final):
    def process_single_dict(single_dict):
        local_matched_skin_concerns = []
        local_reviews_with_match_ratios = []

        for _, review in top_3_reviews.items():
            review_text = review['desc']
            match_ratio = 0
            
            for concern in single_dict.get('skin_concern', []):
                current_ratio = get_match_ratio(concern, review_text)
                if current_ratio > 80:
                    if current_ratio > match_ratio:
                        match_ratio = current_ratio
                        local_matched_skin_concerns.append(concern)
                        
            local_reviews_with_match_ratios.append((review, match_ratio))
        
        return local_matched_skin_concerns, sorted(local_reviews_with_match_ratios, key=lambda x: x[1], reverse=True)

    matched_skin_concerns = []
    reviews_with_match_ratios = []
    
    if isinstance(search_query_dict_final, dict):
        matched_skin_concerns, reviews_with_match_ratios = process_single_dict(search_query_dict_final)
    elif isinstance(search_query_dict_final, list) and all(isinstance(d, dict) for d in search_query_dict_final):
        for single_dict in search_query_dict_final:
            local_matched_skin_concerns, local_reviews_with_match_ratios = process_single_dict(single_dict)
            matched_skin_concerns.extend(local_matched_skin_concerns)
            reviews_with_match_ratios.extend(local_reviews_with_match_ratios)
        
        # Sort again if we had multiple dictionaries
        reviews_with_match_ratios = sorted(reviews_with_match_ratios, key=lambda x: x[1], reverse=True)
    else:
        print("Invalid input type.")
    
    return matched_skin_concerns, reviews_with_match_ratios

def print_review(idx, review):
    metadata = review['metadata']
    debug_print(f"Review {idx+1} (Score: {review['custom_score']}, Matched Data: {review['matched_data']}):")
    debug_print(f"Title: {metadata.get('title', 'N/A')}")
    debug_print(f"Description: {metadata.get('desc', 'N/A')}")
    debug_print(f"Name: {metadata.get('name', 'N/A')} | Age: {metadata.get('age', 'N/A')} | Country: {metadata.get('country', 'N/A')}")
    debug_print(f"Skin Concern: {metadata.get('skin_concern', 'N/A')} | Skin Tone: {metadata.get('skin_tone', 'N/A')} | Skin Type: {metadata.get('skin_type', 'N/A')}")
    debug_print(f"Rating: {metadata.get('rating', 'N/A')} | Promoted: {metadata.get('promoted', 'N/A')}\nPosted: {metadata.get('created_at', 'N/A')}")

# Check if 'created_at' is a string or a datetime.datetime object
    created_at = metadata.get('created_at', 'N/A')
    if isinstance(created_at, str):
        created_at_date = datetime.strptime(created_at, "%Y-%m-%d").date()  # Adjust the format if needed
    elif isinstance(created_at, datetime):
        created_at_date = created_at.date()
    else:
        created_at_date = None
    
    if created_at_date:
        debug_print(f"Posted: {format_date_difference(created_at_date, date.today())}\n")
    else:
        debug_print(f"Posted: N/A\n")

def print_product_data(data):
    debug_print(f"Original relevance score: {data['relevance_score'] - (0.1 * len(set(data['matched_skin_concerns'])) + (1 if data['matched_skin_concerns'] else 0))}")
    debug_print(f"Updated relevance score: {data['relevance_score']}")
    debug_print(f"Product ID: {data['product_id']}")
    debug_print(f"Product: {data['brand']} {data['title']} (Reviews: {data['reviews_count']})")  # Inserted reviews_count here
    debug_print(f"Category: {data['refined_category']}, {data['master_category']} | Price: ${data['price']}")
    debug_print(f"Matched product labels to search query: {data['filtered_master_label_counts_using_AI_dict_str']}")
    debug_print(f"Matched skin concern to review: {data['matched_skin_concerns']}")
    # debug_print(f"Top Features: {data['top_5_master_labels']}")
    debug_print(f"Most Relevant Reviews:")
    
    for idx, (review, _) in enumerate(data['sorted_top_3_reviews']):
        print_review(idx, review)
    debug_print("\n====================\n")

def getList_Productdata(data, is_reviews_included = False):
    rating_rating_dict = []
    if is_reviews_included:
        for key, review in data['reviews'].items():
            rating_rating_dict.append(
                {
                    "rating": review['rating'], 
                    "review": review['desc']
                }
            )

    return {
        "product_id": data['product_id'],
        "brand": data['brand'],
        "title": data['title'],
        "reviews_count": data['reviews_count'],
        "relevancy_score": data['relevance_score'],
        "original_relevancy_score": data['relevance_score'],
        "refined_category":data['refined_category'],
        "master_category": data['master_category'],
        "price": data['price'],
        "top_master_labels": data['top_master_labels'],
        "top_overview_labels": data['top_overview_labels'],
        "filtered_master_label_counts_using_AI_dict_str": data["filtered_master_label_counts_using_AI_dict_str"],
        "reviews": rating_rating_dict,
    }
