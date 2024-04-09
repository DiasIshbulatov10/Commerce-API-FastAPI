from fuzzywuzzy import fuzz

# Set this flag to True to enable debugging or False to disable debugging.
DEBUG_FLAG = False

def debug_print(*args, **kwargs):
    if DEBUG_FLAG:
        print(*args, **kwargs)

# Function to compute the similarity between two strings a and b.
def similarity(a, b):
    return fuzz.token_set_ratio(a, b) / 100

# Custom sorting function
def custom_sort(x):
    if x is None:
        return (0, 0)  # Lowest priority for None
    relevant_to_you_str = x.get('filtered_master_label_counts_using_AI_dict_str', 'N/A')
    has_relevant_data = 1 if relevant_to_you_str and relevant_to_you_str != 'N/A' else 0
    return (has_relevant_data, x.get('relevance_score', 0))


# Handle the comparison logic for price.
def handle_price(matching_fields, matched_data, value, metadata):
    metadata_price = float(metadata.get('price', 0))
    lower_bound, upper_bound = value
    
    debug_print(f"Debug - Price criteria: Lower Bound = {lower_bound}, Upper Bound = {upper_bound}")  # Debug line
    debug_print(f"Debug - Metadata Price: {metadata_price}")  # Debug line

    if (lower_bound is not None and metadata_price < lower_bound) or \
       (upper_bound is not None and metadata_price > upper_bound):
        debug_print("Debug - Price does not meet the criteria")  # Debug line
        return -1, {}
    else:
        debug_print("Debug - Price meets the criteria")  # Debug line
        return matching_fields, matched_data

# Handle the string matching for various fields.
def handle_string_match(matching_fields, matched_data, key, value, metadata_value, threshold, weight=1):
    # Handling list-to-list comparisons, like 'skin_concern' to 'skin_concern'.
    if isinstance(value, list) and isinstance(metadata_value, list):
        seq_match_ratio = len(set(value).intersection(set(metadata_value))) / len(value)
    # Handling single value to list or list to single value comparisons.
    elif isinstance(value, list) or isinstance(metadata_value, list):
        seq_match_ratio = 0
    # Handling string-to-string comparisons, like 'product_name' to 'product'.
    else:
        seq_match_ratio = similarity(str(value).lower(), metadata_value.lower())

    # Update if similarity meets the threshold.
    if seq_match_ratio >= threshold:
        matching_fields += weight
        matched_data[key] = value
        
    return matching_fields, matched_data

# Main function to calculate a custom score for a match.
def custom_score(match, search_query_JSON_list=None, seq_match_threshold=0.7, 
                 productname_weight=1, producttype_weight=1, skintone_weight=1):
    
    if search_query_JSON_list is None:
        search_query_JSON_list = []
        
    # Key mapping from search query keys to metadata keys.
    key_mapping = {
        "skin_tone": ["skin_tone"],
        "skin_concern": ["skin_concern"],
        "skin_type": ["skin_type"],
        "country": ["country"],
        "age_group": ["age"]
    }
    
    # Debug: Print initial states.
    debug_print(f"Initial Search Query JSON List: {search_query_JSON_list}")  # Debug line
    debug_print(f"Initial Key Mapping: {key_mapping}")  # Debug line
    
    # Convert metadata keys to lower case for consistent comparison.
    metadata = {k.lower(): v for k, v in match["metadata"].items()}
    
    matching_fields = 0
    matched_data = {}
    
    # Loop through each dictionary in the list
    for query_dict in search_query_JSON_list:
        # Loop through each key-value pair in each dictionary
        for key, value in query_dict.items():
            debug_print(f"Processing key: {key}")  # Debug line
            metadata_keys = key_mapping.get(key, [key])
            
            for metadata_key in metadata_keys:
                if metadata_key not in metadata:
                    debug_print(f"Metadata key {metadata_key} not found in metadata.")  # Debug line
                    continue
                
                debug_print(f"Comparing {key}: {value} with metadata_key: {metadata_key}, metadata_value: {metadata[metadata_key]}")  # Debug line
                
                if key == "price":
                    matching_fields, matched_data = handle_price(
                        matching_fields, matched_data, value, metadata)
                else:
                    # For all other keys, we use the same logic.
                    matching_fields, matched_data = handle_string_match(
                        matching_fields, matched_data, key, value, metadata.get(metadata_key, ''),
                        seq_match_threshold)
                        
    # Calculate and return final score.
    final_score = match["score"] + matching_fields if match["score"] is not None else 0
    return final_score, matched_data
