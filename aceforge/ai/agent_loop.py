"""
ACEForge Agentic Generation Loop
Implements true multi-turn, dependency-aware SQL generation for Advanced Generation mode.

Flow:
  1. Plan   — AI produces a JSON manifest of all files needed
  2. Approve — user reviews and approves the plan in the UI
  3. Generate — for each file in sequence:
       a. Build context: system prompt + plan + all previously-written SQL
       b. Generate the file with full dependency context
       c. Detect truncation and auto-continue if needed
       d. Self-review: validate SQL structure before saving
       e. Extract and forward WCID/name bindings to next files
       f. Save and advance

The key difference from the original generate_planned_file:
  - Previously written SQL is accumulated and passed to each subsequent call
  - WCID bindings (class_Id → class_Name → description) are extracted and forwarded
  - Truncation is detected and continued automatically without JS intervention
  - A lightweight self-review pass catches obvious structural errors before saving
"""

import re
import json
import threading
from typing import Callable, Optional
import sys as _sys
from pathlib import Path as _Path


# ── SQL structure checks ──────────────────────────────────────────────────────

REQUIRED_TABLES = {
    "creature":  ["weenie", "weenie_properties_int", "weenie_properties_d_i_d"],
    "npc":       ["weenie", "weenie_properties_int", "weenie_properties_d_i_d"],
    "boss":      ["weenie", "weenie_properties_int", "weenie_properties_d_i_d"],
    "item":      ["weenie", "weenie_properties_d_i_d"],
    "weapon":    ["weenie", "weenie_properties_int", "weenie_properties_d_i_d"],
    "armor":     ["weenie", "weenie_properties_int", "weenie_properties_d_i_d"],
    "quest":     ["quest"],
    "generator": ["weenie", "weenie_properties_generator"],
}

INVALID_TRIGGERS = [
    "ReceiveGive", "ReceiveItem", "OnKill", "OnDeath", "OnGive",
    "QuestComplete", "PlayerNear",
]

def _review_sql(sql: str, ftype: str) -> list[str]:
    """
    Lightweight structural review. Returns a list of issues found.
    Empty list = passes review.
    """
    issues = []
    sql_lower = sql.lower()

    # Must have at least one INSERT
    if "insert into" not in sql_lower:
        issues.append("No INSERT statements found — file appears empty or malformed.")

    # Must have DELETE before INSERT into weenie (idempotency)
    if "insert into `weenie`" in sql_lower and "delete from `weenie`" not in sql_lower:
        issues.append("Missing DELETE FROM `weenie` before INSERT — file is not idempotent.")

    # Check required tables
    for table in REQUIRED_TABLES.get(ftype, []):
        if table.lower() not in sql_lower:
            issues.append(f"Expected table `{table}` not found in output.")

    # Invalid emote triggers
    for trigger in INVALID_TRIGGERS:
        if trigger in sql:
            issues.append(f"Invalid emote trigger '{trigger}' used — this table/column does not exist in ACE.")

    # Unclosed SQL (truncation signal)
    stripped = sql.rstrip()
    if stripped and not any(stripped.endswith(s) for s in (";", "*/", "---")):
        issues.append("Output appears truncated — does not end with ';' or a comment block.")

    return issues


