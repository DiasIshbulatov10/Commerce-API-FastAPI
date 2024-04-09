from fuzzywuzzy import fuzz

def custom_score(match, search_query_dict=None, age_group=None, seq_match_threshold=0.1, productname_weight=1, producttype_weight=1, skintone_weight=1):
    if search_query_dict is None:
        search_query_dict = {}
    
    metadata = match["metadata"]
    metadata = {k.lower(): v for k, v in metadata.items()}  # Convert all metadata keys to lowercase
    matching_fields = 0
    matched_data = {}

    key_mapping = {
        "skin_tone": ["skin_tone"],
        "skin_concern": ["skin_concern"],
        "skin_type": ["skin_type"],
        "country": ["country"],
        "age": ["age"]
    }

    key_mapping = {k.lower(): [x.lower() for x in v] for k, v in key_mapping.items()}

    def similarity(a, b):
        return fuzz.token_set_ratio(a, b) / 100
    
    for key, value in search_query_dict.items():
        if key in key_mapping:
            for metadata_key in key_mapping[key]:
                if metadata_key in metadata:
                    try:
                        if metadata_key == "skin_type":
                            if value.lower() == metadata[metadata_key].lower():
                                matching_fields += 1
                                matched_data[key] = value
                        elif key.lower() == "price" and isinstance(value, tuple):
                            # Compare price constraints
                            if 'price' in metadata:
                                metadata_price = float(metadata['price'])
                                lower_bound, upper_bound = value
                                if lower_bound is not None and metadata_price < lower_bound:
                                    return -1, matched_data
                                if upper_bound is not None and metadata_price > upper_bound:
                                    return -1, matched_data
                            else:
                                return -1, matched_data
                        elif key.lower() == "product_name":
                            seq_match_ratio = similarity(value.lower(), metadata["product"].lower())
                            if seq_match_ratio >= seq_match_threshold:
                                matching_fields += productname_weight
                                matched_data[key] = value
                        elif key.lower() == "product_category":
                            seq_match_ratio_refined = similarity(value.lower(), metadata["refined_category"].lower())
                            seq_match_ratio_master = similarity(value.lower(), metadata["master_category"].lower())
                            if seq_match_ratio_refined >= seq_match_threshold or seq_match_ratio_master >= seq_match_threshold:
                                matching_fields += producttype_weight
                                matched_data[key] = value
                        elif key.lower() == "skin_tone":
                            seq_match_ratio = similarity(value.lower(), metadata["skin_tone"].lower())
                            if seq_match_ratio >= seq_match_threshold:
                                matching_fields += skintone_weight
                                matched_data[key] = value
                        elif key.lower() == "skin_concern":
                            seq_match_ratio = similarity(value.lower(), metadata["skin_concern"].lower())
                            if seq_match_ratio >= seq_match_threshold:
                                matching_fields += 1
                                matched_data[key] = value
                        elif key.lower() == "country":
                            seq_match_ratio = similarity(value.lower(), metadata["country"].lower())
                            if value.lower() == metadata["country"].lower():
                                matching_fields += 1
                                matched_data[key] = value
                        else:
                            # Use SequenceMatcher for string similarity
                            seq_match_ratio = similarity(value.lower(), metadata[metadata_key].lower())
                            if seq_match_ratio >= seq_match_threshold:
                                matching_fields += 1
                                matched_data[key] = value
                    except:
                        continue
                    
    if age_group and 'age' in metadata:
        try:
            # Check if the age group matches the age range in metadata
            if " to " in metadata['age']:
                age_range = metadata['age'].split(" to ")
                lower_age, upper_age = int(age_range[0]), int(age_range[1])

                # Add the condition to check if age_group is not None before trying to split it
                if age_group is not None:
                    age_group_range = age_group.split(" to ")
                    search_lower_age, search_upper_age = int(age_group_range[0]), int(age_group_range[1])

                    if search_lower_age <= lower_age <= search_upper_age or search_lower_age <= upper_age <= search_upper_age:
                        matching_fields += 0.2
                        matched_data['age'] = age_group
            else:
                if metadata['age'].lower() == age_group.lower():
                    matching_fields += 0.2
                    matched_data['age'] = age_group
                    
        except Exception as e:
            print(f"Error in custom_score: {e}")
            
    # Move the finally block here, outside the try and except blocks
    # Ensure the function always returns a numerical value
    custom_score = match["score"] + matching_fields if match["score"] is not None else 0
    return custom_score, matched_data
