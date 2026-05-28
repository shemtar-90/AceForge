"""
ACEForge SQL Parser
Parses the streamed Claude response to extract individual SQL file segments.
Each segment is demarcated by /* ===== FILE: name.sql ===== */ headers.
Writes each file to the configured output directory.
"""

import re
import os
from pathlib import Path
from typing import Generator


# Matches: /* ===== FILE: 850009 Valdris Ashenmoor.sql ===== */
FILE_HEADER_RE = re.compile(
    r"/\*\s*=+\s*FILE:\s*(.+?\.sql)\s*=+\s*\*/",
    re.IGNORECASE
)

# Also catch quest flag files and KT files without WCID prefix
FILE_HEADER_LOOSE_RE = re.compile(
    r"/\*\s*=+\s*FILE:\s*(.+?)\s*=+\s*\*/",
    re.IGNORECASE
)


def sanitize_filename(name: str) -> str:
    """Remove characters illegal in Windows filenames."""
    name = name.strip()
    illegal = r'\/:*?"<>|'
    for ch in illegal:
        name = name.replace(ch, "_")
    # Ensure .sql extension
    if not name.lower().endswith(".sql"):
        name += ".sql"
    return name


def strip_sql_comments(sql: str) -> str:
    """
    Remove -- line comments from SQL that break ACE's importer.
    Preserves /* block comments */ which ACE handles fine.
    Only removes -- comments that appear at the start of a line or
    after a semicolon (i.e. not -- inside string literals).
    """
    import re
    lines = sql.split("\n")
    cleaned = []
    for line in lines:
        # Remove -- comments: find -- not inside a string literal
        # Simple approach: strip from first -- that isn't inside quotes
        in_single = False
        result = []
        i = 0
        while i < len(line):
            c = line[i]
            if c == "\'" and not in_single:
                in_single = True
                result.append(c)
            elif c == "\'" and in_single:
                # Check for escaped quote ''
                if i + 1 < len(line) and line[i+1] == "\'":
                    result.append("\'\'"  )
                    i += 2
                    continue
                in_single = False
                result.append(c)
            elif c == "-" and not in_single and i + 1 < len(line) and line[i+1] == "-":
                # Found -- comment outside string - strip rest of line
                break
            else:
                result.append(c)
            i += 1
        stripped = "".join(result).rstrip()
        # Skip lines that are now empty (were pure -- comment lines)
        if stripped:
            cleaned.append(stripped)
    return "\n".join(cleaned)


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

    # Split on FILE: markers
    segments = FILE_HEADER_LOOSE_RE.split(full_response)

    if len(segments) <= 1:
        # No FILE: markers found — try to extract a WCID and name from the SQL
        # Look for: INSERT INTO `weenie` ... VALUES (WCID, 'classname', ...
        import re as _re
        wcid_match = _re.search(r"VALUES\s*\((\d+)\s*,\s*'([^']+)'", full_response)
        # Or quest table: VALUES ('QuestName', ...)
        quest_match = _re.search(r"INSERT INTO\s*`quest`[^;]+VALUES\s*\('([^']+)'", full_response, _re.IGNORECASE)

        if wcid_match:
            wcid = wcid_match.group(1)
            cname = wcid_match.group(2).strip()
            # Capitalize for display
            display = cname.replace("_", " ").title()
            fname = sanitize_filename(f"{wcid} {display}.sql")
        elif quest_match:
            qname = quest_match.group(1).strip()
            fname = sanitize_filename(f"{qname}.sql")
        else:
            fname = "output.sql"

        fpath = output_path / fname
        fpath.write_text(strip_sql_comments(full_response.strip()), encoding="utf-8")
        written.append(str(fpath))
        return written

    # segments alternates: [pre-content, filename, content, filename, content, ...]
    # Index 0 is content before the first marker (usually empty or preamble — skip)
    i = 1
    while i < len(segments):
        raw_name = segments[i].strip()
        content  = segments[i + 1].strip() if (i + 1) < len(segments) else ""
        i += 2

        if not content:
            continue

        fname = sanitize_filename(raw_name)
        fpath = output_path / fname
        fpath.write_text(strip_sql_comments(content), encoding="utf-8")
        written.append(str(fpath))

    return written


def estimate_file_count(prompt_response: str) -> int:
    """Count how many FILE: markers appear in a response."""
    return len(FILE_HEADER_LOOSE_RE.findall(prompt_response))


def extract_summary(full_response: str) -> str:
    """
    Extract the Summary block from the end of a Claude response.
    Returns the summary text, or empty string if not found.
    """
    # Look for Summary: heading near the end
    match = re.search(
        r"(?:^|\n)(#+\s*Summary.*?)$",
        full_response,
        re.IGNORECASE | re.DOTALL
    )
    if match:
        return match.group(1).strip()

    # Fallback: look for a **Summary** marker
    match = re.search(
        r"\*\*Summary[:\*]+\**(.*?)$",
        full_response,
        re.IGNORECASE | re.DOTALL
    )
    if match:
        return match.group(1).strip()

    return ""
