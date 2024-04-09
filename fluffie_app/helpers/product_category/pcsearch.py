
from ...db.pinecone import query_search_index

# Function to perform search query with metadata filters
async def search_reviews(query_vector, prod_ids, metadata_key, desired_value, top_k):
    results = query_search_index(
        vector=query_vector,
        # filter={"$and": [
        #     {metadata_key: {"$eq": desired_value}},
        #     {"prod_id": {"$eq": prod_ids}}
        # ]},
        top_k=top_k,
        include_metadata=True
    )
    return await results

# Define the search_products function and parallel_search function
async def search_products(query_vector, metadata_key, desired_value, top_k, filter_criteria, exclude_products = None):
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
        elif isinstance(value, list):
            combined_filters.append({
                key: { '$in': value }
            })

        else:
            combined_filters.append({key: {"$eq": value}})

    if exclude_products is not None:
        combined_filters.append({
            'prod_id': { '$nin': exclude_products }
        })

    filtered_res = query_search_index(
        vector=query_vector,
        filter={"$and": combined_filters},
        top_k=top_k,
        include_metadata=True
    )
    return await filtered_res
