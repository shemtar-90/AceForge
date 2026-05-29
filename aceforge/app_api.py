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
            "auto_open_folder": self.config.get("auto_open_folder", True),
            "ollama_mode":     self.config.get("ollama_mode", False),
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
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            safe_name = name.lower().replace(" ", "_").replace("'", "")[:40]
            filename  = f"{wcid} {name}.sql"
            fpath     = out_path / filename
            fpath.write_text(sql_text, encoding="utf-8")
            return {"success": True, "path": str(fpath), "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_ai_files(self, full_response: str, content_type: str) -> dict:
        try:
            output_dir = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            # Save all files flat into output_dir — no per-generation subfolder
            written = parse_and_save_files(full_response, output_dir, subfolder="")
            return {
                "success": True,
                "files":  [os.path.basename(f) for f in written],
                "count":  len(written),
                "folder": output_dir,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Content Libraries ─────────────────────────────────────────────────────

    def get_library_status(self) -> list:
        """Return status of all installable content libraries."""
        import json
        from pathlib import Path

        base = Path(__file__).parent
        refs = base / "references"
        web  = base / "web"

        libraries = [
            {
                "id":     "icons",
                "name":   "Icon Library",
                "file":   str(web / "icons.js"),
                "check":  web / "icons.js",
                "hint":   "icons.js — contains all game icon DIDs",
            },
            {
                "id":     "weenies",
                "name":   "Weenie Database",
                "file":   str(refs / "weenie_index.json"),
                "check":  refs / "weenie_index.json",
                "hint":   "weenie_index.json — 29,569 base-game weenie entries",
            },
        ]

        result = []
        for lib in libraries:
            loaded  = lib["check"].exists()
            count   = ""
            if loaded:
                try:
                    text = lib["check"].read_text(encoding="utf-8", errors="replace")
                    if lib["id"] == "icons":
                        # Count entries in ICONS=[...] array
                        import re
                        m = re.search(r"\[([^\]]+)\]", text[:200])
                        n = text.count("],[") + (1 if "],[" not in text and "[" in text else 0)
                        count = f"{n:,} icons loaded"
                    elif lib["id"] == "weenies":
                        data = json.loads(text)
                        count = f"{len(data):,} weenies loaded"
                except Exception:
                    count = "loaded"
            result.append({
                "id":     lib["id"],
                "name":   lib["name"],
                "loaded": loaded,
                "status": count if loaded else f"Not installed — load {lib['hint']}",
            })

        return result

    def browse_and_load_index(self) -> dict:
        """
        Open OS file browser. Accepts:
          - ACEForge_Icons.zip    → extracts icons.js + icons/ to web/
          - ACEForge_WeenieDB.zip → extracts weenie_index.json + weenies/ to references/
          - icons.js              → copies to web/
          - weenie_index.json     → copies to references/ (+ adjacent weenies/ folder)
        Future index types: add a LIBRARY_MAP entry and a handler block below.
        """
        import shutil, zipfile, json, io
        from pathlib import Path

        if not self._window:
            return {"success": False, "error": "No window available"}

        try:
            import webview
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=(
                    "ACEForge Packages (*.zip;*.js;*.json)",
                    "Zip Package (*.zip)",
                    "All Files (*.*)",
                ),
            )
        except Exception as e:
            return {"success": False, "error": f"File dialog error: {e}"}

        if not result:
            return {"success": False, "cancelled": True}

        src_path = Path(result[0])
        if not src_path.exists():
            return {"success": False, "error": "Selected file not found"}

        base  = Path(__file__).parent
        fname = src_path.name.lower()

        # ── ZIP PACKAGE — auto-extract to correct locations ────────────────
        if fname.endswith(".zip"):
            try:
                with zipfile.ZipFile(src_path, "r") as zf:
                    names = zf.namelist()

                    # Detect package type from zip contents
                    has_icons_js      = any(n.endswith("icons.js")          for n in names)
                    has_weenie_index  = any(n.endswith("weenie_index.json") for n in names)
                    has_icon_pngs     = any("/icons/" in n or n.startswith("icons/") for n in names)
                    has_weenie_sql    = any("/weenies/" in n or n.startswith("weenies/") for n in names)

                    if not has_icons_js and not has_weenie_index:
                        return {"success": False,
                                "error": "Zip not recognized. Expected ACEForge_Icons.zip or ACEForge_WeenieDB.zip."}

                    # ── ICONS PACKAGE ──────────────────────────────────────
                    if has_icons_js:
                        web_dir  = base / "web"
                        icon_dst = web_dir / "icons"
                        icon_dst.mkdir(parents=True, exist_ok=True)
                        extracted = 0
                        for member in names:
                            mlow = member.lower()
                            # Strip any leading path prefix (ACEForge/aceforge/web/ or flat)
                            if mlow.endswith("icons.js"):
                                data = zf.read(member)
                                (web_dir / "icons.js").write_bytes(data)
                            elif "/icons/" in mlow or mlow.startswith("icons/"):
                                # Extract PNG to icons/ folder, basename only
                                pname = Path(member).name
                                if pname.endswith(".png"):
                                    data = zf.read(member)
                                    (icon_dst / pname).write_bytes(data)
                                    extracted += 1
                        return {"success": True,
                                "message": f"Icon library installed — {extracted:,} icons"}

                    # ── WEENIE DATABASE PACKAGE ────────────────────────────
                    if has_weenie_index:
                        refs_dir   = base / "references"
                        weenie_dst = refs_dir / "weenies"
                        refs_dir.mkdir(parents=True, exist_ok=True)
                        weenie_dst.mkdir(parents=True, exist_ok=True)
                        count = 0
                        sql_count = 0
                        for member in names:
                            mlow = member.lower()
                            if member.endswith("/"):
                                continue
                            # Strip any leading path prefix
                            pobj = Path(member)
                            # Find the meaningful part (after any ACEForge/aceforge/references/)
                            parts = pobj.parts
                            # Find index of "weenie_index.json" or "weenies" in parts
                            rel = None
                            for i, p in enumerate(parts):
                                if p == "weenie_index.json" or p == "weenies":
                                    rel = Path(*parts[i:])
                                    break
                            if rel is None:
                                continue
                            data = zf.read(member)
                            dst  = refs_dir / rel
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            dst.write_bytes(data)
                            if rel.name == "weenie_index.json":
                                try:
                                    count = len(json.loads(data.decode("utf-8", errors="replace")))
                                except Exception:
                                    pass
                            elif rel.name.endswith(".sql"):
                                sql_count += 1
                        try:
                            self.skill_loader._load_weenie_index()
                        except Exception:
                            pass
                        extra = f" + {sql_count:,} SQL files" if sql_count else ""
                        return {"success": True,
                                "message": f"Weenie database installed — {count:,} entries{extra}"}

            except zipfile.BadZipFile:
                return {"success": False, "error": "Invalid zip file."}
            except Exception as e:
                return {"success": False, "error": f"Extraction failed: {e}"}

        # ── INDIVIDUAL FILES (fallback for direct file loading) ────────────
        elif fname == "icons.js":
            snippet = src_path.read_bytes()[:500].decode("utf-8", errors="replace")
            if "ICONS" not in snippet:
                return {"success": False, "error": "Not a valid icons.js file."}
            shutil.copy2(src_path, base / "web" / "icons.js")
            return {"success": True, "message": "Icon index installed (icons.js)"}

        elif fname == "weenie_index.json":
            try:
                data = json.loads(src_path.read_text(encoding="utf-8", errors="replace"))
                if not isinstance(data, list) or not data or "w" not in data[0]:
                    raise ValueError("wrong format")
                count = len(data)
            except Exception:
                return {"success": False,
                        "error": "Not a valid weenie_index.json — expected [{w,n,c,t,f},...]."}
            refs = base / "references"
            refs.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, refs / "weenie_index.json")
            # Copy adjacent weenies/ folder if present
            weenies_src = src_path.parent / "weenies"
            extra = ""
            if weenies_src.exists():
                weenies_dst = refs / "weenies"
                if weenies_dst.exists():
                    shutil.rmtree(weenies_dst)
                shutil.copytree(weenies_src, weenies_dst)
                extra = " + weenies folder"
            try:
                self.skill_loader._load_weenie_index()
            except Exception:
                pass
            return {"success": True, "message": f"Weenie database installed — {count:,} entries{extra}"}

        else:
            return {"success": False,
                    "error": f"Unrecognized file: '{src_path.name}'. "
                             "Select an ACEForge_Icons.zip or ACEForge_WeenieDB.zip package."}

    def unload_library(self, lib_id: str) -> dict:
        """Remove an installed content library."""
        import shutil
        from pathlib import Path

        base  = Path(__file__).parent
        paths = {
            "icons":   [base / "web" / "icons.js"],
            "weenies": [base / "references" / "weenie_index.json",
                        base / "references" / "weenies"],
        }
        targets = paths.get(lib_id, [])
        if not targets:
            return {"success": False, "error": f"Unknown library: {lib_id}"}

        for p in targets:
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.exists():
                    p.unlink()
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Reload weenie index (now empty)
        if lib_id == "weenies":
            try:
                self.skill_loader._weenie_index = None
            except Exception:
                pass

        return {"success": True}

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

        # Extract keywords from prompt and find matching base-game weenies
        weenie_context = self._build_weenie_context(prompt, content_type)

        system_prompt = self.skill_loader.build_system_prompt(
            content_type=content_type,
            server_name=self.config.server_name,
            wcid_ranges=self.config.get_wcid_ranges(),
            author=self.config.get("author", ""),
            weenie_context=weenie_context,
        )

        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system_prompt, prompt, self._on_chunk, self._on_done, self._on_error),
            daemon=True,
        ).start()
        return {"success": True}

    def _build_weenie_context(self, prompt: str, content_type: str) -> str:
        """
        Search the weenie index for base-game weenies relevant to the prompt.
        Injects 2-4 matching weenie SQL files as format/value references.
        """
        try:
            import re
            # Extract likely creature/item names from the prompt
            # Strip common adjectives and focus on noun phrases
            words = re.findall(r"[A-Za-z][a-z]{2,}", prompt)
            # Filter stop words
            STOP = {"level","high","low","with","that","this","from","into","the",
                    "and","for","has","are","can","will","give","make","create",
                    "drop","loot","kill","quest","named","custom","new","about",
                    "like","some","each","them","item","creature","weapon","armor"}
            keywords = [w for w in words if w.lower() not in STOP]

            # Search for each keyword, collect unique results
            seen_wcids = set()
            results = []
            for kw in keywords[:8]:
                matches = self.skill_loader.search_weenies(kw, max_results=2)
                for m in matches:
                    if m["w"] not in seen_wcids:
                        seen_wcids.add(m["w"])
                        results.append(m)
                if len(results) >= 4:
                    break

            if not results:
                return ""

            # Read and concatenate matching SQL files
            parts = []
            for entry in results[:4]:
                sql = self.skill_loader.get_weenie_sql(entry)
                if sql:
                    parts.append(f"/* WCID {entry['w']} — {entry['n']} ({entry['f'].split('/')[0]}) */")
                    parts.append(sql.strip())
                    parts.append("")

            return "\n".join(parts)
        except Exception:
            return ""

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
