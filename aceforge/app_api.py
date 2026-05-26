"""
ACEForge App API
Python methods exposed to the JavaScript frontend via pywebview's js_api.
Called from JS as: window.pywebview.api.method_name(args)
"""

import threading
import json
import os
from pathlib import Path
from datetime import datetime

from .config import Config
from .skill_loader import SkillLoader
from .api_client import APIClient, KNOWN_ENDPOINTS, DEFAULT_MODELS
from .sql_parser import parse_and_save_files


class AppAPI:
    def __init__(self, config: Config):
        self.config = config
        self.skill_loader = SkillLoader()
        self.api_client = APIClient(
            api_key=config.api_key,
            model=config.model,
            provider=config.provider,
            base_url=config.base_url,
        )
        self._window = None
        self._generating = False

    def set_window(self, window):
        self._window = window

    # ── Configuration ─────────────────────────────────────────────────────────

    def get_config(self) -> dict:
        return {
            "provider":     self.config.provider,
            "api_key_set":  bool(self.config.api_key),
            "model":        self.config.model,
            "base_url":     self.config.base_url,
            "server_name":  self.config.server_name,
            "author":       self.config.get("author", ""),
            "output_dir":   self.config.output_dir,
            "wcid_ranges":  self.config.get_wcid_ranges(),
            # Send provider metadata to JS for building the UI
            "known_endpoints": KNOWN_ENDPOINTS,
            "default_models":  DEFAULT_MODELS,
        }

    def save_config(self, data: dict) -> dict:
        try:
            if "provider"    in data: self.config.provider    = data["provider"]
            if "model"       in data: self.config.model       = data["model"]
            if "base_url"    in data: self.config.base_url    = data["base_url"]
            if "server_name" in data: self.config.server_name = data["server_name"]
            if "author"      in data: self.config.set("author", data["author"])
            if "output_dir"  in data: self.config.output_dir  = data["output_dir"]
            if "api_key" in data and data["api_key"]:
                self.config.api_key = data["api_key"]
            if "wcid_ranges" in data:
                self.config.set("wcid_ranges", data["wcid_ranges"])

            self.config.save()

            # Refresh the API client with new credentials
            self.api_client.update_credentials(
                api_key=self.config.api_key,
                model=self.config.model,
                provider=self.config.provider,
                base_url=self.config.base_url,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_key(self) -> dict:
        """Test the currently saved API credentials."""
        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )
        ok, err = self.api_client.validate_key()
        return {"valid": ok, "error": err}

    def validate_key_with(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str = "",
    ) -> dict:
        """
        Test credentials passed directly from the Settings form.
        Does NOT require saving first — used by the Test Connection button.
        Uses a temporary client so saved credentials are not affected.
        """
        from .api_client import APIClient
        temp = APIClient(
            api_key=api_key,
            model=model or "gemini-2.0-flash",
            provider=provider,
            base_url=base_url,
        )
        ok, err = temp.validate_key()
        return {"valid": ok, "error": err}

    # ── File Operations ────────────────────────────────────────────────────────

    def save_sql(self, sql_text: str, wcid: int, name: str) -> dict:
        try:
            output_dir = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subfolder = Path(output_dir) / f"manual_{timestamp}"
            subfolder.mkdir(parents=True, exist_ok=True)

            safe_name = name.lower().replace(" ", "_").replace("'", "")[:40]
            filename  = f"{wcid}_{safe_name}.sql"
            fpath     = subfolder / filename
            fpath.write_text(sql_text, encoding="utf-8")
            return {"success": True, "path": str(fpath), "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_ai_files(self, full_response: str, content_type: str) -> dict:
        try:
            output_dir = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subfolder = f"{content_type}_{timestamp}"
            written   = parse_and_save_files(full_response, output_dir, subfolder)
            return {
                "success": True,
                "files":  [os.path.basename(f) for f in written],
                "count":  len(written),
                "folder": str(Path(output_dir) / subfolder),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_output_folder(self) -> dict:
        try:
            path = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            Path(path).mkdir(parents=True, exist_ok=True)
            os.startfile(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── AI Generation ─────────────────────────────────────────────────────────

    def start_generation(self, prompt: str, content_type: str) -> dict:
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured. Open Settings and add your API key."}

        self._generating = True
        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        system_prompt = self.skill_loader.build_system_prompt(
            content_type=content_type,
            server_name=self.config.server_name,
            wcid_ranges=self.config.get_wcid_ranges(),
            author=self.config.get("author", ""),
        )

        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system_prompt, prompt, self._on_chunk, self._on_done, self._on_error),
            daemon=True,
        ).start()
        return {"success": True}

    def stop_generation(self) -> dict:
        self._generating = False
        return {"success": True}

    def _on_chunk(self, text: str):
        if not self._generating:
            return
        if self._window:
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('ai_chunk',{{detail:{json.dumps(text)}}}))"
            )

    def _on_done(self, text: str):
        self._generating = False
        if self._window:
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('ai_done',{{detail:{json.dumps(text)}}}))"
            )

    def _on_error(self, message: str):
        self._generating = False
        if self._window:
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('ai_error',{{detail:{json.dumps(message)}}}))"
            )

    def get_version(self) -> str:
        return "1.0.0"
