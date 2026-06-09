"""
ACEForge App API
Python methods exposed to the JavaScript frontend via pywebview's js_api.
Called from JS as: window.pywebview.api.method_name(args)
"""

import queue
from aceforge.lore_api import LoreMixin
import threading
import json
import os
from pathlib import Path
from datetime import datetime

from .config import Config
from .skill_loader import SkillLoader
from .api_client import APIClient, KNOWN_ENDPOINTS, DEFAULT_MODELS
from .sql_parser import parse_and_save_files
from .emote_parser import parse_emote_text


class AppAPI(LoreMixin):
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
        self._chunk_queue      = queue.Queue()
        self._last_ai_response = ''  # stored Python-side to avoid bridge size limit

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

    # ── Emote Parser ──────────────────────────────────────────────────────────

    def convert_emotes(self, emote_text: str, wcid: int) -> dict:
        """
        Convert WeenieFab compact emote text → ACEmulator SQL.
        Called from JS as: window.pywebview.api.convert_emotes(text, wcid)

        Returns:
            {
              success:      bool,
              sql:          str,       # ready-to-paste SQL
              warnings:     [str],     # non-fatal parser warnings
              emote_count:  int,
              action_count: int,
              error:        str|None,
            }
        """
        try:
            if not emote_text or not emote_text.strip():
                return {
                    "success": False, "sql": "", "warnings": [],
                    "emote_count": 0, "action_count": 0,
                    "error": "Emote text is empty.",
                }
            try:
                wcid = int(wcid)
            except (TypeError, ValueError):
                wcid = 850000

            result = parse_emote_text(emote_text, wcid)
            if result["error"]:
                return {
                    "success": False,
                    "sql":          "",
                    "warnings":     result["warnings"],
                    "emote_count":  0,
                    "action_count": 0,
                    "error":        result["error"],
                }
            return {
                "success":      True,
                "sql":          result["sql"],
                "warnings":     result["warnings"],
                "emote_count":  result["emote_count"],
                "action_count": result["action_count"],
                "blocks":       result.get("blocks", []),
                "error":        None,
            }
        except Exception as e:
            import traceback
            return {
                "success":      False,
                "sql":          "",
                "warnings":     [traceback.format_exc()],
                "emote_count":  0,
                "action_count": 0,
                "error":        str(e),
            }

    def start_planning(self, prompt: str, content_type: str, existing_sql: str = '') -> dict:
        """Phase 1: Ask AI to produce a JSON plan of files needed."""
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured."}

        self._generating = True
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break

        wcid_ranges = self.config.get_wcid_ranges()
        server_name = self.config.server_name or "Shattered Dawn"

        edit_mode = bool(existing_sql and existing_sql.strip())
        system_prompt = f"""You are an ACEmulator content {"editor" if edit_mode else "planner"} for the server "{server_name}".
Analyze the user request and produce a complete JSON file plan.

CRITICAL INSTRUCTIONS — READ CAREFULLY:
1. You MUST list EVERY separate SQL file required to fully implement the request.
2. Do NOT collapse multiple pieces of content into one file. Each distinct weenie, NPC, item, quest, or generator needs its OWN entry.
3. If the user requests 10 monsters, plan 10 creature files PLUS 10 generator files = 20 entries.
4. If the user requests a questline, plan every NPC, every item reward, every kill contract, and every generator needed.
5. Do not summarize or reduce. Be complete. More files is better than fewer.

Respond with ONLY a valid JSON object. No markdown fences, no explanation, no extra text before or after.

JSON format (use exactly this structure):
{{
  "summary": "one sentence describing what will be created",
  "files": [
    {{"index": 0, "name": "WCID DescriptiveName.sql", "type": "creature", "wcid": 800001, "description": "brief description"}},
    {{"index": 1, "name": "WCID DescriptiveName Generator.sql", "type": "generator", "wcid": 810001, "description": "spawner for WCID 800001"}}
  ]
}}

WCID ranges for {server_name}:
- Creatures/Mobs: 800000-809999
- Items/Custom objects: 810000-819999
- Portals: 820000-829999
- Bosses: 840000-849999
- NPCs (quest givers, vendors): 850000-859999
- Kill Contracts: 860000-869999
- Custom Gear/Jewelry: 870000-879999
- Generators: creature_wcid + 10000 (e.g. creature 800001 → generator 810001)

File planning rules:
- One file per weenie (creature, NPC, item, weapon, armor, quest, generator)
- Assign unique WCIDs in the correct range — no duplicates
- Order files: items/rewards first, then creatures/NPCs, then quests, then generators last
- Name format: "WCID DescriptiveName.sql"
- Every creature or NPC MUST have a paired generator file so it spawns in world
- Generator WCID = creature_wcid + 10000 (if that range is taken, use creature_wcid + 5000)

Think step by step before writing JSON:
- What distinct creatures/NPCs does this request need?
- What items or rewards are needed?
- What quests or kill contracts are needed?
- What generators are needed (one per creature/NPC)?
Count all of the above, then write that many entries in the files array."""

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        def _plan_done(text: str):
            self._generating = False
            self._last_plan_text = text
            self._chunk_queue.put({"type": "plan_ready", "text": text})
            print(f"[PLAN] done, {len(text)} chars", flush=True)

        # In edit mode, prepend the existing SQL so AI knows what to modify
        planning_prompt = prompt
        if existing_sql and existing_sql.strip():
            # Store for use by generate_planned_file
            self._editing_sql = existing_sql.strip()
            planning_prompt = (
                f"EXISTING WEENIE SQL (modify this, do not create new):\n```sql\n{existing_sql[:8000]}\n```\n\n"
                f"USER REQUEST: {prompt}"
            )
        else:
            self._editing_sql = ""

        try:
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, planning_prompt, self._on_chunk, _plan_done, self._on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": str(e)}
        return {"success": True}

    def generate_planned_file(self, plan_json: str, file_index: int,
                              original_prompt: str, existing_sql: str = '') -> dict:
        """Phase 2: Generate SQL for one specific file from the plan."""
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured."}

        try:
            plan = json.loads(plan_json)
            file_entry = plan["files"][file_index]
        except Exception as e:
            return {"success": False, "error": f"Plan parse error: {e}"}

        server_name = self.config.server_name or "Shattered Dawn"
        fname = file_entry.get("name", "output.sql")
        ftype = file_entry.get("type", "creature")
        wcid  = file_entry.get("wcid", 800000)
        fdesc = file_entry.get("description", "")
        total = len(plan.get("files", []))

        # In edit mode, prefer stored SQL from planning phase
        if not existing_sql:
            existing_sql = getattr(self, "_editing_sql", "")

        # Build context about other files for cross-references
        other_files = [f for i, f in enumerate(plan["files"]) if i != file_index]
        ref_ctx = "\n".join(
            f"- WCID {f['wcid']}: {f['name']} ({f['description']})"
            for f in other_files
        ) or "None"

        # Load the skill system prompt for this content type
        try:
            weenie_context = self._build_weenie_context(original_prompt, ftype)
            skill_system = self.skill_loader.build_system_prompt(
                content_type=ftype,
                server_name=server_name,
                wcid_ranges=self.config.get_wcid_ranges(),
                author=self.config.get("author", ""),
                weenie_context=weenie_context,
                is_local=False,
            )
        except Exception:
            skill_system = f"You are an ACEmulator SQL expert for {server_name}."

        system_prompt = f"""{skill_system}

You are generating FILE {file_index + 1} of {total} in a planned sequence.
Generate ONLY this one file. Do not generate other files.

File to generate: {fname}
WCID: {wcid}
Type: {ftype}
Description: {fdesc}

Other files in this sequence (for WCID cross-references if needed):
{ref_ctx}

EMOTE TRIGGER RULES — STRICTLY ENFORCED:
Valid top-level emote triggers: Use, GotoSet, ReceiveTalkDirect, HeartBeat, Death,
Give, Wield, UnWield, PickUp, Drop, Vendor, Activation, Taunt, WoundedTaunt,
KillTaunt, NewEnemy, Scream, Homesick, ReceiveCritical, ResistSpell, HearChat,
ReceiveLocalSignal.
INVALID triggers that DO NOT EXIST — never use: ReceiveGive, ReceiveItem, OnKill,
OnDeath, OnGive, QuestComplete, PlayerNear.
Use Give: (not ReceiveGive) when an NPC receives an item. Inside Give:, use
InqOwnsItems to check which specific item was given.

Output the complete SQL for ONLY this file.
Start with: /* ===== FILE: {fname} ===== */"""

        self._generating = True
        self._last_ai_response = ""
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        edit_ctx = (
            f"EXISTING WEENIE SQL TO MODIFY:\n```sql\n{existing_sql[:8000]}\n```\n\n"
            if existing_sql else ""
        )
        file_prompt = (
            edit_ctx
            + f"Generate the SQL for: {fdesc}\n"
            + f"Original request: {original_prompt}\n"
            + f"File name: {fname} | WCID: {wcid}"
        )

        def _file_done(text: str):
            self._generating = False
            save_result = {"success": False, "error": "Unknown error in _file_done"}
            try:
                text = self._process_emote_scripts(text)   # convert WeenieFab blocks → SQL
                self._last_ai_response = text
                save_result = self._save_single_file(text, fname)
            except Exception as e:
                print(f"[FILE] _file_done error (file {file_index+1}/{total}): {e}", flush=True)
                save_result = {"success": False, "error": str(e)}
            finally:
                # Always queue file_done so the JS poll doesn't hang forever
                self._chunk_queue.put({
                    "type": "file_done",
                    "file_index": file_index,
                    "file_name": fname,
                    "save": save_result,
                    "total": total,
                })
                print(f"[FILE] {file_index+1}/{total} queued done: {fname}", flush=True)

        def _file_gen_worker():
            try:
                self.api_client.stream_generate(
                    system_prompt, file_prompt, self._on_chunk, _file_done, self._on_error
                )
            except Exception as e:
                print(f"[FILE] Thread crashed: {e}", flush=True)
                self._generating = False
                self._chunk_queue.put({
                    "type": "error",
                    "message": f"File {file_index+1}/{total} thread crashed: {e}",
                })
        try:
            threading.Thread(target=_file_gen_worker, daemon=True).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": str(e)}
        return {"success": True}

    def _save_single_file(self, content: str, suggested_name: str) -> dict:
        """Save one AI-generated SQL file immediately."""
        try:
            output_dir = str(self.config.output_dir or "").strip()
            if not output_dir:
                output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            written = parse_and_save_files(content, output_dir, subfolder="")
            if not written:
                # Fallback: save with suggested name
                from aceforge.sql_parser import sanitize_filename, clean_sql
                fname = sanitize_filename(suggested_name)
                fpath = Path(output_dir) / fname
                fpath.write_text(clean_sql(content), encoding="utf-8")
                written = [str(fpath)]
            return {
                "success": True,
                "files": [os.path.basename(f) for f in written],
                "folder": output_dir,
            }
        except Exception as e:
            import traceback
            print(f"[SAVE] error: {traceback.format_exc()}", flush=True)
            return {"success": False, "error": str(e)}


    def continue_generation(self, pass_num: int) -> dict:
        """Continue a truncated generation — appends to _last_ai_response."""
        if self._generating:
            return {"success": False, "error": "Already generating."}

        tail = self._last_ai_response[-600:] if self._last_ai_response else ""
        if not tail:
            return {"success": False, "error": "No previous output to continue from."}

        continuation_prompt = (
            "Continue generating exactly where you left off. "
            "Do NOT restate the file header or any SQL already written. "
            "Do NOT add introductory text. "
            "Begin IMMEDIATELY from after this last line:\n\n"
            f"...{tail}"
        )
        # Minimal system prompt for continuation
        system_prompt = (
            "You are continuing an ACEmulator SQL generation. "
            "Output only raw SQL continuation with /* ===== FILE: name.sql ===== */ "
            "markers for any new files. No markdown fences, no explanations."
        )
        self._generating = True
        self._continuation_pass = pass_num

        def _on_done_continuation(text: str):
            self._generating = False
            text = self._process_emote_scripts(text)   # convert WeenieFab blocks → SQL
            self._last_ai_response = self._last_ai_response + "\n" + text
            stripped = text.rstrip()
            looks_truncated = bool(stripped) and not any(
                stripped.endswith(s) for s in (";", "*/", "---", "```")
            )
            self._chunk_queue.put({
                "type": "done",
                "truncated": looks_truncated,
                "pass": pass_num,
            })
            print(f"[API] continuation pass {pass_num} done, appended {len(text)} chars", flush=True)

        try:
            self.api_client.update_credentials(
                api_key=self.config.api_key,
                model=self.config.model,
                provider=self.config.provider,
                base_url=self.config.base_url,
            )
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, continuation_prompt,
                      self._on_chunk, _on_done_continuation, self._on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": str(e)}
        return {"success": True}


    def save_ai_files(self, content_type: str = "creature") -> dict:
        try:
            full_response = self._last_ai_response
            if not full_response:
                return {"success": False, "error": "No content to save — generate first."}
            output_dir = str(self.config.output_dir or "").strip()
            if not output_dir:
                output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")
            # Ensure output dir exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            written = parse_and_save_files(full_response, output_dir, subfolder="")
            if not written:
                return {"success": False, "error": "Parser found no SQL content in response. Ensure AI output contains FILE: markers or valid SQL."}
            return {
                "success": True,
                "files":  [os.path.basename(f) for f in written],
                "count":  len(written),
                "folder": output_dir,
            }
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied writing to output directory: {e}"}
        except Exception as e:
            import traceback
            print(f"[SAVE] exception: {traceback.format_exc()}", flush=True)
            return {"success": False, "error": str(e)}

    # ── Content Libraries ─────────────────────────────────────────────────────



    def import_sql(self) -> dict:
        """Open a file dialog and return SQL file content for import into the builder.
        Uses pywebview native dialog (works in both dev and EXE mode)."""
        from pathlib import Path
        try:
            if self._window is None:
                return {"error": "Window not ready — call set_window() first."}
            result = self._window.create_file_dialog(
                dialog_type=10,          # OPEN_DIALOG
                allow_multiple=False,
                file_types=("SQL Files (*.sql)", "All Files (*.*)")
            )
            if not result:
                return {"cancelled": True}
            path = result[0] if isinstance(result, (list, tuple)) else result
        except Exception as e:
            # Fallback: tkinter (dev mode without pywebview window)
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw()
                path = filedialog.askopenfilename(
                    title="Import SQL File",
                    filetypes=[("SQL files", "*.sql"), ("All files", "*.*")]
                )
                root.destroy()
                if not path:
                    return {"cancelled": True}
            except Exception as e2:
                return {"error": f"File dialog unavailable: {e2}"}
        if not path:
            return {"cancelled": True}
        try:
            content = Path(path).read_text(encoding='utf-8', errors='ignore')
            return {
                "path": str(path),
                "filename": Path(path).name,
                "content": content,
                "size": len(content),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_icons_data(self) -> list:
        """
        Return the ICONS array from icons.js for the icon picker.
        In frozen (.exe) mode sys._MEIPASS is a temp dir that changes each run,
        so we read from the persistent directory beside the executable instead.
        """
        import sys, json, re
        from pathlib import Path

        # Persistent base: next to the .exe when frozen, or next to this file in dev
        if getattr(sys, 'frozen', False):
            persistent_base = Path(sys.executable).parent / 'aceforge'
        else:
            persistent_base = Path(__file__).parent

        icons_js = persistent_base / 'web' / 'icons.js'

        # Also check next to the exe directly (some install layouts)
        if not icons_js.exists():
            icons_js = Path(sys.executable).parent / 'aceforge' / 'web' / 'icons.js'
        if not icons_js.exists():
            icons_js = Path(sys.executable).parent / 'web' / 'icons.js'

        if not icons_js.exists():
            return []

        try:
            text = icons_js.read_text(encoding='utf-8', errors='ignore')
            # Extract the array literal: const ICONS = [...];
            m = re.search(r'(?:const|var|let)\s+ICONS\s*=\s*(\[.*?\])\s*;?\s*$', text, re.DOTALL)
            if m:
                return json.loads(m.group(1))
            return []
        except Exception:
            return []

    def build_icon_cats(self):
        """Run generate_icon_cats.py and return result to JS."""
        import subprocess, sys, os, re
        script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generate_icon_cats.py")
        if not os.path.exists(script):
            return {"ok": False, "error": "generate_icon_cats.py not found in ACEForge root."}
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
            m = re.search(r"Unique icon DIDs: (\d+)", result.stdout)
            return {"ok": True, "count": int(m.group(1)) if m else 0}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timed out after 120 seconds."}
        except Exception as e:
            return {"ok": False, "error": str(e)}


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
                        # Count entries — icons.js uses "], [" separator
                        n = text.count("], [") + text.count("],[") + 1
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
                        # Use persistent dir (beside .exe) so files survive restarts
                        import sys as _sys
                        if getattr(_sys, "frozen", False):
                            _persistent = Path(_sys.executable).parent / "aceforge"
                        else:
                            _persistent = Path(__file__).parent
                        web_dir  = _persistent / "web"
                        icon_dst = web_dir / "icons"
                        icon_dst.mkdir(parents=True, exist_ok=True)
                        extracted = 0
                        png_members = [m for m in names
                                       if "/icons/" in m.lower() or m.lower().startswith("icons/")]
                        total_pngs = len(png_members)
                        # First pass: extract icons.js
                        for member in names:
                            if member.lower().endswith("icons.js"):
                                (web_dir / "icons.js").write_bytes(zf.read(member))
                                self._lib_progress(f"Installing icon library…", 0, total_pngs)
                                break
                        # Second pass: extract PNGs with progress
                        for member in png_members:
                            pname = Path(member).name
                            if pname.endswith(".png"):
                                (icon_dst / pname).write_bytes(zf.read(member))
                                extracted += 1
                                if extracted % 500 == 0 or extracted == total_pngs:
                                    self._lib_progress(
                                        f"Installing icons… {extracted:,} / {total_pngs:,}",
                                        extracted, total_pngs
                                    )
                        self._lib_progress("Icon library ready", total_pngs, total_pngs)
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
                        # Pre-count SQL members for progress
                        sql_members = [m for m in names
                                       if not m.endswith("/") and (
                                           "weenie_index.json" in m or
                                           m.endswith(".sql")
                                       )]
                        total = len(sql_members)
                        processed = 0
                        self._lib_progress("Installing weenie database…", 0, total)

                        for member in names:
                            if member.endswith("/"):
                                continue
                            pobj = Path(member)
                            parts = pobj.parts
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
                            processed += 1
                            if processed % 1000 == 0 or processed == total:
                                self._lib_progress(
                                    f"Installing weenies… {processed:,} / {total:,}",
                                    processed, total
                                )
                        try:
                            self.skill_loader._load_weenie_index()
                        except Exception:
                            pass
                        self._lib_progress("Weenie database ready", total, total)
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

    # ── Auto-Update ────────────────────────────────────────────────────────────

    APP_VERSION = "1.9.2"
    GITHUB_REPO = "shemtar-90/AceForge"

    def check_for_update(self) -> dict:
        """
        Check GitHub releases API for a newer version.
        Returns {has_update, latest_version, current_version, download_url, release_notes}
        """
        import urllib.request, json as _json
        try:
            url = f"https://api.github.com/repos/{self.GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "ACEForge-Updater/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = _json.loads(resp.read())
            
            latest_tag  = data.get("tag_name", "").lstrip("v")
            release_name = data.get("name", latest_tag)
            body        = data.get("body", "")[:500]
            
            # Find the main zip asset
            assets = data.get("assets", [])
            dl_url = next(
                (a["browser_download_url"] for a in assets
                 if a["name"].lower().endswith(".zip") and "weenie" not in a["name"].lower()
                 and "icon" not in a["name"].lower()),
                data.get("zipball_url", "")
            )
            
            # Semantic version compare
            def vparse(v):
                try: return tuple(int(x) for x in v.split("."))
                except: return (0,)
            
            has_update = vparse(latest_tag) > vparse(self.APP_VERSION)
            
            return {
                "has_update":      has_update,
                "current_version": self.APP_VERSION,
                "latest_version":  latest_tag,
                "release_name":    release_name,
                "release_notes":   body,
                "download_url":    dl_url,
            }
        except Exception as e:
            return {"has_update": False, "error": str(e), "current_version": self.APP_VERSION}

    def download_and_install_update(self, download_url: str) -> dict:
        """
        Download the new release zip, extract it over the current install,
        then restart the application.
        """
        import urllib.request, zipfile, shutil, sys, os
        from pathlib import Path

        if not download_url:
            return {"success": False, "error": "No download URL provided"}

        try:
            # Determine install root (where ACEForge.exe or main.py lives)
            if hasattr(sys, "_MEIPASS"):
                install_root = Path(sys.executable).parent
            else:
                install_root = Path(__file__).parent.parent

            tmp_zip = install_root / "_update_download.zip"
            tmp_dir = install_root / "_update_extract"

            # Download with progress
            self._ollama_event("download_start", "Downloading update…", 0, 0)

            def on_progress(block, block_size, total):
                if total > 0:
                    pct = min(100, int(block * block_size * 100 / total))
                    mb  = round(block * block_size / 1024 / 1024, 1)
                    mbt = round(total / 1024 / 1024, 1)
                    self._ollama_event("download_progress",
                        f"Downloading update… {mb} MB / {mbt} MB", pct, 100)

            urllib.request.urlretrieve(download_url, str(tmp_zip), on_progress)
            self._ollama_event("download_done", "Extracting update…", 100, 100)

            # Extract
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(tmp_dir)

            # Copy new files over install root
            # Zip should have ACEForge/ at root
            src_root = next(
                (tmp_dir / d for d in os.listdir(tmp_dir)
                 if (tmp_dir / d).is_dir()), tmp_dir
            )
            for item in os.listdir(src_root):
                s = src_root / item
                d = install_root / item
                if s.is_dir():
                    if d.exists():
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

            # Cleanup
            tmp_zip.unlink(missing_ok=True)
            shutil.rmtree(tmp_dir, ignore_errors=True)

            # Restart
            self._ollama_event("download_done", "Update installed! Restarting…", 100, 100)
            import threading
            def _restart():
                time.sleep(1.5)
                os.execl(sys.executable, sys.executable, *sys.argv)
            threading.Thread(target=_restart, daemon=True).start()
            return {"success": True, "message": "Update installed. Restarting…"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_url(self, url: str) -> dict:
        """Open a URL in the system default browser."""
        import webbrowser
        webbrowser.open(url)
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
        # Clear any stale chunks from previous run
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break
        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        # Detect local model — Ollama or compatible with ollama_mode flag
        provider   = self.config.get("provider", "anthropic")
        ollama_mode = self.config.get("ollama_mode", False)
        is_local   = provider == "ollama" or bool(ollama_mode)

        # Extract keywords from prompt and find matching base-game weenies
        try:
            content_type = content_type or "creature"
            weenie_context = self._build_weenie_context(prompt, content_type)
            system_prompt = self.skill_loader.build_system_prompt(
                content_type=content_type,
                server_name=self.config.server_name,
                wcid_ranges=self.config.get_wcid_ranges(),
                author=self.config.get("author", ""),
                weenie_context=weenie_context,
                is_local=is_local,
            )
        except Exception as e:
            self._generating = False
            return {"success": False, "error": f"Prompt build error: {e}"}

        try:
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, prompt, self._on_chunk, self._on_done, self._on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": f"Failed to start generation: {e}"}
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

    # ── Ollama Setup & Management ─────────────────────────────────────────────

    def check_ollama(self) -> dict:
        """
        Full Ollama status check. Returns:
          installed  — ollama binary found
          running    — localhost:11434 is responding
          models     — list of locally installed model names
          path       — path to ollama binary (or empty)
          recommended — recommended models with name/size/desc
        """
        import shutil, urllib.request, json as _json, os

        RECOMMENDED = [
            {"id": "qwen2.5-coder:7b",  "label": "Qwen 2.5 Coder 7B",  "size": "4.5 GB",
             "desc": "Best for SQL — trained on structured data and code schemas. Recommended."},
            {"id": "codellama:7b",       "label": "CodeLlama 7B",        "size": "3.8 GB",
             "desc": "Meta's code-focused model. Good SQL, reliable formatting."},
            {"id": "llama3.2:3b",        "label": "Llama 3.2 3B",        "size": "2.0 GB",
             "desc": "Fastest, lowest RAM. Less accurate for complex quest chains."},
        ]

        # Find binary
        path = shutil.which("ollama") or ""
        if not path:
            win_path = os.path.join(
                os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
            )
            if os.path.exists(win_path):
                path = win_path

        installed = bool(path)

        # Check if running
        running = False
        models  = []
        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/tags",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = _json.loads(resp.read())
                running = True
                models  = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass

        return {
            "installed":    installed,
            "running":      running,
            "models":       models,
            "path":         path,
            "recommended":  RECOMMENDED,
        }

    def launch_ollama(self) -> dict:
        """Start `ollama serve` as a background subprocess, then wait until ready."""
        import subprocess, time, urllib.request, shutil, os

        path = shutil.which("ollama") or os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
        )
        if not path or not os.path.exists(path):
            return {"success": False, "error": "Ollama binary not found. Please install it first."}

        try:
            # Start silently (no console window on Windows)
            flags = 0
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                flags = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(
                [path, "serve"],
                creationflags=flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            return {"success": False, "error": str(e)}

        # Poll until ready (up to 15 seconds)
        for _ in range(15):
            time.sleep(1)
            try:
                urllib.request.urlopen("http://localhost:11434/", timeout=1)
                return {"success": True, "message": "Ollama started successfully"}
            except Exception:
                pass

        return {"success": False, "error": "Ollama started but did not respond in time. Try again."}

    def install_ollama(self) -> dict:
        """
        Download OllamaSetup.exe and launch the installer.
        Streams download progress via ollama_progress events.
        """
        import urllib.request, tempfile, os, subprocess

        URL  = "https://ollama.com/download/OllamaSetup.exe"
        dest = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")

        self._ollama_event("download_start", "Downloading Ollama installer…", 0, 0)
        try:
            def on_progress(block, block_size, total):
                if total > 0:
                    pct = min(100, int(block * block_size * 100 / total))
                    mb_done = round(block * block_size / 1024 / 1024, 1)
                    mb_total = round(total / 1024 / 1024, 1)
                    self._ollama_event(
                        "download_progress",
                        f"Downloading Ollama… {mb_done} MB / {mb_total} MB",
                        pct, 100
                    )
            urllib.request.urlretrieve(URL, dest, on_progress)
        except Exception as e:
            return {"success": False, "error": f"Download failed: {e}"}

        self._ollama_event("download_done", "Launching installer…", 100, 100)

        try:
            subprocess.Popen([dest], shell=False)
            return {
                "success": True,
                "message": "Installer launched. Complete installation, then click 'Check Again'."
            }
        except Exception as e:
            return {"success": False, "error": f"Could not launch installer: {e}"}

    def pull_ollama_model(self, model: str) -> dict:
        """
        Run `ollama pull MODEL` and stream progress via ollama_progress events.
        Runs in a background thread so the UI stays responsive.
        """
        import subprocess, threading, re, shutil, os

        path = shutil.which("ollama") or os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
        )
        if not path:
            return {"success": False, "error": "Ollama not found."}

        def _run():
            try:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                proc = subprocess.Popen(
                    [path, "pull", model],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=flags,
                    encoding="utf-8",
                    errors="replace",   # swap undecodable bytes with ? instead of crashing
                )
                last_pct = -1
                for line in proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    # Parse: "pulling abc123...  42% ▕███▏  1.8 GB/4.5 GB"
                    m = re.search(r"(\d+)%", line)
                    gb = re.search(r"([\d.]+\s*GB/[\d.]+\s*GB)", line)
                    if m:
                        pct = int(m.group(1))
                        size_label = gb.group(1) if gb else ""
                        if pct != last_pct:
                            last_pct = pct
                            self._ollama_event(
                                "pull_progress",
                                f"Downloading {model}… {size_label or str(pct)+'%'}",
                                pct, 100
                            )
                    elif line:
                        self._ollama_event("pull_status", line, last_pct if last_pct >= 0 else 0, 100)

                proc.wait()
                if proc.returncode == 0:
                    self._ollama_event("pull_done", f"{model} installed and ready", 100, 100)
                    # Auto-configure ACEForge to use this model
                    self.config.set("provider",   "compatible")
                    self.config.set("base_url",   "http://localhost:11434/v1")
                    self.config.set("model",       model)
                    self.config.set("ollama_mode", True)
                    self.config.save()
                    self._ollama_event("auto_configured", model, 100, 100)
                else:
                    self._ollama_event("pull_error", f"Pull failed (exit {proc.returncode})", 0, 100)
            except Exception as e:
                self._ollama_event("pull_error", str(e), 0, 100)

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True, "message": f"Pulling {model} — this may take several minutes…"}

    def _ollama_event(self, event: str, message: str, current: int, total: int):
        """Send an ollama_setup event to the UI."""
        if self._window:
            import json as _json
            payload = _json.dumps({
                "event":   event,
                "message": message,
                "current": current,
                "total":   total,
            })
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('ollama_setup',{{detail:{payload}}}))"
            )

    def _lib_progress(self, message: str, current: int, total: int):
        """Push a library installation progress event to the UI."""
        if self._window:
            import json as _json
            payload = _json.dumps({"message": message, "current": current, "total": total})
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('lib_progress',{{detail:{payload}}}))"
            )

    def stop_generation(self) -> dict:
        self._generating = False
        return {"success": True}


    # ── Emote Script Post-Processor ───────────────────────────────────────────

    def _process_emote_scripts(self, text: str) -> str:
        """
        Scan AI output for WeenieFab emote blocks and convert them to SQL.

        Marker format (written by AI):
            -- EMOTE SCRIPT (WCID: 850000)
            Use:
                - Tell: Hello!
            -- END EMOTE SCRIPT

        Each block is replaced with the converted SQL in-place.
        Conversion errors are left as SQL comments so the file is still usable.
        """
        import re
        pattern = re.compile(
            r'--\s*EMOTE SCRIPT\s*\(WCID:\s*(\d+)\)\s*\n(.*?)\n\s*--\s*END EMOTE SCRIPT',
            re.DOTALL | re.IGNORECASE,
        )

        def _replace(m: re.Match) -> str:
            wcid   = int(m.group(1))
            script = m.group(2).strip()
            if not script:
                return ''
            try:
                result = parse_emote_text(script, wcid)
                if result['error']:
                    return (
                        f'-- EMOTE CONVERSION ERROR: {result["error"]}\n'
                        f'-- Original script preserved below:\n'
                        + m.group(0)
                    )
                # Prefix with summary comment
                header = (
                    f'-- Emote rows: {result["emote_count"]}  '
                    f'Action rows: {result["action_count"]}\n'
                )
                warnings = ''.join(
                    f'-- WARN: {w}\n' for w in result['warnings']
                )
                return header + warnings + result['sql']
            except Exception as exc:
                return (
                    f'-- EMOTE CONVERSION EXCEPTION: {exc}\n'
                    + m.group(0)
                )

        converted = pattern.sub(_replace, text)
        n_blocks   = len(pattern.findall(text))
        if n_blocks:
            print(f'[EMOTE] converted {n_blocks} emote block(s)', flush=True)
        return converted

    def _on_chunk(self, text: str):
        if not self._generating:
            return
        self._chunk_queue.put({"type": "chunk", "text": text})
        print(f"[API] chunk queued: {len(text)} chars, queue size ~{self._chunk_queue.qsize()}", flush=True)

    def _on_done(self, text: str):
        self._generating = False
        text = self._process_emote_scripts(text)   # convert WeenieFab blocks → SQL
        self._last_ai_response = text              # store full text Python-side (avoid bridge size limit)
        stripped = text.rstrip()
        looks_truncated = bool(stripped) and not any(
            stripped.endswith(s) for s in (";", "*/", "---", "```")
        )
        self._chunk_queue.put({"type": "done", "truncated": looks_truncated})
        print(f"[API] done queued, total chars: {len(text)}", flush=True)

    def _on_error(self, message: str):
        self._generating = False
        self._chunk_queue.put({"type": "error", "message": message})
        print(f"[API] error queued: {message}", flush=True)

    def poll_generation(self) -> dict:
        """Called by JS every 100ms — drains the queue and returns all pending items."""
        items = []
        try:
            while True:
                items.append(self._chunk_queue.get_nowait())
        except queue.Empty:
            pass
        if items:
            print(f"[API] poll returning {len(items)} items", flush=True)
        return {"items": items, "generating": self._generating}


    def get_version(self) -> str:
        return "2.1.polling"

    def ping(self) -> dict:
        """Connectivity test — confirms new code is loaded."""
        return {"ok": True, "version": "2.1.polling", "queue_ready": hasattr(self, "_chunk_queue")}