def _extract_wcid_bindings(sql: str) -> dict:
    """
    Pull class_Id → (class_Name, type) from INSERT INTO `weenie` statements.
    Used to thread WCID bindings into subsequent file contexts.
    """
    bindings = {}
    pattern = re.compile(
        r"VALUES\s*\(\s*(\d+)\s*,\s*'([^']+)'\s*,\s*(\d+)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(sql):
        class_id   = int(m.group(1))
        class_name = m.group(2)
        wtype      = int(m.group(3))
        bindings[class_id] = {"class_name": class_name, "type": wtype}
    return bindings


def _is_truncated(sql: str) -> bool:
    stripped = sql.rstrip()
    if not stripped:
        return True
    return not any(stripped.endswith(s) for s in (";", "*/", "---", "```"))


# ── Agent Loop ────────────────────────────────────────────────────────────────

class AgentLoop:
    """
    Manages one full agentic generation session.
    Thread-safe: generation runs on a worker thread; status is queued for JS polling.
    """

    MAX_CONTINUATION_PASSES = 3   # max times we'll auto-continue a truncated file
    MAX_FILE_TOKENS = 16000

    def __init__(
        self,
        api_client,
        skill_loader,
        config,
        chunk_queue,
        process_emote_scripts: Callable[[str], str],
        save_file: Callable[[str, str], dict],
        on_complete: Callable[[], None] = None,
    ):
        self._api         = api_client
        self._skills      = skill_loader
        self._config      = config
        self._queue       = chunk_queue
        self._emotes      = process_emote_scripts
        self._save        = save_file
        self._on_complete = on_complete  # called when worker thread exits

        self._stop_flag  = threading.Event()
        self._generating = False

        # Session state — reset per run
        self._plan: Optional[dict]   = None
        self._orig_prompt: str       = ""
        self._accumulated_sql: str   = ""   # all SQL written so far this session
        self._wcid_bindings: dict    = {}   # class_id → {class_name, type}
        self._editing_sql: str       = ""

    # ── Public ────────────────────────────────────────────────────────────────

    def stop(self):
        self._stop_flag.set()

    def is_generating(self) -> bool:
        return self._generating

    def run_file(
        self,
        plan: dict,
        file_index: int,
        original_prompt: str,
        editing_sql: str = "",
    ):
        """Start generating one file from the plan on a worker thread."""
        if self._generating:
            return False
        self._plan         = plan
        self._orig_prompt  = original_prompt
        self._editing_sql  = editing_sql
        self._stop_flag.clear()
        self._generating   = True
        threading.Thread(
            target=self._run_file_worker,
            args=(file_index,),
            daemon=True,
        ).start()
        return True

    # ── Worker ────────────────────────────────────────────────────────────────

    def _run_file_worker(self, file_index: int):
        plan       = self._plan
        files      = plan.get("files", [])
        total      = len(files)
        file_entry = files[file_index]

        fname = file_entry.get("name", f"file_{file_index}.sql")
        ftype = file_entry.get("type", "creature")
        wcid  = file_entry.get("wcid", 800000)
        fdesc = file_entry.get("description", "")

        # Import converter here to avoid circular import at module level
        try:
            from aceforge.json_to_sql import extract_and_convert as _j2s
        except ImportError:
            try:
                from json_to_sql import extract_and_convert as _j2s
            except ImportError:
                _j2s = None

        try:
            raw = self._generate_with_continuation(file_index, file_entry, total)
            if _j2s:
                sql = _j2s(raw, fname)
                if not sql.strip():
                    sql = raw  # fallback to raw if no JSON found
            else:
                sql = raw
        except Exception as e:
            self._generating = False
            self._queue.put({
                "type": "error",
                "message": f"File {file_index + 1}/{total} ({fname}): {e}",
            })
            if self._on_complete:
                try: self._on_complete()
                except Exception: pass
            return

        if self._stop_flag.is_set():
            self._generating = False
            self._queue.put({"type": "stopped"})
            if self._on_complete:
                try: self._on_complete()
                except Exception: pass
            return

        # ── Self-review ───────────────────────────────────────────────────────
        issues = _review_sql(sql, ftype)
        if issues:
            # Queue a warning but don't block saving — let user decide
            self._queue.put({
                "type": "review_warning",
                "file_index": file_index,
                "file_name": fname,
                "issues": issues,
            })

        # ── Extract WCID bindings for future files ────────────────────────────
        new_bindings = _extract_wcid_bindings(sql)
        self._wcid_bindings.update(new_bindings)

        # ── Accumulate context ────────────────────────────────────────────────
        self._accumulated_sql += f"\n\n-- ===== {fname} =====\n{sql}"

        # ── Save ──────────────────────────────────────────────────────────────
        try:
            sql = self._emotes(sql)
            save_result = self._save(sql, fname)
        except Exception as e:
            save_result = {"success": False, "error": str(e)}

        self._generating = False
        self._queue.put({
            "type": "file_done",
            "file_index": file_index,
            "file_name": fname,
            "save": save_result,
            "total": total,
            "review_issues": issues,
        })
        # Notify app_api that this file's generation is complete
        if self._on_complete:
            try: self._on_complete()
            except Exception: pass

    def _generate_with_continuation(
        self, file_index: int, file_entry: dict, total: int
    ) -> str:
        """Generate SQL for one file, auto-continuing if truncated."""
        fname = file_entry.get("name", "output.sql")
        ftype = file_entry.get("type", "creature")
        wcid  = file_entry.get("wcid", 800000)
        fdesc = file_entry.get("description", "")

        system_prompt = self._build_system_prompt(file_index, file_entry, total)
        user_prompt   = self._build_user_prompt(file_index, file_entry)

        sql = self._stream_blocking(system_prompt, user_prompt)

        # Auto-continue if truncated
        for pass_num in range(1, self.MAX_CONTINUATION_PASSES + 1):
            if self._stop_flag.is_set():
                break
            if not _is_truncated(sql):
                break
            self._queue.put({
                "type": "continuation",
                "file_index": file_index,
                "pass": pass_num,
                "message": f"Output truncated — auto-continuing (pass {pass_num})…",
            })
            tail = sql[-800:]
            cont_system = (
                "You are continuing an ACEmulator SQL generation. "
                "Output only raw SQL continuation. No markdown fences, no explanations. "
                "Do NOT restate anything already written."
            )
            cont_prompt = (
                f"Continue EXACTLY where you left off after this last line:\n\n...{tail}\n\n"
                "Pick up immediately from there. No preamble."
            )
            continuation = self._stream_blocking(cont_system, cont_prompt)
            sql = sql + "\n" + continuation

        return sql

    def _build_system_prompt(
        self, file_index: int, file_entry: dict, total: int
    ) -> str:
        plan  = self._plan
        files = plan.get("files", [])
        fname = file_entry.get("name", "output.sql")
        ftype = file_entry.get("type", "creature")
        wcid  = file_entry.get("wcid", 800000)
        fdesc = file_entry.get("description", "")
        server_name = self._config.server_name or "Shattered Dawn"

        # Load JSON schema prompt
        try:
            _base = (_Path(_sys._MEIPASS) if hasattr(_sys, '_MEIPASS')
                     else _Path(__file__).parent.parent)
            _json_schema = (_base / 'references' / 'ai_json_schema.md').read_text(encoding='utf-8')
            _emote_fmt   = (_base / 'references' / 'emote_format.md').read_text(encoding='utf-8')
        except Exception:
            _json_schema = 'Output a JSON object describing the ACE content.'
            _emote_fmt   = ''

        # Base skill system prompt — now JSON-based
        try:
            weenie_ctx = self._build_weenie_context(self._orig_prompt, ftype)
            _is_local = (self._config.get('provider','anthropic') == 'ollama'
                         or bool(self._config.get('ollama_mode', False)))
            skill_sys  = self._skills.build_system_prompt(
                content_type=ftype,
                server_name=server_name,
                wcid_ranges=self._config.get_wcid_ranges(),
                author=self._config.get("author", ""),
                weenie_context=weenie_ctx,
                is_local=_is_local,
            )
        except Exception:
            pass

        # Build JSON-based system prompt
        skill_sys = (
            f'You are an ACEmulator content generator for the server "{server_name}".\n'
            f'You output ONLY a JSON object. Never write SQL.\n\n'
            + _json_schema
            + ('\n\n' + _emote_fmt if _emote_fmt else '')
        )

        # Other files in the plan (cross-reference context)
        other_files_ctx = "\n".join(
            f"  - File {i+1}: WCID {f['wcid']} | {f['name']} | {f['description']}"
            for i, f in enumerate(files) if i != file_index
        ) or "  (none)"

        # WCID bindings confirmed from already-generated files
        binding_lines = "\n".join(
            f"  - WCID {cid}: class_name='{b['class_name']}' type={b['type']}"
            for cid, b in self._wcid_bindings.items()
        ) or "  (none yet — this is the first file)"

        # Accumulated SQL context (trimmed to avoid token bloat)
        # Include up to ~4000 chars of recent context so the model sees real WCIDs
        acc = self._accumulated_sql
        if len(acc) > 4000:
            acc = "... [earlier files omitted] ...\n" + acc[-4000:]
        acc_section = (
            f"\n\n## SQL Already Generated This Session\n"
            f"Reference these WCIDs when cross-referencing:\n```sql\n{acc}\n```"
            if acc.strip() else ""
        )

        return f"""{skill_sys}

## Agentic Generation Context
You are generating FILE {file_index + 1} of {total} in a multi-file sequence.
Generate ONLY this one file — do NOT generate other files in this response.

### This File
Name: {fname}
WCID: {wcid}
Type: {ftype}
Description: {fdesc}

### All Files in Sequence
{other_files_ctx}

### Confirmed WCID Bindings (from files already generated)
Use these exact class_name values when referencing these WCIDs in emotes, create_list, or generators:
{binding_lines}
{acc_section}

## Output Rules
- Start output with: /* ===== FILE: {fname} ===== */
- Output raw SQL only — no markdown fences, no explanations
- Use the exact WCID {wcid} for this weenie's class_Id
- If this is a generator, use the creature WCID from the bindings above
- INVALID emote triggers (never use): ReceiveGive, ReceiveItem, OnKill, OnDeath, OnGive, QuestComplete, PlayerNear
- VALID give trigger: Give: (not ReceiveGive)
"""

    def _build_user_prompt(self, file_index: int, file_entry: dict) -> str:
        fname = file_entry.get("name", "output.sql")
        wcid  = file_entry.get("wcid", 800000)
        fdesc = file_entry.get("description", "")

        edit_ctx = (
            f"EXISTING WEENIE SQL TO MODIFY:\n```sql\n{self._editing_sql[:6000]}\n```\n\n"
            if self._editing_sql else ""
        )
        return (
            f"{edit_ctx}"
            f"Generate a JSON object for: {fdesc}\n"
            f"Original request: {self._orig_prompt}\n"
            f"File: {fname} | WCID: {wcid}\n"
            f"Output ONLY the JSON object. No SQL. No explanations."
        )

    def _stream_blocking(self, system: str, user: str) -> str:
        """Run stream_generate synchronously on the current thread, return full text."""
        result   = []
        done_evt = threading.Event()
        error    = [None]

        def on_chunk(text: str):
            result.append(text)
            # Forward chunks to the JS poll queue as usual
            self._queue.put({"type": "chunk", "text": text})

        def on_done(full: str):
            done_evt.set()

        def on_error(msg: str):
            error[0] = msg
            done_evt.set()

        self._api.stream_generate(system, user, on_chunk, on_done, on_error, 0.2)  # 0.2 for SQL precision
        done_evt.wait(timeout=300)   # 5-minute per-file timeout

        if error[0]:
            raise RuntimeError(error[0])

        return "".join(result)

    def _build_weenie_context(self, prompt: str, content_type: str) -> str:
        """Delegate to the app_api weenie context builder if available."""
        try:
            results = self._skills.search_weenies(prompt, max_results=2)
            parts   = []
            for entry in results:
                sql = self._skills.get_weenie_sql(entry)
                if sql:
                    parts.append(f"/* WCID {entry.get('w', '?')} — {entry.get('n', '')} */\n{sql}")
            return "\n\n".join(parts)
        except Exception:
            return ""
