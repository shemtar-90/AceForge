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
        # No markers found — save as single file
        fname = "output.sql"
        fpath = output_path / fname
        fpath.write_text(full_response.strip(), encoding="utf-8")
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
        fpath.write_text(content, encoding="utf-8")
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
