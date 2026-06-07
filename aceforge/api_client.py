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
PROVIDER_OLLAMA     = "ollama"   # local Ollama — maps to compatible at localhost:11434/v1

OLLAMA_BASE_URL = "http://localhost:11434/v1"

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
    PROVIDER_OLLAMA:     "deepseek-r1:14b",
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
        "deepseek-chat",
        "deepseek-coder",
    ],
    PROVIDER_OLLAMA: [
        "deepseek-r1:14b",   # best quality/speed balance — recommended
        "deepseek-r1:7b",    # faster, slightly less capable
        "llama3.1:8b",       # great all-rounder, runs on 8GB VRAM
        "llama3.1:70b",      # high quality, needs 48GB+ RAM
        "llama3.2:3b",       # ultra-fast, basic tasks only
        "mistral:7b",
        "codellama:13b",
        "phi3:medium",
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
        if provider == PROVIDER_OLLAMA:
            provider = PROVIDER_COMPATIBLE
            base_url = base_url.strip() or OLLAMA_BASE_URL
            api_key  = api_key or "ollama"
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
        # Ollama is OpenAI-compatible at localhost — normalise here so the
        # rest of the class never needs to know about the ollama provider.
        if provider == PROVIDER_OLLAMA:
            provider = PROVIDER_COMPATIBLE
            base_url = base_url.strip() or OLLAMA_BASE_URL
            api_key  = api_key or "ollama"  # Ollama ignores the key; must be non-empty
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
            # Use models.list() — zero tokens, just verifies the API key is valid
            client = anthropic.Anthropic(api_key=self._api_key)
            client.models.list()
            return True, ""
        except ImportError:
            return False, "anthropic package not installed. Run: pip install anthropic"
        except anthropic.AuthenticationError:
            return False, "Invalid API key. Check your Anthropic key at console.anthropic.com"
        except Exception as e:
            return False, _friendly_error(e, "anthropic")

    def _validate_google(self) -> tuple[bool, str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            # list_models is a lightweight call that just verifies the key
            list(genai.list_models())
            return True, ""
        except ImportError:
            return False, "google-generativeai package not installed. Run: pip install google-generativeai"
        except Exception as e:
            return False, _friendly_error(e, "google")

    def _validate_openai_compat(self) -> tuple[bool, str]:
        try:
            import openai
            client = self._build_openai_client()
            # Try models.list() first — lightweight, just checks auth
            try:
                models = list(client.models.list())
                # If we got a model list and the configured model is set,
                # verify it actually exists (optional warning only — don't fail)
                if self._model and models:
                    ids = [m.id for m in models]
                    if self._model not in ids:
                        # Return success but warn about model name
                        return True, f"Key valid, but model '{self._model}' not in provider's list. Available: {', '.join(ids[:5])}…"
                return True, ""
            except openai.AuthenticationError:
                return False, "Invalid API key. Check your key at your provider's dashboard."
            except Exception:
                # Some providers don't support models.list() — try a minimal chat call
                try:
                    client.chat.completions.create(
                        model=self._model or "llama-3-8b-8192",
                        max_tokens=1,
                        messages=[{"role": "user", "content": "hi"}],
                    )
                    return True, ""
                except openai.AuthenticationError:
                    return False, "Invalid API key. Check your key at your provider's dashboard."
                except openai.NotFoundError:
                    # Key works but model name is wrong — still connected
                    return True, f"Key valid, but model '{self._model}' not found. Check the model name."
                except Exception as e2:
                    return False, _friendly_error(e2, "openai")
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
        temperature: float = 0.7,
    ):
        try:
            if self._provider == PROVIDER_ANTHROPIC:
                self._stream_anthropic(system_prompt, user_prompt, on_chunk, on_done, on_error, temperature)
            elif self._provider == PROVIDER_GOOGLE:
                self._stream_google(system_prompt, user_prompt, on_chunk, on_done, on_error, temperature)
            else:
                self._stream_openai_compat(system_prompt, user_prompt, on_chunk, on_done, on_error, temperature)
        except Exception as e:
            on_error(f"Unexpected error: {str(e)}")

    def _stream_anthropic(self, system, user, on_chunk, on_done, on_error, temperature=0.7):
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=self._api_key,
                timeout=600.0,  # 10 minute timeout for long generations
            )
            full = []
            with client.messages.stream(
                model=self._model, max_tokens=16000,
                temperature=temperature,
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

    def _stream_google(self, system, user, on_chunk, on_done, on_error, temperature=0.7):
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
                    max_output_tokens=16000,
                    temperature=temperature,
                ),
            )
            for chunk in response:
                # FinishReason 2 = MAX_TOKENS: chunk may have no valid Part.
                # Guard against AttributeError on .text access.
                try:
                    text = chunk.text if hasattr(chunk, "text") else ""
                except (AttributeError, ValueError):
                    # No valid Part — model hit token limit on this chunk; skip it.
                    text = ""
                if text:
                    full.append(text)
                    on_chunk(text)

            # Check finish reason on final response to detect truncation
            try:
                finish_reason = None
                if hasattr(response, "candidates") and response.candidates:
                    finish_reason = getattr(response.candidates[0], "finish_reason", None)
                elif hasattr(response, "prompt_feedback"):
                    pass  # safety block — let on_done handle empty full
            except Exception:
                pass

            assembled = "".join(full)
            if not assembled and finish_reason == 2:
                # MAX_TOKENS with nothing streamed — likely a safety/quota issue
                on_error("Google API hit token limit with no output. Try a shorter prompt or switch to a larger model.")
                return

            on_done(assembled)

        except ImportError:
            on_error(
                "google-generativeai package not installed.\n"
                "Run: pip install google-generativeai"
            )
        except Exception as e:
            on_error(_friendly_error(e, "google"))

    def _stream_openai_compat(self, system, user, on_chunk, on_done, on_error, temperature=0.7):
        try:
            import openai
            client = self._build_openai_client()
            full = []

            # Build kwargs — some providers (Groq, Mistral) accept max_tokens,
            # others use max_completion_tokens. Start with max_tokens and fall back.
            kwargs = dict(
                model=self._model,
                stream=True,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            # Try with max_tokens first (works for Groq, Mistral, Ollama, etc.)
            try:
                kwargs["max_tokens"] = 16000
                stream = client.chat.completions.create(**kwargs)
            except openai.BadRequestError as e:
                if "max_tokens" in str(e).lower() or "max_completion_tokens" in str(e).lower():
                    kwargs.pop("max_tokens", None)
                    kwargs["max_completion_tokens"] = 16000
                    stream = client.chat.completions.create(**kwargs)
                else:
                    raise

            for chunk in stream:
                delta = chunk.choices[0].delta
                text = delta.content if delta.content is not None else ""
                if text:
                    full.append(text)
                    on_chunk(text)
            on_done("".join(full))
        except ImportError:
            on_error("openai package not installed. Run: pip install openai")
        except openai.AuthenticationError:
            on_error("Invalid API key. Check your key in Settings.")
        except openai.NotFoundError as e:
            on_error(f"Model not found: '{self._model}'. Check the model name for your provider.")
        except Exception as e:
            on_error(_friendly_error(e, "openai"))

    def _build_openai_client(self):
        import openai
        url = self._base_url.strip() or None
        return openai.OpenAI(api_key=self._api_key or "none", base_url=url)


# ── Helpers ───────────────────────────────────────────────────────────────────

def list_ollama_models(base_url: str = OLLAMA_BASE_URL) -> list[str]:
    """Return model names installed in local Ollama instance. Empty list if not running."""
    import urllib.request, json
    try:
        tags_url = base_url.replace("/v1", "").rstrip("/") + "/api/tags"
        with urllib.request.urlopen(tags_url, timeout=2) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []

def _friendly_error(exc: Exception, provider: str) -> str:
    msg = str(exc)
    low = msg.lower()
    # Auth errors — must be specific, not catch model errors
    if "401" in low or "authentication" in low or "unauthenticated" in low:
        return "Invalid API key. Check your key in Settings."
    if "403" in low and "permission" in low:
        return "API key does not have permission for this operation."
    # Rate limits
    if "429" in low or ("rate" in low and "limit" in low) or "quota" in low or "resource exhausted" in low:
        return "Rate limit or quota exceeded. Wait a moment and try again."
    # Network
    if "connect" in low or "timeout" in low or "network" in low or "refused" in low or "unreachable" in low:
        return "Connection failed. Check your internet connection and endpoint URL."
    # Model not found — do NOT confuse with auth
    if ("model" in low or "engine" in low) and ("not found" in low or "does not exist" in low or "invalid" in low or "404" in low):
        return "Model not found or invalid. Check the model name in Settings."
    # Billing
    if "billing" in low or "payment" in low or "insufficient_quota" in low:
        return "Billing issue. Check your account at your provider's dashboard."
    # Google FinishReason=2 (MAX_TOKENS) — "valid Part" / "Quick accessor" error
    if "quick accessor" in low or "finish_reason" in low or "finishreason" in low or        ("part" in low and "valid" in low) or "finish reason" in low:
        return ("Google hit max token limit mid-response. The multi-pass system will "
                "automatically continue. If it fails, try switching to gemini-1.5-pro "
                "or reducing prompt complexity.")
    return f"API error: {msg}"
