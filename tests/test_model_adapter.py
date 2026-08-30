"""Tests for the Hugging Face runtime model adapter."""

from types import SimpleNamespace

from src.model_adapter import HuggingFaceChatModel


def test_hugging_face_adapter_returns_model_text_without_network() -> None:
    captured_request: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="  model response  ")
                    )
                ]
            )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=FakeCompletions(),
        )
    )

    model = HuggingFaceChatModel(
        model="synthetic/test-model",
        client=fake_client,
    )

    result = model("Return valid JSON only.")

    assert result == "model response"
    assert captured_request["model"] == "synthetic/test-model"
    assert captured_request["reasoning_effort"] == "low"
    assert captured_request["messages"] == [
        {
            "role": "user",
            "content": "Return valid JSON only.",
        }
    ]
