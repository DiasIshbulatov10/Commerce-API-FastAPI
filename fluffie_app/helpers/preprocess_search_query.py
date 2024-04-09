# preprocess_search_query.py
import json
from .utils import vectorize_JSON_list, create_embedding
import asyncio
import time
import concurrent
import openai


from .clustered import clustered_labels
# Add any other necessary imports here, such as JSON handling, etc.


# Function to call the first API
def call_api_1(search_query):
    response = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0613:personal::8kjIZb2o",
        messages=[
            {"role": "system", "content": """Please analyze the skincare product review provided, and identify key various aspects of skincare products based on the provided schema below: \\n{\\n  \\\"schema\\\": {\\n    \\\"skin_concern\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"skin_type\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"skin_tone\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"age\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"product_name\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"brand\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"product_category\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"product_benefits\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"product_aspects\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"ingredients\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"country\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}},\\n    \\\"price\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"integer\\\"}},\\n    \\\"skincare_extra_info\\\": {\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"string\\\"}}\\n  }\\n}\\n Output your result as a JSON-formatted list. Make sure to identify any product categories as product_category, and brands as 'brand'. Also, if there are any aspects which are present in this list, use them as key value pairs in your output:     ""['lip product comptabile', 'effective highlighting', 'toner', 'pleasant texture', 'good for long-term use', 'travel-friendly', 'eyelash darkening', 'mature lip-friendly', 'oil-free', 'gentle', 'seasonal use-friendly', 'jaw-area friendly', 'smooths lip wrinkles', 'makeup-free', 'gel formula', 'not tight-feeling', 'darkens eyebrows', 'waterproof', 'soothes irritation', 'white-cast free', 'liquid formula', 'smooth texture', 'exfoliating scrub', 'brightening', 'acne scar reducing', 'eye cream', 'discoloration reducing', 'for combination skin', 'effective exfoliator', 'controls oil', 'double cleanse appropriate', 'revitalizing for dull skin', 'gentle exfoliate', 'skin balancing', 'hand softening', 'softens skin', 'wrinkle reducing', 'transfer-resistant', 'skin barrier-friendly', 'firming and tightening', 'age spot reduction', 'quality packaging', 'eye-irritation free', 'no rinse required', 'small amount of product required', 'serum', 'hydrating', 'removes tan well', 'rapid results', 'alternatives', 'easy to mix', 'non-drying', 'hydrates dry areas', 'evens tone', 'beginner-friendly', 'targets milia', 'buildable', 'promotes brow growth ', 'spray form', 'good coverage', 'removes eye makeup well', 'tinted moisturizer', 'natural finish', 'good price', 'hormonal-acne friendly', 'controls eyelid oil', 'no pilling', 'T-zone targeted', 'good color accuracy', 'diminishes dark circles', 'anti-aging', 'long battery life', 'removes makeup well', 'dark spot reduction', 'cake-free', 'refreshing', 'non-glossy', 'brow lifting', 'soft texture', 'eco-friendly', 'promotes healthy skin', 'calming', 'pleasant scent', 'eye-area friendly', 'pregnancy-safe', 'red light therapy', 'clay product', 'mess-free', 'beneficial for under-eyes', 'overnight use', 'gloss finish', 'easy to apply', 'no peeling or flaking', 'skin purging', 'effective chemical exfoliator', 'deep cleansing', 'durable', 'eye bag reduction', 'effectiveness', 'helps psoriasis', 'child-friendly', 'soothes sunburn', 'foamy lather', 'effective for acne', 'mask', 'for oily skin', 'great as a base', 'irritation-free', 'suitable for winter use', 'breathable', 'neck-friendly', 'chemical-free', 'acne-preventing', 'enhances hand appearance', 'boosts eye appearance', 'promoted reviews', 'lip-friendly', 'night use', 'nice finish', 'fast-drying', 'balancing', 'lash strengthening', 'promotes eyebrow growth', 'UV protection', 'refreshes makeup', 'residue-free', 'removes sunscreen well', 'matte finish', 'gel cleanser', 'weatherproof', 'good size', 'depuffing', 'enhances lash curl', 'for dehydrated lips', 'quality applicator', 'refines pores', 'enhances makeup longevity', 'for dehydrated skin', 'long-lasting', 'non-clogging', 'lotion', 'lip plumping', 'vegan', 'sunscreen comptabile', 'targets whiteheads', 'clears blackheads', 'cruelty free', 'rosacea-friendly', 'detoxifying', 'skin smoothing', 'complexion enhancing', 'non-sticky', 'for dry skin', 'promotes eyelash growth', 'tanning', 'removes lip makeup well', 'makeup alternative', 'compatible with other products', 'invisible finish', 'compatible with primers', 'nourishing', 'versatile', 'acne-prone skin friendly', 'blackhead minimizing', 'skin brightening', 'suitable for long-term use', 'makeup compatible', 'suitable for darker skin tones', 'easy dispense', 'pleasant taste', 'sting-free', 'cystic acne relief', 'reduces blotchiness', 'not stripping', 'easy to remove', 'promotes supple skin', 'gentle cleanse', 'plumping', 'balm', 'grainy texture', 'lip softening', 'for normal skin', 'lightweight', 'teen-skin friendly', 'suitable for all ages', 'moisturizes hands', 'boosts brow volume', 'lip smoothing', 'lip hydrating', 'strong formula', 'creamy', 'summer suitable', 'tingling sensation', 'skin detoxifying', 'thick', 'suitable for morning use', 'cleansing', 'suitable for daily use', 'mist formula', 'calms redness', 'quality ingredients', 'enhances brow health & appearance', 'heat-resistant', 'mature skin-friendly', 'cooling', 'for sensitive skin', 'promotes clear skin', 'clean product', 'decongesting', 'eczema soothing', 'sheer finish', 'flake-free', 'pore strip', 'chin-area friendly', 'drying effect', 'soothes itchiness', 'natural product', 'promotes dewy skin', 'rejuvenating', 'suitable for all skin types', 'dermatitis soothing', 'easy to blend', 'scar healing', 'moisturizer', 'chest-area friendly', 'undereye depuffing', 'enhances lash health & appearance', 'crease-free', 'sheer coverage', 'targets blind pimples', 'pleasant feel', 'heavy', 'enhances eyelid appearance', 'stain-free', 'high quality', 'targets bacne', 'pleasant feeling', 'sun spot reduction', 'sensitive eye friendly', 'high color payoff', 'boosts lash growth', 'rich', 'pore cleansing', 'pigmentation reduction', 'for oily lips', 'eyelid friendly', 'streak-free', 'absorbs well', 'fragrance free', 'lip makeup compatible', 'promotes healthy skin cells', 'keratosis pilaris-friendly']"" You MUST return at least one field, even if the user input is one word:\\n"},
    {"role": "user", "content": f"{search_query}"""},
            {"role": "user", "content": f"{search_query}"}
        ]
    )
    return json.loads(response.choices[0].message.content)

