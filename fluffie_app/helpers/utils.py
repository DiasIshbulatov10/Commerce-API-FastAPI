from scipy.stats import hmean
from collections import Counter
from pprint import PrettyPrinter
from langchain.chat_models import ChatOpenAI
import openai
import asyncio
from gptcache import cache
from gptcache.embedding.openai import OpenAI

from ..core.config import settings

cache.init()
cache.set_openai_key()
# Initialize your language model
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=settings.openai_key)
import sys
import pprint

sys.setrecursionlimit(3000)

pp = pprint.PrettyPrinter(depth=6)
MODEL = "text-embedding-ada-002"

encoder = OpenAI(api_key=settings.openai_key, model=MODEL)

# // Custom functions and logic that Langchain doesn't have //
# Function to vectorize a list of JSON objects (which are dictionaries in Python)
async def vectorize_JSON_list(search_query_JSON_list):
    print("tpye", type(search_query_JSON_list))
    vectorized_list = []
    for single_JSON in search_query_JSON_list:
        vectorized_list.append(asyncio.create_task(vectorize_dict(single_JSON)))
    response = await asyncio.gather(*vectorized_list)
    return response

# Function to vectorize a dictionary
async def vectorize_dict(search_query_dict):
    keys = []
    tasks = []
    for key, value in search_query_dict.items():
        keys.append(key)
        tasks.append(asyncio.create_task(vectorize_sub_dict(value) if isinstance(value, dict) else create_embedding(key, value)))
    results = await asyncio.gather(*tasks)
    return {k: v for k, v in zip(keys, results)}

# Function to vectorize sub-dictionary
async def vectorize_sub_dict(sub_dict):
    return {k: create_embedding(k, v) for k, v in sub_dict.items()}

# Function to create embedding
async def create_embedding(key, value):
    input_string = f"{key} {' '.join(map(str, value))}" if isinstance(value, list) else f"{key} {str(value)}"
    
    # without GPTCache
    # result = await openai.Embedding.acreate(input=input_string, engine=MODEL)
    # return result['data'][0]['embedding']

    # with GPTCache
    result = encoder.to_embeddings(input_string)
    return result.tolist()