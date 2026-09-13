from types import SimpleNamespace

from app.agents import generation


def test_create_chat_model_configures_bounded_provider_request(monkeypatch):
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: SimpleNamespace(
            llm_provider="groq",
            groq_api_key="test-key",
            llm_model="test-model",
            llm_base_url="https://example.test/v1",
            llm_timeout_seconds=12.0,
        ),
    )

    import langchain_openai

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", FakeChatOpenAI)
    generation.create_chat_model()

    assert captured["request_timeout"] == 12.0
    assert captured["max_retries"] == 0
