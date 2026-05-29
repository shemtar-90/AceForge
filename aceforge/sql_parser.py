"""
ACEForge SQL Parser
Parses the streamed Claude response to extract individual SQL file segments.
Each segment is demarcated by /* ===== FILE: name.sql ===== */ headers.
Writes each file to the configured output directory.
"""

import re
import os
from pathlib import Path


# Matches: /* ===== FILE: 850009 Valdris Ashenmoor.sql ===== */
FILE_HEADER_RE = re.compile(
    r"/\*\s*=+\s*FILE:\s*(.+?\.sql)\s*=+\s*\*/",
    re.IGNORECASE
)

FILE_HEADER_LOOSE_RE = re.compile(
    r"/\*\s*=+\s*FILE:\s*(.+?)\s*=+\s*\*/",
    re.IGNORECASE
)


def sanitize_filename(name: str) -> str:
    """
    Clean a filename for Windows:
    - Remove illegal characters
    - Replace underscores with spaces
    - Ensure .sql extension
    """
    name = name.strip()
    # Replace underscores with spaces before anything else
    name = name.replace("_", " ")
    # Collapse multiple spaces
    name = re.sub(r" {2,}", " ", name).strip()
    # Remove characters illegal in Windows filenames
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "")
    if not name.lower().endswith(".sql"):
        name += ".sql"
    return name


def strip_sql_comments(sql: str) -> str:
    """
    Remove ALL -- line comments from SQL output.
    ACE's importer does not handle them. /* block comments */ are preserved.
    Handles -- inside string literals correctly (does not strip them).
    """
    lines = sql.split("\n")
    cleaned = []
    for line in lines:
        in_single = False
        result = []
        i = 0
        while i < len(line):
            c = line[i]
            if c == "'" and not in_single:
                in_single = True
                result.append(c)
            elif c == "'" and in_single:
                result.append(c)
                # Peek: escaped quote ''
                if i + 1 < len(line) and line[i + 1] == "'":
                    result.append("'")
                    i += 2
                    continue
                in_single = False
            elif c == "-" and not in_single and i + 1 < len(line) and line[i + 1] == "-":
                break  # Strip from here to end of line
            else:
                result.append(c)
            i += 1
        stripped = "".join(result).rstrip()
        if stripped:
            cleaned.append(stripped)
    return "\n".join(cleaned)


def format_sql(sql: str) -> str:
    """
    Post-process AI-generated SQL to enforce correct formatting:

    1. Blank line between every statement (after each closing ;)
    2. weenie_properties_body_part column list on a single line (no wrapping)
    3. weenie_properties_emote_action column list on a single line (no wrapping)
    4. Normalize CRLF to LF
    """
    # Normalize line endings
    sql = sql.replace("\r\n", "\n").replace("\r", "\n")

    # ── Fix 1: Un-wrap INSERT INTO column lists that span multiple lines ──────
    # Targets weenie_properties_body_part and weenie_properties_emote_action
    # which must have all columns on ONE line per the ACE schema spec.
    def collapse_column_list(m):
        table   = m.group(1)
        columns = re.sub(r"\s+", " ", m.group(2)).strip()
        return f"INSERT INTO `{table}` ({columns})"

    sql = re.sub(
        r"INSERT INTO `(weenie_properties_body_part|weenie_properties_emote_action)`\s*\(([^)]+)\)",
        collapse_column_list,
        sql,
        flags=re.DOTALL,
    )

    # ── Fix 2: Ensure blank line between SQL statements ───────────────────────
    # Add a blank line after every ; that is followed by another statement.
    # Strategy: split on lines, detect statement boundaries, re-join with spacing.
    lines = sql.split("\n")
    output = []
    for idx, line in enumerate(lines):
        output.append(line)
        stripped = line.rstrip()
        # A line that ends a statement: ends with ; or ); or );  /* comment */
        # and the next non-empty line starts a new statement keyword
        if re.search(r";\s*(?:/\*[^*]*\*/\s*)?$", stripped):
            # Peek forward to next non-blank line
            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j].strip()
                # If next statement is DELETE/INSERT/SET/CREATE/DROP/UPDATE
                if re.match(r"^(DELETE|INSERT|SET|CREATE|DROP|UPDATE|ALTER)\b", next_line, re.IGNORECASE):
                    # Only add blank if there isn't one already
                    if idx + 1 < len(lines) and lines[idx + 1].strip():
                        output.append("")

    return "\n".join(output)


def clean_sql(sql: str) -> str:
    """Full pipeline: strip -- comments, then format."""
    sql = strip_sql_comments(sql)
    sql = format_sql(sql)
    return sql.strip()


def parse_and_save_files(
    full_response: str,
    output_dir: str,
    subfolder: str = "",
) -> list[str]:
    """
    Parse a complete Claude response into individual SQL files.
    Returns list of file paths that were written.
    If no FILE: markers are found, saves the entire response as a single file.
    """
    output_path = Path(output_dir)
    if subfolder:
        output_path = output_path / subfolder
    output_path.mkdir(parents=True, exist_ok=True)

    written = []
    segments = FILE_HEADER_LOOSE_RE.split(full_response)

    if len(segments) <= 1:
        # No FILE: markers — derive filename from SQL content
        wcid_match  = re.search(r"VALUES\s*\((\d+)\s*,\s*'([^']+)'", full_response)
        quest_match = re.search(
            r"INSERT INTO\s*`quest`[^;]+VALUES\s*\('([^']+)'",
            full_response, re.IGNORECASE
        )
        if wcid_match:
            wcid    = wcid_match.group(1)
            cname   = wcid_match.group(2).strip()
            display = cname.replace("_", " ").title()
            fname   = sanitize_filename(f"{wcid} {display}.sql")
        elif quest_match:
            fname = sanitize_filename(quest_match.group(1).strip() + ".sql")
        else:
            fname = "output.sql"

        fpath = output_path / fname
        fpath.write_text(clean_sql(full_response), encoding="utf-8")
        written.append(str(fpath))
        return written

    # segments: [preamble, filename, content, filename, content, ...]
    i = 1
    while i < len(segments):
        raw_name = segments[i].strip()
        content  = segments[i + 1].strip() if (i + 1) < len(segments) else ""
        i += 2

        if not content:
            continue

        fname = sanitize_filename(raw_name)
        fpath = output_path / fname
        fpath.write_text(clean_sql(content), encoding="utf-8")
        written.append(str(fpath))

    return written


def estimate_file_count(prompt_response: str) -> int:
    return len(FILE_HEADER_LOOSE_RE.findall(prompt_response))


def extract_summary(full_response: str) -> str:
    match = re.search(r"(?:^|\n)(#+\s*Summary.*?)$", full_response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"\*\*Summary[:\*]+\**(.*?)$", full_response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""