# Function to call the second API
def call_api_2(search_query):
    response = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0613:personal::8Y8M0ypE",
        messages=[
            {"role": "system", "content": """Please analyze the skincare product review provided and assign labels with associated weights from the provided list only. The weights should reflect each label's importance relative to the review. Output your result in a Weighted Label List, formatted as a JSON object. Each object in the list should comprise a string identifier (label) and a numerical value (weight) representing its significance. Only use labels from the following label list:
          
    ""['lip product comptabile', 'effective highlighting', 'toner', 'pleasant texture', 'good for long-term use', 'travel-friendly', 'eyelash darkening', 'mature lip-friendly', 'oil-free', 'gentle', 'seasonal use-friendly', 'jaw-area friendly', 'smooths lip wrinkles', 'makeup-free', 'gel formula', 'not tight-feeling', 'darkens eyebrows', 'waterproof', 'soothes irritation', 'white-cast free', 'liquid formula', 'smooth texture', 'exfoliating scrub', 'brightening', 'acne scar reducing', 'eye cream', 'discoloration reducing', 'for combination skin', 'effective exfoliator', 'controls oil', 'double cleanse appropriate', 'revitalizing for dull skin', 'gentle exfoliate', 'skin balancing', 'hand softening', 'softens skin', 'wrinkle reducing', 'transfer-resistant', 'skin barrier-friendly', 'firming and tightening', 'age spot reduction', 'quality packaging', 'eye-irritation free', 'no rinse required', 'small amount of product required', 'serum', 'hydrating', 'removes tan well', 'rapid results', 'alternatives', 'easy to mix', 'non-drying', 'hydrates dry areas', 'evens tone', 'beginner-friendly', 'targets milia', 'buildable', 'promotes brow growth ', 'spray form', 'good coverage', 'removes eye makeup well', 'tinted moisturizer', 'natural finish', 'good price', 'hormonal-acne friendly', 'controls eyelid oil', 'no pilling', 'T-zone targeted', 'good color accuracy', 'diminishes dark circles', 'anti-aging', 'long battery life', 'removes makeup well', 'dark spot reduction', 'cake-free', 'refreshing', 'non-glossy', 'brow lifting', 'soft texture', 'eco-friendly', 'promotes healthy skin', 'calming', 'pleasant scent', 'eye-area friendly', 'pregnancy-safe', 'red light therapy', 'clay product', 'mess-free', 'beneficial for under-eyes', 'overnight use', 'gloss finish', 'easy to apply', 'no peeling or flaking', 'skin purging', 'effective chemical exfoliator', 'deep cleansing', 'durable', 'eye bag reduction', 'effectiveness', 'helps psoriasis', 'child-friendly', 'soothes sunburn', 'foamy lather', 'effective for acne', 'mask', 'for oily skin', 'great as a base', 'irritation-free', 'suitable for winter use', 'breathable', 'neck-friendly', 'chemical-free', 'acne-preventing', 'enhances hand appearance', 'boosts eye appearance', 'promoted reviews', 'lip-friendly', 'night use', 'nice finish', 'fast-drying', 'balancing', 'lash strengthening', 'promotes eyebrow growth', 'UV protection', 'refreshes makeup', 'residue-free', 'removes sunscreen well', 'matte finish', 'gel cleanser', 'weatherproof', 'good size', 'depuffing', 'enhances lash curl', 'for dehydrated lips', 'quality applicator', 'refines pores', 'enhances makeup longevity', 'for dehydrated skin', 'long-lasting', 'non-clogging', 'lotion', 'lip plumping', 'vegan', 'sunscreen comptabile', 'targets whiteheads', 'clears blackheads', 'cruelty free', 'rosacea-friendly', 'detoxifying', 'skin smoothing', 'complexion enhancing', 'non-sticky', 'for dry skin', 'promotes eyelash growth', 'tanning', 'removes lip makeup well', 'makeup alternative', 'compatible with other products', 'invisible finish', 'compatible with primers', 'nourishing', 'versatile', 'acne-prone skin friendly', 'blackhead minimizing', 'skin brightening', 'suitable for long-term use', 'makeup compatible', 'suitable for darker skin tones', 'easy dispense', 'pleasant taste', 'sting-free', 'cystic acne relief', 'reduces blotchiness', 'not stripping', 'easy to remove', 'promotes supple skin', 'gentle cleanse', 'plumping', 'balm', 'grainy texture', 'lip softening', 'for normal skin', 'lightweight', 'teen-skin friendly', 'suitable for all ages', 'moisturizes hands', 'boosts brow volume', 'lip smoothing', 'lip hydrating', 'strong formula', 'creamy', 'summer suitable', 'tingling sensation', 'skin detoxifying', 'thick', 'suitable for morning use', 'cleansing', 'suitable for daily use', 'mist formula', 'calms redness', 'quality ingredients', 'enhances brow health & appearance', 'heat-resistant', 'mature skin-friendly', 'cooling', 'for sensitive skin', 'promotes clear skin', 'clean product', 'decongesting', 'eczema soothing', 'sheer finish', 'flake-free', 'pore strip', 'chin-area friendly', 'drying effect', 'soothes itchiness', 'natural product', 'promotes dewy skin', 'rejuvenating', 'suitable for all skin types', 'dermatitis soothing', 'easy to blend', 'scar healing', 'moisturizer', 'chest-area friendly', 'undereye depuffing', 'enhances lash health & appearance', 'crease-free', 'sheer coverage', 'targets blind pimples', 'pleasant feel', 'heavy', 'enhances eyelid appearance', 'stain-free', 'high quality', 'targets bacne', 'pleasant feeling', 'sun spot reduction', 'sensitive eye friendly', 'high color payoff', 'boosts lash growth', 'rich', 'pore cleansing', 'pigmentation reduction', 'for oily lips', 'eyelid friendly', 'streak-free', 'absorbs well', 'fragrance free', 'lip makeup compatible', 'promotes healthy skin cells', 'keratosis pilaris-friendly']""
     
    The output must strictly contain labels from this list and no others. The format of your output should resemble the following example:

    "{\"label_weights\": [{\"label\": \"retinol\", \"weight\": 0.57}, {\"label\": \"non-drying\", \"weight\": 0.43}]}"

    Provide no further explanation:"""},
            {"role": "user", "content": f"{search_query}"}
        ]
    )
    return json.loads(response.choices[0].message.content)


