import openai
import os
from dotenv import load_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from gptcache import cache
from gptcache.adapter import openai
from gptcache.manager import CacheBase, VectorBase, get_data_manager

cache_base = CacheBase('sqlite')
vector_base = VectorBase('chromadb')
data_manager = get_data_manager(cache_base, vector_base)
cache.init(data_manager=data_manager)
cache.set_openai_key()

load_dotenv()
openai.api_key = os.environ["openai_key"]

embeddings = OpenAIEmbeddings()

# use "gpt-4" for better results
def get_chat_completion(messages,model="gpt-3.5-turbo-16k"):
    """
    Generate a chat completion using OpenAI's chat completion API.
    Args:
        messages: The list of messages in the chat history.
        model: The name of the model to use for the completion. Default is gpt-3.5-turbo, which is a fast, cheap and versatile model. Use gpt-4 for higher quality but slower results. And also we can use gpt-3.5-turbo-16k for 16k token context if the token size exceeds
    Returns:
        A string containing the chat completion.
    Raises:
        Exception: If the OpenAI API call fails.
    """
    # call the OpenAI chat completion API with the given messages
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
    )
    choices = response["choices"]  # type: ignore
    # if response is from GPTCache, handle it accordingly
    if isinstance(response, dict):
        completion = choices[0].get("message").get("content").strip()
    else:
        completion = choices[0].message.content.strip()
    print(f"{completion}")
    return completion

def fetch_vector_store(index_name: str, text_key, namespace):
    vector_store = Pinecone.from_existing_index(index_name, embeddings, text_key, namespace)
    return vector_store