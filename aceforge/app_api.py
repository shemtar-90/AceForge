"""
ACEForge App API
Python methods exposed to the JavaScript frontend via pywebview's js_api.
Called from JS as: window.pywebview.api.method_name(args)

All public methods must be synchronous from Python's perspective.
Streaming is handled by pushing events into the webview from a background thread.
"""

import threading
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import Config
from .skill_loader import SkillLoader
from .api_client import APIClient
from .sql_parser import parse_and_save_files


class AppAPI:
    def __init__(self, config: Config):
        self.config = config
        self.skill_loader = SkillLoader()
        self.api_client = APIClient(config.api_key, config.model)
        self._window = None
        self._generating = False

    def set_window(self, window):
        """Called by main.py after the window is created."""
        self._window = window

    # ── Configuration ─────────────────────────────────────────────────────────

    def get_config(self) -> dict:
        """Return full app config to the frontend on load."""
        return {
            "server_name": self.config.server_name,
            "author": self.config.get("author", ""),
            "output_dir": self.config.output_dir,
            "api_key_set": bool(self.config.api_key),
            "model": self.config.model,
            "wcid_ranges": self.config.get_wcid_ranges(),
        }

    def save_config(self, data: dict) -> dict:
        """Save settings from the Settings panel."""
        try:
            if "server_name" in data:
                self.config.server_name = data["server_name"]
            if "author" in data:
                self.config.set("author", data["author"])
            if "output_dir" in data:
                self.config.output_dir = data["output_dir"]
            if "api_key" in data and data["api_key"]:
                self.config.api_key = data["api_key"]
                self.api_client.update_credentials(
                    self.config.api_key, self.config.model
                )
            if "model" in data:
                self.config.model = data["model"]
                self.api_client.update_credentials(
                    self.config.api_key, self.config.model
                )
            if "wcid_ranges" in data:
                self.config.set("wcid_ranges", data["wcid_ranges"])
            self.config.save()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── File Operations ────────────────────────────────────────────────────────

    def save_sql(self, sql_text: str, wcid: int, name: str) -> dict:
        """
        Save a single weenie's SQL to the output directory.
        Called from the workbench Save File button.
        """
        try:
            output_dir = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subfolder = Path(output_dir) / f"manual_{timestamp}"
            subfolder.mkdir(parents=True, exist_ok=True)

            safe_name = (
                name.lower()
                .replace(" ", "_")
                .replace("'", "")
                .replace('"', "")[:40]
            )
            filename = f"{wcid}_{safe_name}.sql"
            fpath = subfolder / filename
            fpath.write_text(sql_text, encoding="utf-8")

            return {"success": True, "path": str(fpath), "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_ai_files(self, full_response: str, content_type: str) -> dict:
        """
        Parse an AI response into individual SQL files and save them.
        Called after AI generation completes.
        """
        try:
            output_dir = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subfolder = f"{content_type}_{timestamp}"
            written = parse_and_save_files(full_response, output_dir, subfolder)
            return {
                "success": True,
                "files": [os.path.basename(f) for f in written],
                "count": len(written),
                "folder": str(Path(output_dir) / subfolder),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_output_folder(self) -> dict:
        """Open the output folder in Windows Explorer."""
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
        """
        Begin a streaming AI generation.
        Chunks are pushed back to JS via pywebview events as they arrive.
        Returns immediately — generation runs in a background thread.
        """
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {
                "success": False,
                "error": "No API key configured. Open Settings and add your Anthropic API key.",
            }

        self._generating = True
        self.api_client.update_credentials(self.config.api_key, self.config.model)

        system_prompt = self.skill_loader.build_system_prompt(
            content_type=content_type,
            server_name=self.config.server_name,
            wcid_ranges=self.config.get_wcid_ranges(),
            author=self.config.get("author", ""),
        )

        thread = threading.Thread(
            target=self._run_generation,
            args=(system_prompt, prompt, content_type),
            daemon=True,
        )
        thread.start()
        return {"success": True}

    def stop_generation(self) -> dict:
        """Signal the generation thread to stop."""
        self._generating = False
        return {"success": True}

    def _run_generation(self, system_prompt: str, user_prompt: str, content_type: str):
        """Background thread: streams from Anthropic API, pushes events to JS."""
        full_text = []

        def on_chunk(text: str):
            if not self._generating:
                return
            full_text.append(text)
            # Push chunk to frontend
            if self._window:
                escaped = json.dumps(text)
                self._window.evaluate_js(
                    f"window.dispatchEvent(new CustomEvent('ai_chunk', {{detail: {escaped}}}))"
                )

        def on_done(text: str):
            self._generating = False
            if self._window:
                self._window.evaluate_js(
                    f"window.dispatchEvent(new CustomEvent('ai_done', {{detail: {json.dumps(text)}}}))"
                )

        def on_error(message: str):
            self._generating = False
            if self._window:
                escaped = json.dumps(message)
                self._window.evaluate_js(
                    f"window.dispatchEvent(new CustomEvent('ai_error', {{detail: {escaped}}}))"
                )

        self.api_client.stream_generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            on_chunk=on_chunk,
            on_done=on_done,
            on_error=on_error,
        )

    # ── Utilities ─────────────────────────────────────────────────────────────

    def validate_api_key(self) -> dict:
        """Quick validation of the stored API key."""
        if not self.config.api_key:
            return {"valid": False, "error": "No API key set."}
        self.api_client.update_credentials(self.config.api_key, self.config.model)
        ok, err = self.api_client.validate_key()
        return {"valid": ok, "error": err}

    def get_version(self) -> str:
        return "1.0.0"
