import json
import sys
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_STAGE2 = ROOT / "external" / "equational-theories-lean-stage2"
sys.path.insert(0, str(EXTERNAL_STAGE2))

from pipeline import proxy  # noqa: E402
from pipeline import marathon_llm, marathon_proxy  # noqa: E402


MASS_BASE_URL = "http://60.171.65.125:30197/v1"
MASS_MODEL = "gemma-4-31b"
MASS_API_KEY = "mass-no-key-required"
MASS_LOCAL_MAX_OUTPUT_TOKENS = 1024
MASS_LOCAL_HTTP_TIMEOUT_SECONDS = 60


def assert_openai_ctor_uses_mass_without_env_proxy(ctor: dict, timeout: float):
    assert ctor["api_key"] == MASS_API_KEY
    assert ctor["base_url"] == MASS_BASE_URL
    assert ctor["timeout"] == timeout
    http_client = ctor.get("http_client")
    assert http_client is not None
    assert getattr(http_client, "_trust_env", None) is False
    assert ctor["max_retries"] == 0


def test_external_stage2_config_routes_llm_to_mass_gemma():
    config = json.loads((EXTERNAL_STAGE2 / "pipeline" / "config.json").read_text())
    llm = config["llm"]

    assert llm["model"] == MASS_MODEL
    assert llm["base_url"] == MASS_BASE_URL
    assert llm["api_key"] == MASS_API_KEY
    assert llm["max_output_tokens"] == MASS_LOCAL_MAX_OUTPUT_TOKENS
    assert llm["http_timeout_seconds"] == MASS_LOCAL_HTTP_TIMEOUT_SECONDS
    assert llm["stream"] is True
    assert "provider" not in llm
    assert "reasoning_effort" not in llm


def test_solo_proxy_uses_configured_mass_key_without_openrouter_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured_ctor: list[dict] = []
    captured_create: list[dict] = []

    class _CaptureOpenAI:
        def __init__(self, **kwargs):
            captured_ctor.append(dict(kwargs))

            class _Msg:
                content = "ok"
                reasoning = None

            class _Choice:
                message = _Msg()
                finish_reason = "stop"

            class _Completion:
                choices = [_Choice()]

            class _Completions:
                def create(self_inner, **kwargs):
                    captured_create.append(dict(kwargs))
                    return _Completion()

            class _Chat:
                completions = _Completions()

            self.chat = _Chat()

    config = {
        "llm": {
            "model": MASS_MODEL,
            "base_url": MASS_BASE_URL,
            "api_key": MASS_API_KEY,
            "max_output_tokens": 16,
            "temperature": 0.0,
        }
    }

    with patch.object(proxy, "OpenAI", _CaptureOpenAI):
        result = proxy._call_llm("hi", config, max_seconds=5.0)

    assert result == {"response": "ok"}
    assert len(captured_ctor) == 1
    assert_openai_ctor_uses_mass_without_env_proxy(captured_ctor[0], 5.0)
    assert captured_create[0]["model"] == MASS_MODEL
    assert "extra_body" not in captured_create[0]


def test_solo_proxy_can_stream_from_config_without_trace_hook(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured_create: list[dict] = []

    class _Delta:
        reasoning = None

        def __init__(self, content: str | None):
            self.content = content

    class _Choice:
        def __init__(self, content: str | None, finish_reason: str | None = None):
            self.delta = _Delta(content)
            self.finish_reason = finish_reason

    class _Chunk:
        def __init__(self, content: str | None, finish_reason: str | None = None):
            self.choices = [_Choice(content, finish_reason)]

    class _Stream:
        def __iter__(self):
            yield _Chunk("o")
            yield _Chunk("k")
            yield _Chunk(None, "stop")

    class _CaptureOpenAI:
        def __init__(self, **kwargs):
            class _Completions:
                def create(self_inner, **kwargs):
                    captured_create.append(dict(kwargs))
                    if not kwargs.get("stream"):
                        raise AssertionError("expected streaming request")
                    return _Stream()

            class _Chat:
                completions = _Completions()

            self.chat = _Chat()

    config = {
        "llm": {
            "model": MASS_MODEL,
            "base_url": MASS_BASE_URL,
            "api_key": MASS_API_KEY,
            "max_output_tokens": 16,
            "temperature": 0.0,
            "stream": True,
        }
    }

    with patch.object(proxy, "OpenAI", _CaptureOpenAI):
        result = proxy._call_llm("hi", config, max_seconds=5.0)

    assert result == {"response": "ok"}
    assert captured_create[0]["stream"] is True


def test_marathon_helper_defaults_to_mass_gemma(monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", MASS_API_KEY)
    monkeypatch.setenv("JUDGE_MARATHON_BUDGET_TOKENS", "-1")
    marathon_llm._last_seen_tokens_total = 0

    captured_ctor: list[dict] = []
    captured_create: list[dict] = []

    class _CaptureOpenAI:
        def __init__(self, **kwargs):
            captured_ctor.append(dict(kwargs))

            class _Msg:
                content = "ok"
                reasoning = None

            class _Choice:
                message = _Msg()
                finish_reason = "stop"

            class _Usage:
                total_tokens = 3

            class _Completion:
                choices = [_Choice()]
                usage = _Usage()

            class _Completions:
                def create(self_inner, **kwargs):
                    captured_create.append(dict(kwargs))
                    return _Completion()

            class _Chat:
                completions = _Completions()

            self.chat = _Chat()

    with patch("openai.OpenAI", _CaptureOpenAI):
        result = marathon_llm.call_llm(
            "hi",
            config={"max_output_tokens": 16, "temperature": 0.0},
            max_seconds=5.0,
        )

    assert result["response"] == "ok"
    assert len(captured_ctor) == 1
    assert_openai_ctor_uses_mass_without_env_proxy(captured_ctor[0], 5.0)
    assert captured_create[0]["model"] == MASS_MODEL
    assert "extra_body" not in captured_create[0]


def test_marathon_proxy_defaults_to_mass_upstream_without_env(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    handle = marathon_proxy.start_marathon_proxy(
        state_dir=tmp_path / "proxy-state",
        budget_tokens=0,
    )
    try:
        config = handle._server.config
        assert config.upstream_base_url == MASS_BASE_URL
        assert config.upstream_api_key == MASS_API_KEY
    finally:
        handle.stop()
