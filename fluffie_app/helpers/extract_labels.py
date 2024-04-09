from fluffie_app.helpers.boosters import debug_print
from ..openai_functions.openAIcompletion import get_chat_completion
import ast

def extract_master_labels_using_openAI(search_query, master_label_list, label_count=5, max_attempts=3):
    for attempt in range(max_attempts):
        if len(search_query.split(" ")) <= 2:
            search_query = 'good for ' + search_query
        
        if label_count is not None:
            messages = [{"role": "user", "content": f"""Based on the skincare search query: '{search_query}', evaluate its relevance to the provided labels in this 'master_label_list':{master_label_list}'. The labels are already sorted by relevance so the order matters. Identify and include the top {label_count} labels that are directly mentioned or very strongly implied by the query, without rephrasing or altering them. Ensure that the output consists only of the exact labels from the 'master_label_list', up to the specified number of {label_count}. Labels that are not explicitly related to the query or are not present in the original 'master_label_list' should be excluded. If there are fewer than {label_count} relevant labels, include all that apply. Return the result as a Python list of strings, strictly following the given instructions, without any additional explanation or commentary."""}]
        else:
            messages = [{"role": "user", "content": f"""Based on the skincare search query: '{search_query}', evaluate its relevance to the provided labels in '{master_label_list}'. The labels are already sorted by relevance so the order matters. Identify and include labels that are directly mentioned or very strongly implied by the query, without rephrasing or altering them. Ensure that the output consists only of the exact labels from the 'master_label_list'. Labels that are not explicitly related to the query or are not present in the original 'master_label_list' should be excluded. Return the result as a Python list of strings, strictly following the given instructions, without any additional explanation or commentary."""}]

        master_label_list_extracted = get_chat_completion(messages)

        try:
            master_label_list_extracted = ast.literal_eval(master_label_list_extracted)
            debug_print("Successfully extracted list directly from response")
            if master_label_list_extracted:  # If the list is not empty
                debug_print(f"List extracted successfully in attempt {attempt + 1}")
                return master_label_list_extracted
        except (ValueError, SyntaxError):   
            debug_print(f"Attempt {attempt + 1} failed to extract the list, retrying...")

    debug_print(f"All {max_attempts} attempts failed to extract the list.")
    return []

def renormalize_labels(master_labels, unique_master_labels):
    # Filter out the labels not in unique_master_labels
    filtered_labels = [label for label in master_labels if label[0] in unique_master_labels]
    
    # If no labels left after filtering, return an empty list
    if not filtered_labels:
        return []
    
    # Calculate the sum of weights of the filtered labels
    total_weight = sum(weight for _, _, weight in filtered_labels)
    total_weight = total_weight if total_weight > 0 else 1
    # Create a new list with renormalized weights
    renormalized_labels = [(label, count, weight / total_weight) for label, count, weight in filtered_labels]
    
    return renormalized_labels

def extract_master_label_weights_using_openAI(search_query, master_label_list, skincare_schema, label_count=5, max_attempts=3):
    
    # Inner function to normalize the weights
    def normalize_weights(master_labels):
        total_current_weight = sum(weight for label, occurrence, weight in master_labels)
        normalized_master_labels = [(label, occurrence, weight / total_current_weight) for label, occurrence, weight in master_labels]
        return normalized_master_labels
    
    for attempt in range(max_attempts):
        if len(search_query.split(" ")) <= 2:
            search_query = 'good for ' + search_query

        content = f"""
Based on the skincare search query: '{search_query}', I want to evaluate its relevance to the provided labels in this 'master_label_list': {master_label_list}, using the 'skincare_schema': {skincare_schema}. It's essential that the labels returned are strictly from the 'master_label_list'. The labels and schema properties are already sorted by relevance, and the order matters.

First, identify the aspects of the search query that correspond to the properties in the 'skincare_schema'. Assign weights to each label in the 'master_label_list' based on how directly it's mentioned or implied in the search query, while ensuring that only labels from 'master_label_list' are considered. The weight should also take into account the order of the properties in the 'skincare_schema', giving more weight to properties appearing earlier in the schema.

For instance, if 'skin_concern' is first in 'skincare_schema' and explicitly mentioned in the query, labels related to 'skin_concern' in 'master_label_list' should be weighted higher. Similarly, if 'skin_type' is next and is also mentioned, labels related to 'skin_type' in 'master_label_list' should be weighted next, but less than 'skin_concern'.

After assigning weights, normalize them so that they sum up to 1. Return the result as a Python list of tuples. Each tuple must contain the exact label from 'master_label_list', its occurrence as an integer, and its normalized weight as a float. If there are fewer than {label_count} relevant labels, include all that apply.

Provide the list of tuples strictly following these instructions, without any additional explanation or commentary. And ensure that all the labels in the output are exclusively from the 'master_label_list'."""

        messages = [{"role": "user", "content": content}]
        
        master_label_list_extracted = get_chat_completion(messages)  # Replace with your actual method
    
        try:
            master_label_list_extracted = ast.literal_eval(master_label_list_extracted)
            
            # Validate the list of tuples and each label in the output
            if all(isinstance(item, tuple) and len(item) == 3 for item in master_label_list_extracted):
                if all(isinstance(item[0], str) and isinstance(item[1], int) and isinstance(item[2], float) for item in master_label_list_extracted):
                    valid_master_labels = all(label[0] in master_label_list for label in master_label_list_extracted)
                    if not valid_master_labels:
                        raise ValueError("Some labels in the output are not part of the master_label_list.")
                    
                    # Normalize the weights
                    normalized_master_labels = normalize_weights(master_label_list_extracted)
                    
                    # Make sure the list has exactly label_count number of items
                    if len(normalized_master_labels) > label_count:
                        normalized_master_labels = normalized_master_labels[:label_count]
                    elif len(normalized_master_labels) < label_count:
                        print(f"Warning: Only {len(normalized_master_labels)} labels are available.")
                        
                    return normalized_master_labels
        except (ValueError, SyntaxError):   
            print(f"Attempt {attempt + 1} failed to extract the list, retrying...")
    
    print(f"All {max_attempts} attempts failed to extract the list.")
    return []

