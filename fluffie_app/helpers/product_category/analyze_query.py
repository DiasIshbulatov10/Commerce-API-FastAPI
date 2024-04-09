import re
import ast
import json

from ...services.openai.completion import get_chat_completion
from ...core.logger import logger
from .parse_age import convert_age_to_group

def extract_dictionary_and_age_group(search_query):
    if len(search_query.split(" ")) <= 2:
        search_query = 'good for ' + search_query

    messages = [{
        "role": "user",
        "content": f"""Please carefully analyze the following skin and beauty search query: '{search_query}'.
Create a dictionary containing only the relevant key-value pairs that can be found in the query.
The possible keys are: skin_type, skin_tone, age, product_category, skin_concern, country,
brand, price, ingredients, and product_name.
If any of these keys are not present in the query, do not include them in the dictionary.
For skin_type, recognize common abbreviations and terms, such as 'combo skin' for 'Combination'.
For Age, extract the full digits only (e.g.'30 y/o' should be 'Age': '30').
For country, use the full country name (e.g., 'aus' should be 'Australia').
If the query contains price, or price constraints like 'less than $30',
extract the lower and upper bounds as a tuple (e.g., 'Price': (None, 30)).
If the query seems to have a specific product name, include it as the 'product_name' key in the dictionary.
Recognize and correct typos in product categories such as exfoliator, cleanser, moisturizer,
serum, and toner, and include them as the 'product_category' key in the dictionary if present in the search query.
Only include key-value pairs for the keys that are explicitly mentioned in the search query.
Do not make assumptions or add information that is not present in the search query.
Do not include any key-value pairs with 'not found' values,
and do not include any additional text or context in your response."""
    }]

    search_query_dict_str = get_chat_completion(messages)

    try:
        search_query_dict = ast.literal_eval(search_query_dict_str)
        search_query_dict = {k.lower(): v.lower() if isinstance(v, str) else v for k, v in search_query_dict.items()}
        # print("Successfully extracted dictionary directly from response")
    except (json.decoder.JSONDecodeError, ValueError, SyntaxError):
        logger.warn("Failed to extract dictionary directly from response")
        search_query_dict = {}
        possible_keys = ["skin_type", "skin_tone", "age", "product_category", "skin_concern", "location", "brand", "price", "ingredients", "product_name"]

        for key in possible_keys:
            if key == "price":
                pattern = re.compile(r'["\']{}["\']:\s*\(([^)]+)\)'.format(key), re.IGNORECASE)
                match = pattern.search(search_query_dict_str)
                if match:
                    values = match.group(1).split(',')
                    lower_bound = None if values[0].strip().lower() == 'none' else int(values[0].strip())
                    upper_bound = None if values[1].strip().lower() == 'none' else int(values[1].strip())
                    search_query_dict[key] = (lower_bound, upper_bound)
                else:
                    print("No match found for key {}".format(key))
            else:
                pattern = re.compile(r'["\']{}["\']:\s*["\']([^"\']+)["\']'.format(key), re.IGNORECASE)
                match = pattern.search(search_query_dict_str)
                if match:
                    value = match.group(1)
                    if value.lower() not in ('none', 'not found'):
                        search_query_dict[key] = value
                    else:
                        print("Skipping key {} due to 'None' or 'not found' value".format(key))
                else:
                    print("No match found for key {}".format(key))

        search_query_dict = {k: v for k, v in search_query_dict.items() if v is not None}

    age = None
    age_group = None

    for term in search_query.split():
        if term.isdigit():
            age = int(term)
            break

    #convert age group to an age group
    if isinstance(age, int):
        age_group = convert_age_to_group(age)
    else:
        age_group = None

    # Remove 'not found' key-value pairs
    search_query_dict = {k: v for k, v in search_query_dict.items() if v != 'not found'}

    return search_query_dict, age_group
