"""
ACEForge API Client
Supports multiple AI providers via a unified streaming interface.

Providers:
  - anthropic   → Anthropic API (Claude models)
  - google      → Google AI Studio (Gemini models) — free tier available
  - openai      → OpenAI API (GPT models)
  - compatible  → Any OpenAI-compatible endpoint (Mistral, Groq, Together,
                  Ollama, LM Studio, Jan, etc.)

Get a free Google AI Studio key at: https://aistudio.google.com/apikey
"""

from typing import Callable


PROVIDER_ANTHROPIC  = "anthropic"
PROVIDER_GOOGLE     = "google"
PROVIDER_OPENAI     = "openai"
PROVIDER_COMPATIBLE = "compatible"

KNOWN_ENDPOINTS = {
    "OpenAI (default)":  "https://api.openai.com/v1",
    "Mistral":           "https://api.mistral.ai/v1",
    "Groq":              "https://api.groq.com/openai/v1",
    "Together AI":       "https://api.together.xyz/v1",
    "Perplexity":        "https://api.perplexity.ai",
    "Ollama (local)":    "http://localhost:11434/v1",
    "LM Studio (local)": "http://localhost:1234/v1",
    "Jan (local)":       "http://localhost:1337/v1",
}

DEFAULT_MODELS = {
    PROVIDER_ANTHROPIC:  "claude-sonnet-4-20250514",
    PROVIDER_GOOGLE:     "gemini-2.0-flash",
    PROVIDER_OPENAI:     "gpt-4o",
    PROVIDER_COMPATIBLE: "mistral-medium",
}

# Model suggestions shown as quick-fill buttons in Settings
MODEL_SUGGESTIONS = {
    PROVIDER_ANTHROPIC: [
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-haiku-4-5-20251001",
    ],
    PROVIDER_GOOGLE: [
        "gemini-2.0-flash",          # free, fast, recommended
        "gemini-2.0-flash-lite",     # free, fastest
        "gemini-1.5-pro",            # free tier, more capable
        "gemini-1.5-flash",          # free tier, balanced
    ],
    PROVIDER_OPENAI: [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ],
    PROVIDER_COMPATIBLE: [
        "mistral-medium",
        "mistral-small",
        "llama-3-70b-instruct",
        "mixtral-8x7b",
        "gemma-7b-it",
    ],
}


class APIClient:
    def __init__(
        self,
        api_key:  str = "",
        model:    str = "claude-sonnet-4-20250514",
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
        api_key:  str,
        model:    str,
        provider: str = PROVIDER_ANTHROPIC,
        base_url: str = "",
    ):
        self._api_key  = api_key
        self._model    = model
        self._provider = provider
        self._base_url = base_url
        self._client   = None

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_key(self) -> tuple[bool, str]:
        try:
            if self._provider == PROVIDER_ANTHROPIC:
                return self._validate_anthropic()
            elif self._provider == PROVIDER_GOOGLE:
                return self._validate_google()
            else:
                return self._validate_openai_compat()
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _validate_anthropic(self) -> tuple[bool, str]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            client.messages.create(
                model=self._model, max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True, ""
        except ImportError:
            return False, "anthropic package not installed. Run: pip install anthropic"
        except Exception as e:
            return False, _friendly_error(e, "anthropic")

    def _validate_google(self) -> tuple[bool, str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model)
            model.generate_content("hi", generation_config={"max_output_tokens": 10})
            return True, ""
        except ImportError:
            return False, "google-generativeai package not installed. Run: pip install google-generativeai"
        except Exception as e:
            return False, _friendly_error(e, "google")

    def _validate_openai_compat(self) -> tuple[bool, str]:
        try:
            import openai
            client = self._build_openai_client()
            client.chat.completions.create(
                model=self._model, max_tokens=10,
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
        user_prompt:   str,
        on_chunk: Callable[[str], None],
        on_done:  Callable[[str], None],
        on_error: Callable[[str], None],
    ):
        try:
            if self._provider == PROVIDER_ANTHROPIC:
                self._stream_anthropic(system_prompt, user_prompt, on_chunk, on_done, on_error)
            elif self._provider == PROVIDER_GOOGLE:
                self._stream_google(system_prompt, user_prompt, on_chunk, on_done, on_error)
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
                model=self._model, max_tokens=8000,
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

    def _stream_google(self, system, user, on_chunk, on_done, on_error):
        """
        Google AI Studio streaming via google-generativeai SDK.
        System prompt is passed as system_instruction (supported in Gemini 1.5+).
        Free tier: 15 requests/min, 1500 requests/day on flash models.
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)

            model = genai.GenerativeModel(
                model_name=self._model,
                system_instruction=system,
            )

            full = []
            response = model.generate_content(
                user,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8000,
                    temperature=0.7,
                ),
            )
            for chunk in response:
                text = chunk.text if hasattr(chunk, "text") else ""
                if text:
                    full.append(text)
                    on_chunk(text)

            on_done("".join(full))

        except ImportError:
            on_error(
                "google-generativeai package not installed.\n"
                "Run: pip install google-generativeai"
            )
        except Exception as e:
            on_error(_friendly_error(e, "google"))

    def _stream_openai_compat(self, system, user, on_chunk, on_done, on_error):
        try:
            import openai
            client = self._build_openai_client()
            full = []
            stream = client.chat.completions.create(
                model=self._model, max_tokens=8000, stream=True,
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
    if "auth" in low or "api key" in low or "401" in low or "403" in low or "invalid" in low and "key" in low:
        return "Invalid API key. Check your key in Settings."
    if "rate" in low or "429" in low or "quota" in low or "resource exhausted" in low:
        return "Rate limit or quota exceeded. Wait a moment and try again."
    if "connect" in low or "timeout" in low or "network" in low or "refused" in low:
        return "Connection failed. Check your internet connection and endpoint URL."
    if "model" in low and ("not found" in low or "does not exist" in low or "404" in low):
        return "Model not found. Check the model name in Settings."
    if "billing" in low or "payment" in low:
        return "Billing issue with your API account. Check your provider dashboard."
    return f"API error: {msg}"
