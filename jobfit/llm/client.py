import json
import urllib.request
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


def chat(messages: list[dict], response_format: dict = None, **kwargs) -> str:
    """
    Sends a chat completion request to the reasoning model.
    """
    try:
        api_kwargs = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.0,
        }
        if response_format:
            api_kwargs["response_format"] = response_format
            
        api_kwargs.update(kwargs)

        response = client.chat.completions.create(**api_kwargs)
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(
            f"Failed to communicate with model '{LLM_MODEL}' at '{LLM_ENDPOINT}'. "
            "Please ensure your model server is running and the model is pulled."
        ) from e


def _native_base_url() -> str:
    """Ollama's native API base (strip the OpenAI-compat ``/v1`` suffix)."""
    base = LLM_ENDPOINT.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base.rstrip("/")


def chat_no_think(messages: list[dict], max_tokens: int = 2000, temperature: float = 0.0) -> dict:
    """
    Chat with thinking fully disabled, via Ollama's native ``/api/chat`` endpoint.

    The OpenAI-compat endpoint (``/v1/chat/completions``) ignores the ``think``
    flag / ``reasoning_effort`` on this Ollama build, and the ``/no_think`` prompt
    tag is not honored either, so a thinking model burns the whole token budget
    reasoning and truncates the JSON. The native endpoint honors ``think: False``
    and returns clean content with an empty thinking field.

    Returns the raw parsed response dict (contains ``message`` and ``done_reason``).
    """
    url = _native_base_url() + "/api/chat"
    body = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(
            f"Failed to communicate with model '{LLM_MODEL}' at native endpoint '{url}'. "
            "Please ensure Ollama is running and the model is pulled."
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
