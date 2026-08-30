"""Runtime model adapter for Hugging Face Inference Providers."""

from typing import Any
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(dotenv_path=".env")

HF_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b:cerebras"


class HuggingFaceChatModel:
    """Callable text model compatible with the specialist agent interfaces."""

    def __init__(
        self,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or os.getenv("MODEL_ID") or DEFAULT_MODEL
        self._client = client

    def _get_client(self) -> Any:
        """Create the OpenAI-compatible Hugging Face client when needed."""

        if self._client is not None:
            return self._client

        token = os.getenv("HF_TOKEN")
        if not token:
            raise RuntimeError(
                "HF_TOKEN is not configured. "
                "Set it as an environment variable before running the agent."
            )

        self._client = OpenAI(
            base_url=HF_BASE_URL,
            api_key=token,
        )
        return self._client

    def __call__(self, prompt: str) -> str:
        """Send one prompt to the configured model and return response text."""

        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")
        if not prompt.strip():
            raise ValueError("prompt must not be empty")

        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            reasoning_effort="low",
        )

        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("model returned an empty response")

        return content.strip()