def extract_relevant_labels(search_query):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "system", "content": """Task: You will be given a skincare search query. Your task is to determine which clusters from 'clustered_skincare_labels' would be most relevant to the search query, and output a JSON dictionary, and provide no further explanation. You can look at skincare_labels for reference too. Here are the clusters:

            skincare_labels = {
                "acne": ['effective for acne', 'acne-preventing', 'acne-prone skin friendly', 'targets bacne', 'clears blackheads', 'targets blind pimples', 'targets whiteheads', 'blackhead minimizing','cystic acne relief','hormonal-acne friendly'],
                "aging": ['anti-aging', 'wrinkle reducing'],
                "sensitivity": ['sting-free', 'eye-irritation free', 'sensitive eye friendly', 'irritation-free', 'eye-area friendly','eyelid friendly'],
                "dryness": ['hydrating', 'moisturizer', 'hydrates dry areas', 'flake-free'],
                "oiliness": ['controls eyelid oil', 'controls oil', 'oil-free'],
                "pigmentation": ['dark spot reduction', 'pigmentation reduction', 'discoloration reducing', 'age spot reduction', 'sun spot reduction'],
                "scarring": ['scar healing', 'acne scar reducing'],
                "texture": ['skin smoothing', 'softens skin','promotes supple skin'],
                "uneven skin tone": ['evens tone', 'reduces blotchiness','complexion enhancing'],
                "dark circles": ['diminishes dark circles', 'undereye depuffing','eye bag reduction','boosts eye appearance','beneficial for under-eyes', 'enhances eyelid appearance'],
                "sun protection": ['sunscreen comptabile', 'UV protection', 'soothes sunburn'],
                "eczema": ['eczema soothing'],
                "milia": ['targets milia'],
                "dermatitis": ['dermatitis soothing'],
                "psoriasis": ['helps psoriasis'],
                "inflammation":['depuffing'],
                "rosacea": ['rosacea-friendly','calms redness'],
                "firming": ['firming and tightening','plumping'],
                "dull skin": ['revitalizing for dull skin', 'brightening','promotes dewy skin', 'promotes clear skin','skin brightening'],
                "keratosis pilaris": ['keratosis pilaris-friendly'],
                "skin health": ['skin protection', 'balancing' , 'skin barrier-friendly','promotes healthy skin cells','skin balancing','promotes healthy skin'],
                "pores": ['pore strip', 'refines pores', 'pore cleansing', 'non-clogging', 'decongesting'],
                "detox": ['detoxifying', 'skin detoxifying'],
                "hormonal issues": [],
                "tanning": ['tanning'],
                "lip care": ['lip hydrating', 'lip softening', 'lip plumping', 'lip smoothing', 'for oily lips', 'lip makeup compatible', 'lip product comptabile', 'for dehydrated lips', 'smooths lip wrinkles','lip-friendly','mature lip-friendly'],
                "hand and nail care": ['hand softening', 'enhances hand appearance', 'moisturizes hands'],
                "cleansing": ['cleansing','double cleanse appropriate', 'deep cleansing','removes eye makeup well','removes sunscreen well','removes tan well', 'removes lip makeup well','removes makeup well','gentle cleanse'],
                "makeup-related": ['refreshes makeup', 'makeup compatible', 'compatible with primers', 'compatible with other products', 'makeup alternative', 'enhances makeup longevity', 'makeup-free','great as a base'],
                "packaging": ['quality packaging', 'good size', 'travel-friendly', 'easy dispense','quality applicator'],
                "product attributes": ['eco-friendly', 'vegan', 'cruelty free', 'natural product', 'chemical-free','pregnancy-safe', 'clean product'],
                "eyelash and eyebrow care": ['promotes brow growth ', 'brow lifting', 'darkens eyebrows', 'boosts brow volume', 'promotes eyebrow growth', 'enhances brow health & appearance', 'lash strengthening', 'boosts lash growth', 'enhances lash health & appearance', 'enhances lash curl','eyelash darkening','promotes eyelash growth'],
                "texture/formula": ['smooth texture', 'gel cleanser', 'soft texture', 'gel formula', 'creamy', 'lotion', 'mist formula', 'thick', 'grainy texture', 'liquid formula', 'rich', 'foamy lather', 'gentle', 'pleasant texture', 'heavy', 'spray form', 'clay product', 'serum', 'quality ingredients', 'eye cream', 'tinted moisturizer', 'exfoliating scrub', 'mask','strong formula','breathable','non-sticky','lightweight','toner','balm'],
                "exfoliation": ['gentle exfoliate','effective exfoliator','effective chemical exfoliator'],
                "coverage/finish": ['natural finish', 'sheer coverage', 'good coverage', 'nice finish', 'gloss finish', 'non-glossy', 'matte finish', 'buildable','sheer finish','invisible finish'],
                "application": ['easy to apply', 'absorbs well','no rinse required' , 'easy to blend', 'fast-drying', 'mess-free', 'beginner-friendly','easy to remove','easy to mix'],
                "skin type": ['for normal skin', 'for combination skin', 'suitable for all skin types', 'for dry skin', 'for sensitive skin','for oily skin', 'for dehydrated skin', 'acne-prone skin friendly'],
                "skin tone": ['suitable for darker skin tones'],
                "age suitability": ['mature skin-friendly', 'teen-skin friendly', 'suitable for all ages','child-friendly'],
                "skin feeling": ['not tight-feeling', 'soothes irritation','nourishing','pleasant feel', 'cooling', 'tingling sensation','refreshing', 'soothes itchiness', 'rejuvenating', 'drying effect', 'no peeling or flaking','calming','not stripping','skin purging', 'non-drying','pleasant feeling'],
                "fragrance/scent": ['pleasant taste', 'fragrance free', 'pleasant scent'],
                "transferability": ['stain-free', 'transfer-resistant', 'white-cast free', 'cake-free', 'no pilling', 'residue-free', 'streak-free','crease-free'],
                "versatility": ['heat-resistant', 'versatile', 'waterproof', 'long-lasting', 'weatherproof','durable'],
                "color": ['good color accuracy','high color payoff'],
                "usage": ['night use','good for long-term use','overnight use', 'summer suitable','small amount of product required', 'suitable for winter use', 'suitable for daily use', 'seasonal use-friendly', 'suitable for morning use','suitable for long-term use'],
                "promoted": ['promoted reviews'],
                "other skin areas": ['chin-area friendly','jaw-area friendly','neck-friendly','chest-area friendly','T-zone targeted'],
                "price and quality": ['good price','high quality'],
                "general effectiveness": ['effectiveness','effective highlighting','rapid results'],
                "unclassified": ['long battery life', 'red light therapy', 'alternatives']
            }


            clustered_skincare_labels = {
                "Acne and Oil Control": skincare_labels["acne"] + skincare_labels["oiliness"],
                "Anti-Aging and Firming": skincare_labels["aging"] + skincare_labels["firming"],
                "Pore and Texture Refinement": skincare_labels["pores"] + skincare_labels["texture"],
                "Skin Tone and Pigmentation": skincare_labels["pigmentation"] + skincare_labels["uneven skin tone"],
                "Sensitivity and Redness": skincare_labels["sensitivity"] + skincare_labels["rosacea"] + skincare_labels["inflammation"],
                "Hydration and Nourishment": skincare_labels["dryness"],
                "Cleansing and Makeup Removal": skincare_labels["cleansing"],
                "Scarring and Healing": skincare_labels["scarring"] + skincare_labels["skin health"],
                "Dullness and Revitalization": skincare_labels["dull skin"],
                "Specific Conditions": skincare_labels["eczema"] + skincare_labels["milia"] + skincare_labels["dermatitis"] + skincare_labels["psoriasis"] + skincare_labels["keratosis pilaris"],
                "Product Characteristics": skincare_labels["product attributes"] + skincare_labels["texture/formula"] + skincare_labels["coverage/finish"] + skincare_labels["application"] + skincare_labels["fragrance/scent"],
                "Sun and Protection": skincare_labels["sun protection"],
                "Lip and Eye Care": skincare_labels["lip care"] + skincare_labels["eyelash and eyebrow care"],
                "Hand and Nail Care": skincare_labels["hand and nail care"],
                "Skin Type and Tone": skincare_labels["skin type"] + skincare_labels["skin tone"],
                "Age Suitability and Feeling": skincare_labels["age suitability"] + skincare_labels["skin feeling"],
                "Versatility and Usage": skincare_labels["versatility"] + skincare_labels["usage"],
                "Color and Finish": skincare_labels["color"] + skincare_labels["transferability"],
                "Value and Effectiveness": skincare_labels["price and quality"] + skincare_labels["general effectiveness"],
                "Other": skincare_labels["other skin areas"] + skincare_labels["unclassified"],
            }


            Here's an example: Search query: glycolic acid 30 percent" 

            Reasoning (you don't need to output this, but think about this reasoning before your output response):

            Given the search query "glycolic acid 30 percent," users are likely looking for products with exfoliation properties, targeting texture improvement, and possibly anti-aging benefits due to the concentration of glycolic acid. Here are the keys from the nested dictionary that would be most valuable:

            Pore and Texture Refinement: Because glycolic acid is known for its exfoliating properties, it can help improve skin texture and minimize the appearance of pores.

            Anti-Aging and Firming: Glycolic acid can help reduce the appearance of fine lines and wrinkles, making this category relevant.

            Dullness and Revitalization: Glycolic acid is often used to brighten dull skin, making it look more revitalized.

            Scarring and Healing: Since glycolic acid can aid in the reduction of acne scars and promote healing, this cluster might also be relevant.

            Exfoliation: If you have a separate category or labels related to exfoliation, this would be directly relevant (though it's not listed in the provided clusters).

            These clusters would help users find products with glycolic acid that are aimed at refining skin texture, anti-aging, brightening dull skin, and potentially helping with scarring. It's important to note that a 30% concentration of glycolic acid is quite high and is usually used in chemical peels, so the products may also fall under professional or clinical skincare categories.


            Output:

            {
            "RelevantKeys": [
                "Pore and Texture Refinement",
                "Anti-Aging and Firming",
                "Dullness and Revitalization",
                "Scarring and Healing",
                "Exfoliation"
            ]
            }

            Now provide an Output for this JSON query"""},
                        {"role": "user", "content": f"{search_query}"}
                    ]
                )
    return json.loads(response.choices[0].message.content)

