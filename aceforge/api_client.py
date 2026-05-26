"""
ACEForge API Client
Supports multiple AI providers via a unified streaming interface.

Providers:
  - anthropic   → Anthropic API (Claude models)
  - openai      → OpenAI API (GPT models)
  - compatible  → Any OpenAI-compatible endpoint (Mistral, Groq, Together,
                  Ollama, LM Studio, Jan, etc.)

The provider is selected in Settings. All three share the same
stream_generate() / validate_key() interface so the rest of the app
never needs to know which provider is active.
"""

from typing import Callable, Optional


# ── Provider constants ────────────────────────────────────────────────────────

PROVIDER_ANTHROPIC   = "anthropic"
PROVIDER_OPENAI      = "openai"
PROVIDER_COMPATIBLE  = "compatible"   # OpenAI-compatible custom endpoint

# Well-known base URLs for the compatible provider dropdown
KNOWN_ENDPOINTS = {
    "OpenAI (default)":    "https://api.openai.com/v1",
    "Mistral":             "https://api.mistral.ai/v1",
    "Groq":                "https://api.groq.com/openai/v1",
    "Together AI":         "https://api.together.xyz/v1",
    "Perplexity":          "https://api.perplexity.ai",
    "Ollama (local)":      "http://localhost:11434/v1",
    "LM Studio (local)":   "http://localhost:1234/v1",
    "Jan (local)":         "http://localhost:1337/v1",
}

# Default model suggestions per provider
DEFAULT_MODELS = {
    PROVIDER_ANTHROPIC:  "claude-sonnet-4-20250514",
    PROVIDER_OPENAI:     "gpt-4o",
    PROVIDER_COMPATIBLE: "mistral-medium",
}


class APIClient:
    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-sonnet-4-20250514",
        provider: str = PROVIDER_ANTHROPIC,
        base_url: str = "",
    ):
        self._api_key  = api_key
        self._model    = model
        self._provider = provider
        self._base_url = base_url
        self._client   = None

    def update_credentials(
        self,
        api_key: str,
        model: str,
        provider: str = PROVIDER_ANTHROPIC,
        base_url: str = "",
    ):
        self._api_key  = api_key
        self._model    = model
        self._provider = provider
        self._base_url = base_url
        self._client   = None   # force re-init on next call

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_key(self) -> tuple[bool, str]:
        """
        Send a minimal request to verify the API key and endpoint are working.
        Returns (success, error_message).
        """
        try:
            if self._provider == PROVIDER_ANTHROPIC:
                return self._validate_anthropic()
            else:
                return self._validate_openai_compat()
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _validate_anthropic(self) -> tuple[bool, str]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True, ""
        except ImportError:
            return False, "anthropic package not installed. Run: pip install anthropic"
        except Exception as e:
            return False, _friendly_error(e, "anthropic")

    def _validate_openai_compat(self) -> tuple[bool, str]:
        try:
            import openai
            client = self._build_openai_client()
            client.chat.completions.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True, ""
        except ImportError:
            return False, "openai package not installed. Run: pip install openai"
        except Exception as e:
            return False, _friendly_error(e, "openai")

    # ── Streaming ─────────────────────────────────────────────────────────────

    def stream_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        on_chunk: Callable[[str], None],
        on_done:  Callable[[str], None],
        on_error: Callable[[str], None],
    ):
        """
        Stream a generation request. Runs in a background thread.
        Calls on_chunk(text) for each token, on_done(full) when complete,
        on_error(message) on failure.
        """
        try:
            if self._provider == PROVIDER_ANTHROPIC:
                self._stream_anthropic(system_prompt, user_prompt, on_chunk, on_done, on_error)
            else:
                self._stream_openai_compat(system_prompt, user_prompt, on_chunk, on_done, on_error)
        except Exception as e:
            on_error(f"Unexpected error: {str(e)}")

    def _stream_anthropic(self, system, user, on_chunk, on_done, on_error):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            full = []
            with client.messages.stream(
                model=self._model,
                max_tokens=8000,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                for text in stream.text_stream:
                    full.append(text)
                    on_chunk(text)
            on_done("".join(full))
        except ImportError:
            on_error("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            on_error(_friendly_error(e, "anthropic"))

    def _stream_openai_compat(self, system, user, on_chunk, on_done, on_error):
        try:
            import openai
            client = self._build_openai_client()
            full = []
            stream = client.chat.completions.create(
                model=self._model,
                max_tokens=8000,
                stream=True,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            for chunk in stream:
                text = chunk.choices[0].delta.content or ""
                if text:
                    full.append(text)
                    on_chunk(text)
            on_done("".join(full))
        except ImportError:
            on_error("openai package not installed. Run: pip install openai")
        except Exception as e:
            on_error(_friendly_error(e, "openai"))

    def _build_openai_client(self):
        import openai
        url = self._base_url.strip() or None
        return openai.OpenAI(api_key=self._api_key or "none", base_url=url)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _friendly_error(exc: Exception, provider: str) -> str:
    msg = str(exc)
    low = msg.lower()
    if "auth" in low or "api key" in low or "401" in low or "403" in low:
        return f"Invalid API key. Check your key in Settings."
    if "rate" in low or "429" in low:
        return "Rate limit exceeded. Wait a moment and try again."
    if "connect" in low or "timeout" in low or "network" in low:
        return f"Connection failed. Check your internet connection and endpoint URL."
    if "model" in low and ("not found" in low or "invalid" in low or "404" in low):
        return f"Model not found. Check the model name in Settings."
    return f"API error: {msg}"
