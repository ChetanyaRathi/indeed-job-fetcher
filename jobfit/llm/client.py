from openai import OpenAI
from jobfit.config import LLM_ENDPOINT, LLM_MODEL, EMBED_MODEL
import logging

logger = logging.getLogger(__name__)

# Initialize the client. Base URL points to the local model server.
# API key is a dummy value since we are hitting a local server.
try:
    client = OpenAI(base_url=LLM_ENDPOINT, api_key="local")
except Exception as e:
    raise RuntimeError(
        f"Failed to initialize OpenAI client with endpoint {LLM_ENDPOINT}. "
        "Ensure your model server (Ollama or LM Studio) is running."
    ) from e


def chat(messages: list[dict], response_format: dict = None) -> str:
    """
    Sends a chat completion request to the reasoning model.
    """
    try:
        kwargs = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.0,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(
            f"Failed to communicate with model '{LLM_MODEL}' at '{LLM_ENDPOINT}'. "
            "Please ensure your model server is running and the model is pulled."
        ) from e


def embed(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a batch of texts.
    """
    if not texts:
        return []
    try:
        response = client.embeddings.create(
            model=EMBED_MODEL,
            input=texts
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        raise RuntimeError(
            f"Failed to generate embeddings with model '{EMBED_MODEL}' at '{LLM_ENDPOINT}'. "
            "Please ensure your model server is running and the embedding model is pulled."
        ) from e