def fetch_relevant_labels(results):
    relevant_labels = {}
    for key in results['RelevantKeys']:
        relevant_labels[key] = clustered_labels[key]
    return relevant_labels

async def preprocess_search_query(search_query, extraction_chain):
    if len(search_query.split(" ")) <= 1:
        search_query = f'good for {search_query}'
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Schedule the API calls and retrieve their results
        future_api_1 = executor.submit(call_api_1, search_query)
        future_api_2 = executor.submit(call_api_2, search_query)
        relevant_labels = executor.submit(extract_relevant_labels, search_query)

    try:
        result_api_1 = future_api_1.result()  # Result from API 1
        result_api_2 = future_api_2.result()  # Result from API 2
        results_relevant_labels = fetch_relevant_labels(relevant_labels.result())
        print("OpenAI result_api_1", result_api_1)
        print("OpenAI result_api_2", result_api_2)
        print("OpenAI results_relevant_labels", results_relevant_labels)
        search_query_JSON_string = str(result_api_1) + search_query
        
        weighted_query_vector = await asyncio.gather(*[create_embedding("", search_query_JSON_string)])
        return result_api_1, result_api_2, weighted_query_vector, results_relevant_labels
    except Exception as e:
        print(f"An error occurred: {e}")

    # Vectorization logic
    # search_query_JSON_string = str(search_query_JSON_list) + search_query
    # print("search_query_JSON_list", search_query_JSON_list)
    # vectorized_search_query_JSON_list, weighted_query_vector = await asyncio.gather(*[vectorize_JSON_list(search_query_JSON_list), create_embedding("", search_query_JSON_string)])
    # print("End vectorizing JSON list task main")
    # print("--- %s seconds ---" % (time.time() - start_time))
    # return search_query_JSON_list, search_query_JSON_string, vectorized_search_query_JSON_list, weighted_query_vector
