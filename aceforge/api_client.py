"""
ACEForge API Client
Manages streaming Anthropic API calls.
Yields text chunks as they arrive so the UI can display them live.
"""

import anthropic
from typing import Generator, Optional, Callable


class APIClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key
        self._model = model
        self._client: Optional[anthropic.Anthropic] = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None or self._client.api_key != self._api_key:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def update_credentials(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = None

    def validate_key(self) -> tuple[bool, str]:
        """
        Quick validation check — sends a minimal request.
        Returns (success, error_message).
        """
        try:
            client = self._get_client()
            client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True, ""
        except anthropic.AuthenticationError:
            return False, "Invalid API key. Please check your Anthropic API key."
        except anthropic.APIConnectionError:
            return False, "Could not connect to the Anthropic API. Check your internet connection."
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def stream_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        on_chunk: Callable[[str], None],
        on_done: Callable[[str], None],
        on_error: Callable[[str], None],
    ):
        """
        Stream a generation request.
        Calls on_chunk(text) for each streamed token.
        Calls on_done(full_text) when complete.
        Calls on_error(message) on failure.

        This method is designed to run in a background thread.
        """
        try:
            client = self._get_client()
            full_text = []

            with client.messages.stream(
                model=self._model,
                max_tokens=8000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                for text in stream.text_stream:
                    full_text.append(text)
                    on_chunk(text)

            on_done("".join(full_text))

        except anthropic.AuthenticationError:
            on_error("Authentication failed. Please check your API key in Settings.")
        except anthropic.RateLimitError:
            on_error("Rate limit exceeded. Please wait a moment and try again.")
        except anthropic.APIStatusError as e:
            on_error(f"API error {e.status_code}: {e.message}")
        except anthropic.APIConnectionError:
            on_error("Connection failed. Check your internet connection.")
        except Exception as e:
            on_error(f"Unexpected error: {str(e)}")