def extract_master_label_weights_using_openAI(search_query, master_label_list, skincare_schema, label_count=5, max_attempts=3):
    
    # Inner function to normalize the weights
    def normalize_weights(master_labels):
        total_current_weight = sum(weight for label, occurrence, weight in master_labels)
        normalized_master_labels = [(label, occurrence, weight / total_current_weight) for label, occurrence, weight in master_labels]
        return normalized_master_labels
    
    for attempt in range(max_attempts):
        if len(search_query.split(" ")) <= 2:
            search_query = 'good for ' + search_query

        content = f"""
Based on the skincare search query: '{search_query}', I want to evaluate its relevance to the provided labels in this 'master_label_list': {master_label_list}, using the 'skincare_schema': {skincare_schema}. It's essential that the labels returned are strictly from the 'master_label_list'. The labels and schema properties are already sorted by relevance, and the order matters.

First, identify the aspects of the search query that correspond to the properties in the 'skincare_schema'. Assign weights to each label in the 'master_label_list' based on how directly it's mentioned or implied in the search query, while ensuring that only labels from 'master_label_list' are considered. The weight should also take into account the order of the properties in the 'skincare_schema', giving more weight to properties appearing earlier in the schema.

For instance, if 'skin_concern' is first in 'skincare_schema' and explicitly mentioned in the query, labels related to 'skin_concern' in 'master_label_list' should be weighted higher. Similarly, if 'skin_type' is next and is also mentioned, labels related to 'skin_type' in 'master_label_list' should be weighted next, but less than 'skin_concern'.

After assigning weights, normalize them so that they sum up to 1. Return the result as a Python list of tuples. Each tuple must contain the exact label from 'master_label_list', its occurrence as an integer, and its normalized weight as a float. If there are fewer than {label_count} relevant labels, include all that apply.

Provide the list of tuples strictly following these instructions, without any additional explanation or commentary. And ensure that all the labels in the output are exclusively from the 'master_label_list'."""

        messages = [{"role": "user", "content": content}]
        
        master_label_list_extracted = get_chat_completion(messages)  # Replace with your actual method
    
        try:
            master_label_list_extracted = ast.literal_eval(master_label_list_extracted)
            
            # Validate the list of tuples and each label in the output
            if all(isinstance(item, tuple) and len(item) == 3 for item in master_label_list_extracted):
                if all(isinstance(item[0], str) and isinstance(item[1], int) and isinstance(item[2], float) for item in master_label_list_extracted):
                    valid_master_labels = all(label[0] in master_label_list for label in master_label_list_extracted)
                    if not valid_master_labels:
                        raise ValueError("Some labels in the output are not part of the master_label_list.")
                    
                    # Normalize the weights
                    normalized_master_labels = normalize_weights(master_label_list_extracted)
                    
                    # Make sure the list has exactly label_count number of items
                    if len(normalized_master_labels) > label_count:
                        normalized_master_labels = normalized_master_labels[:label_count]
                    elif len(normalized_master_labels) < label_count:
                        print(f"Warning: Only {len(normalized_master_labels)} labels are available.")
                        
                    return normalized_master_labels
        except (ValueError, SyntaxError):   
            print(f"Attempt {attempt + 1} failed to extract the list, retrying...")
    
    debug_print(f"All {max_attempts} attempts failed to extract the list.")
    return []
