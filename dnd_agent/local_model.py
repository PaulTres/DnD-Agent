"""LangChain adapter for an OpenAI-compatible locally hosted chat model."""

from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from langchain_openai import ChatOpenAI

from config import RuntimeSettings, get_settings


class LocalModelUnavailableError(RuntimeError):
    """Raised when the configured local model endpoint cannot be reached."""


def check_local_model(settings: RuntimeSettings | None = None, *, timeout: float = 4.0) -> None:
    """Check that the configured OpenAI-compatible endpoint is serving models."""

    settings = settings or get_settings()
    url = f"{settings.model_base_url.rstrip('/')}/models"
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status < 200 or response.status >= 300:
                raise LocalModelUnavailableError(
                    f"Local model endpoint {url} returned HTTP {response.status}. "
                    "Start the local model server and check DND_MODEL_BASE_URL."
                )
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise LocalModelUnavailableError(
            f"Could not reach the local model endpoint at {url}: {exc}. "
            "Start an OpenAI-compatible local server and check DND_MODEL_BASE_URL. "
            "DND_MODEL_PATH is informational; this app does not load model weights itself."
        ) from exc


def create_chat_model(
    settings: RuntimeSettings | None = None,
    *,
    temperature: float = 0.7,
    check_available: bool = True,
) -> ChatOpenAI:
    """Create the LangChain chat model, clearly failing if the server is down."""

    settings = settings or get_settings()
    if check_available:
        check_local_model(settings)
    try:
        return ChatOpenAI(
            base_url=settings.model_base_url,
            api_key="local-only",
            model=settings.model_name,
            temperature=temperature,
        )
    except Exception as exc:
        raise LocalModelUnavailableError(
            f"Could not configure the local chat model {settings.model_name!r}: {exc}"
        ) from exc
