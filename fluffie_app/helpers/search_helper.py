def make_filters_criteria_filters(**filters):
    brand = filters['brand']
    master_category = filters['master_category']
    refined_category = filters['refined_category']
    min_price = filters['min_price']
    max_price = filters['max_price']
    pl_summary = filters['pl_summary']

    filter_criteria = {}

    if brand is not None:
        filter_criteria['brand'] = brand[0]
    if master_category is not None:
        filter_criteria['master_category'] = master_category[0]
    if refined_category is not None:
        filter_criteria['refined_category'] = refined_category[0]
    if min_price is not None and max_price is not None:
        filter_criteria['price'] = (min_price, max_price)
    if pl_summary is not None:
        filter_criteria['pl_summary'] = pl_summary[0]
    
    return filter_criteria
    

def filter_search_results(result: [], **filters):
    brand = filters['brand']
    master_category = filters['master_category']
    refined_category = filters['refined_category']
    min_price = filters['min_price']
    max_price = filters['max_price']

    # Filters based on brand
    if brand is not None:
        result = [res for res in result if brand[0] in res['brand']]
    
    # Filter based on master_category
    if master_category is not None:
        result = [res for res in result if master_category[0] in res['master_category']]
    
    # Filter based on refined category
    if refined_category is not None:
        result = [res for res in result if refined_category[0] in res['refined_category']]
    
    # Filter based on price range
    if min_price is not None and max_price is not None:
        result = [res for res in result if isinstance(res['price'], float) and min_price <= res['price'] <= max_price]
    
    return result