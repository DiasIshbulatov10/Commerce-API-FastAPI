import openai

from tenacity import retry, wait_random_exponential, stop_after_attempt

MODEL = "text-embedding-ada-002"

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Embed texts using OpenAI's ada model.
    Args:
        texts: The list of texts to embed.
    Returns:
        A list of embeddings, each of which is a list of floats.
    Raises:
        Exception: If the OpenAI API call fails.
    """
    # Call the OpenAI API to get the embeddings
    response = openai.Embedding.create(input=texts, model=MODEL)

    # Extract the embedding data from the response
    data = response["data"]  # type: ignore

    # Return the embeddings as a list of lists of floats
    return [result["embedding"] for result in data]
