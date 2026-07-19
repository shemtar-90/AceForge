"""
world_api.py — backend for the World Placement editor.

Joins the two halves of the feature: :mod:`aceforge.landblock_dat` reads the
terrain canvas out of cell.dat, :mod:`aceforge.landblock` writes placements into
the server's per-landblock SQL files. Everything the web view calls lands here
so ``app_api`` only carries thin delegating methods.

Nothing in here mutates a server file except :func:`place_weenie` and
:func:`remove_instance`, both of which go through ``LandblockFile`` and so
preserve every byte they didn't author.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Dict, List, Optional

from .dat_loader import DatDatabase
from .landblock import (
    LandblockFile, LandblockError, make_obj_cell_id, quaternion_to_heading,
)
from .landblock_dat import (
    LandblockDatError, Landblock, build_dungeon_mesh, build_room_mesh,
    build_terrain_mesh, group_cells_by_frame, landblock_exists,
    parse_environment, read_envcells, read_landblock, resolve_cell_candidates,
    ENVCELL_HEIGHT, LANDBLOCK_SIZE,
)

#: Config key holding the server's landblock SQL folder
#: (…/3-Core/6 LandBlockExtendedData/SQL).
SQL_DIR_KEY = "landblock_sql_dir"

#: Conventional tail of the landblock folder inside an ACE-World checkout.
_CONVENTIONAL_TAIL = Path("3-Core") / "6 LandBlockExtendedData" / "SQL"


# ── DAT handle cache ─────────────────────────────────────────────────────────
#
# Opening a DAT re-reads its directory tree; the world view asks for a new
# landblock on every navigation, so handles are kept open and reused. Guarded
# because pywebview dispatches js_api calls on a worker thread.

_dat_lock = threading.Lock()
_dat_cache: Dict[str, DatDatabase] = {}


def _dat(path: str) -> DatDatabase:
    with _dat_lock:
        db = _dat_cache.get(path)
        if db is None:
            db = DatDatabase(path)
            _dat_cache[path] = db
        return db


def close_dats() -> None:
    """Release cached DAT handles (called on shutdown / DAT path change)."""
    with _dat_lock:
        for db in _dat_cache.values():
            try:
                db.close()
            except Exception:
                pass
        _dat_cache.clear()


# ── landblock ids ────────────────────────────────────────────────────────────

def parse_landblock_id(text: str) -> Optional[int]:
    """
    Accept the many ways a user might name a landblock.

    ``C6A9``, ``0xC6A9``, ``0xC6A90000`` (a full obj_cell_id or @teleloc), or a
    plain decimal. Returns None if it isn't one.
    """
    if text is None:
        return None
    s = str(text).strip().lower().replace("_", "")
    m = re.search(r"0x([0-9a-f]{1,8})", s)
    if m:
        v = int(m.group(1), 16)
        return (v >> 16) & 0xFFFF if v > 0xFFFF else v & 0xFFFF
    if re.fullmatch(r"[0-9a-f]{1,8}", s) and re.search(r"[a-f]", s):
        v = int(s, 16)
        return (v >> 16) & 0xFFFF if v > 0xFFFF else v & 0xFFFF
    if s.isdigit():
        v = int(s)
        return (v >> 16) & 0xFFFF if v > 0xFFFF else v & 0xFFFF
    if re.fullmatch(r"[0-9a-f]{1,8}", s):
        v = int(s, 16)
        return (v >> 16) & 0xFFFF if v > 0xFFFF else v & 0xFFFF
    return None


# ── weenie discovery ─────────────────────────────────────────────────────────

_WEENIE_RE = re.compile(
    r"INSERT\s+INTO\s+`weenie`\s*\([^)]*\)\s*\n\s*VALUES\s*\(\s*(\d+)\s*,\s*"
    r"'([^']*)'\s*,\s*(\d+)",
    re.I,
)


#: Ceiling on files opened by one scan. A user's own output folder holds tens to
#: hundreds of weenies, but pointing the setting at something like a full
#: WeenieDefaults tree (29,585 files locally) would otherwise stall the picker
#: for minutes with the UI thread waiting on it.
MAX_SCAN_FILES = 4000

#: Only the first chunk of a file is read — the `weenie` header row is always at
#: the top, while a big weenie's property blocks can run to hundreds of KB.
_HEADER_BYTES = 4096


def scan_weenies(folders: List[str],
                 max_files: int = MAX_SCAN_FILES) -> List[dict]:
    """
    Every weenie the user has authored, read from their output folders.

    Parses only the ``weenie`` header row of each .sql — enough for a picker
    (wcid, class name, type) without loading whole property blocks. Returns at
    most ``max_files`` worth; ``scan_weenies_truncated`` reports whether the cap
    was hit so the caller can say so.
    """
    seen: Dict[int, dict] = {}
    scanned = 0
    for folder in folders:
        if not folder or scanned >= max_files:
            continue
        base = Path(folder)
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.sql")):
            if scanned >= max_files:
                break
            scanned += 1
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read(_HEADER_BYTES)
            except Exception:
                continue
            m = _WEENIE_RE.search(text)
            if not m:
                continue
            wcid = int(m.group(1))
            if wcid in seen:
                continue
            seen[wcid] = {
                "wcid": wcid,
                "name": m.group(2),
                "type": int(m.group(3)),
                "file": path.name,
                "path": str(path),
            }
    return sorted(seen.values(), key=lambda w: w["wcid"])


# ── sql folder ───────────────────────────────────────────────────────────────

_LANDBLOCK_NAME_RE = re.compile(r"^[0-9A-Fa-f]{4}\.sql$")

#: Folder layouts seen in the wild, relative to a server-content checkout.
#: ACE-World uses the 3-Core tail; community repos commonly use sql/landblocks.
_KNOWN_TAILS = (
    _CONVENTIONAL_TAIL,
    Path("sql") / "landblocks",
    Path("landblocks"),
    Path("Database") / "3-Core" / "6 LandBlockExtendedData" / "SQL",
)

#: Directory names never worth descending into during discovery.
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".vs", "bin", "obj", "venv"}


def count_landblock_files(folder: str | Path) -> int:
    """How many ``%04X.sql`` files a folder holds — 0 means it isn't one."""
    base = Path(folder)
    if not base.is_dir():
        return 0
    try:
        return sum(1 for p in base.iterdir()
                   if p.is_file() and _LANDBLOCK_NAME_RE.match(p.name))
    except OSError:
        return 0


def describe_sql_dir(folder: str | Path) -> dict:
    """
    Explain what a candidate folder actually is, so the UI can say why a pick
    didn't work instead of silently showing an empty landblock.
    """
    base = Path(folder or "")
    if not folder:
        return {"ok": False, "reason": "No folder selected", "count": 0}
    if not base.is_dir():
        return {"ok": False, "reason": "Folder does not exist", "count": 0}
    count = count_landblock_files(base)
    if count:
        return {"ok": True, "reason": f"{count} landblock files", "count": count}
    total_sql = sum(1 for _ in base.glob("*.sql"))
    nested = find_landblock_dirs(base, limit=3)
    if nested:
        return {"ok": False, "count": 0, "suggestions": nested,
                "reason": ("No landblock files here, but found "
                           f"{len(nested)} candidate folder(s) below it")}
    if total_sql:
        return {"ok": False, "count": 0,
                "reason": (f"{total_sql} .sql files here, but none are named "
                           "like a landblock (e.g. C6A9.sql) — this looks like "
                           "a weenie or quest folder")}
    return {"ok": False, "count": 0, "reason": "No .sql files in this folder"}


def find_landblock_dirs(root: str | Path, limit: int = 8,
                        max_depth: int = 6) -> List[str]:
    """
    Walk below ``root`` for folders holding ``%04X.sql`` files.

    Bounded in both depth and result count, and skips VCS/build folders — a
    content repo can hold tens of thousands of files and this runs on the UI
    thread.
    """
    root = Path(root)
    if not root.is_dir():
        return []
    found: List[str] = []
    stack = [(root, 0)]
    while stack and len(found) < limit:
        base, depth = stack.pop()
        try:
            entries = list(base.iterdir())
        except OSError:
            continue
        if any(p.is_file() and _LANDBLOCK_NAME_RE.match(p.name) for p in entries):
            found.append(str(base))
            continue                      # don't descend into a hit
        if depth < max_depth:
            for p in entries:
                if p.is_dir() and p.name not in _SKIP_DIRS and not p.name.startswith("."):
                    stack.append((p, depth + 1))
    return found


def guess_sql_dir(hints: List[str]) -> str:
    """
    Best-effort discovery of the landblock SQL folder.

    Tries, in order: the hint itself, each known layout tail beneath it, then a
    bounded walk. Handles both ACE-World's ``3-Core/6 LandBlockExtendedData/SQL``
    and the ``sql/landblocks`` layout community content repos use.
    """
    for hint in hints:
        if not hint:
            continue
        base = Path(hint)
        if not base.is_dir():
            continue
        if count_landblock_files(base):
            return str(base)
        for tail in _KNOWN_TAILS:
            candidate = base / tail
            if count_landblock_files(candidate):
                return str(candidate)
    # Nothing obvious — walk the hints, most-specific first.
    for hint in hints:
        if not hint:
            continue
        hits = find_landblock_dirs(hint, limit=1)
        if hits:
            return hits[0]
    return ""


# ── landblock loading ────────────────────────────────────────────────────────

def _environment_geometry(portal_db, envcells) -> Dict[int, object]:
    """{environment_id: CellGeometry} for every environment a landblock uses."""
    geoms: Dict[int, object] = {}
    for c in envcells:
        if c.environment_id in geoms:
            continue
        parsed = parse_environment(portal_db, c.environment_id)
        if parsed:
            geoms[c.environment_id] = next(iter(parsed.values()))
    return geoms


def resolve_cell(cell_dat: str, portal_dat: str, landblock: int,
                 x: float, y: float, z: float) -> dict:
    """
    Shortlist the interior cells that could contain a point.

    Deliberately returns candidates rather than an answer — see
    :func:`landblock_dat.resolve_cell_candidates` for why position alone can't
    determine cell membership. The UI presents these for confirmation.
    """
    cells = read_envcells(_dat(cell_dat), landblock)
    geoms = _environment_geometry(_dat(portal_dat), cells)
    ranked = resolve_cell_candidates(cells, geoms, (x, y, z))
    by_id = {c.cell: c for c in cells}
    return {
        "candidates": [
            {"cell": cid, "cellHex": f"0x{cid:04X}",
             "objCellId": f"0x{make_obj_cell_id(landblock, cid):08X}",
             "depth": round(depth, 3),
             "envId": f"0x{by_id[cid].environment_id:04X}"}
            for cid, depth in ranked[:8]
        ],
        "count": len(ranked),
        "unambiguous": len(ranked) == 1,
    }


def load_landblock(cell_dat: str, portal_dat: str, sql_dir: str,
                   landblock: int, with_objects: bool = True) -> dict:
    """
    Everything the web view needs to draw and edit one landblock.

    Returns the terrain mesh as base64 typed arrays plus the placements already
    present in the landblock's SQL file (empty list if the file doesn't exist —
    that's the create-on-first-place case, not an error).
    """
    cell = _dat(cell_dat)
    if not landblock_exists(cell, landblock):
        raise LandblockDatError(
            f"landblock 0x{landblock:04X} has no terrain in cell.dat"
        )
    lb = read_landblock(cell, _dat(portal_dat), landblock,
                        with_objects=with_objects)
    mesh = build_terrain_mesh(lb)

    # Interior cells. Indoor instances are positioned in this same frame space
    # (verified: median offset 0.000 from the owning cell's frame), so they can
    # be drawn directly with no per-cell transform.
    envcells = read_envcells(cell, landblock)
    geoms = _environment_geometry(_dat(portal_dat), envcells)
    # Real room surfaces when the Environments parse; box placeholders if not.
    dungeon = build_room_mesh(envcells, geoms)
    if not dungeon.triangle_count:
        dungeon = build_dungeon_mesh(envcells)
    cell_by_id = {c.cell: c for c in envcells}

    instances: List[dict] = []
    file_exists = False
    if sql_dir:
        lbf = LandblockFile.load(sql_dir, landblock)
        file_exists = lbf.existed
        child_guids = {l.child_guid for l in lbf.links}
        for inst in lbf.instances:
            outdoor = inst.cell == 0
            instances.append({
                "guid": inst.guid,
                "guidHex": f"0x{inst.guid:08X}",
                "wcid": inst.wcid,
                "name": inst.name,
                "cell": inst.cell,
                "objCellId": f"0x{inst.obj_cell_id:08X}",
                "x": inst.x, "y": inst.y, "z": inst.z,
                "heading": round(inst.heading, 3),
                "outdoor": outdoor,
                "isLinkChild": inst.is_link_child,
                "hasParent": inst.guid in child_guids,
                # Terrain view only shows outdoor rows; indoor rows live in the
                # dungeon view, which uses the same coordinates they're stored in.
                "placeable": outdoor and 0 <= inst.x <= LANDBLOCK_SIZE
                             and 0 <= inst.y <= LANDBLOCK_SIZE,
                "inDungeon": (not outdoor) and inst.cell in cell_by_id,
            })

    return {
        "landblock": landblock,
        "landblockHex": f"{landblock:04X}",
        "mesh": mesh.to_base64(),
        "staticObjects": [
            {"setupId": f"0x{o.setup_id:08X}", "x": o.x, "y": o.y, "z": o.z,
             "w": o.angles_w, "qx": o.angles_x, "qy": o.angles_y, "qz": o.angles_z}
            for o in lb.static_objects
        ],
        "numCells": lb.num_cells,
        "hasObjects": lb.has_objects,
        "instances": instances,
        # Frames, not cells. A frame is a location shared by 1..28 cells, so it
        # identifies *where* something is but not *which cell* it belongs to —
        # that needs the Environment geometry. New indoor placements are
        # therefore not offered from a click; see place_weenie.
        "dungeon": dict(dungeon.to_base64(), frames=[
            {"x": round(x, 4), "y": round(y, 4), "z": round(z, 4),
             "cells": [f"0x{c.cell:04X}" for c in members[:12]],
             "cellCount": len(members)}
            for (x, y, z), members in group_cells_by_frame(envcells)
        ]),
        "envCellCount": len(envcells),
        "hasDungeon": bool(envcells),
        "sqlFile": str(LandblockFile.path_for(sql_dir, landblock)) if sql_dir else "",
        "sqlFileExists": file_exists,
        "outdoorCount": sum(1 for i in instances if i["placeable"]),
        "indoorCount": sum(1 for i in instances if not i["outdoor"]),
        "dungeonCount": sum(1 for i in instances if i.get("inDungeon")),
    }


def terrain_height(cell_dat: str, portal_dat: str,
                   landblock: int, x: float, y: float) -> float:
    """Exact terrain Z at a landblock-local point — used to snap placements."""
    lb = read_landblock(_dat(cell_dat), _dat(portal_dat), landblock,
                        with_objects=False)
    return lb.height_at(x, y)


# ── mutation ─────────────────────────────────────────────────────────────────

def place_weenie(sql_dir: str, landblock: int, wcid: int,
                 x: float, y: float, z: Optional[float] = None,
                 heading: float = 0.0, name: str = "",
                 cell: int = 0x0000,
                 cell_dat: str = "", portal_dat: str = "") -> dict:
    """
    Write one placement into the landblock's SQL file, creating it if absent.

    ``z=None`` snaps to terrain, which is what a click on the surface wants.
    """
    if not sql_dir:
        raise LandblockError("No landblock SQL folder configured")
    # The 0-192 m bound is a *terrain* constraint. Interior cells are positioned
    # in their own frame space, where x legitimately runs past 192 and y is
    # often negative, so only outdoor placements get range-checked.
    if cell == 0 and (not 0 <= x <= LANDBLOCK_SIZE or not 0 <= y <= LANDBLOCK_SIZE):
        raise LandblockError(
            f"({x:.2f}, {y:.2f}) is outside the landblock's 0-{LANDBLOCK_SIZE:g} m range"
        )
    if z is None:
        if cell != 0:
            raise LandblockError(
                "Indoor placements need an explicit Z — there is no terrain to snap to"
            )
        if not (cell_dat and portal_dat):
            raise LandblockError("Cannot snap to terrain without the DAT files")
        z = terrain_height(cell_dat, portal_dat, landblock, x, y)

    lbf = LandblockFile.load(sql_dir, landblock)
    created = not lbf.existed
    guid = lbf.add_instance(wcid=wcid, cell=cell, x=x, y=y, z=z,
                            heading_deg=heading, name=name)
    path = lbf.save()
    return {
        "guid": guid,
        "guidHex": f"0x{guid:08X}",
        "objCellId": f"0x{make_obj_cell_id(landblock, cell):08X}",
        "x": x, "y": y, "z": z, "heading": heading,
        "file": str(path),
        "created": created,
        "instanceCount": len(lbf.instances),
        "reloadCommand": f"/reload-landblock 0x{landblock:04X}",
    }


def remove_instance(sql_dir: str, landblock: int, guid: int) -> dict:
    """Delete a placement (and any links touching it) from the SQL file."""
    if not sql_dir:
        raise LandblockError("No landblock SQL folder configured")
    lbf = LandblockFile.load(sql_dir, landblock)
    if not lbf.existed:
        raise LandblockError(f"{LandblockFile.file_name(landblock)} does not exist")
    if not lbf.remove_instance(guid):
        raise LandblockError(f"0x{guid:08X} is not in this landblock")
    path = lbf.save()
    return {"removed": f"0x{guid:08X}", "file": str(path),
            "instanceCount": len(lbf.instances),
            "reloadCommand": f"/reload-landblock 0x{landblock:04X}"}


def move_instance(sql_dir: str, landblock: int, guid: int,
                  x: float, y: float, z: Optional[float] = None,
                  heading: Optional[float] = None,
                  cell_dat: str = "", portal_dat: str = "") -> dict:
    """Reposition an existing placement, re-snapping to terrain when z is None."""
    if not sql_dir:
        raise LandblockError("No landblock SQL folder configured")
    lbf = LandblockFile.load(sql_dir, landblock)
    inst = lbf.by_guid(guid)
    if inst is None:
        raise LandblockError(f"0x{guid:08X} is not in this landblock")
    if z is None:
        if not (cell_dat and portal_dat):
            raise LandblockError("Cannot snap to terrain without the DAT files")
        z = terrain_height(cell_dat, portal_dat, landblock, x, y)

    from .landblock import heading_to_quaternion
    inst.x, inst.y, inst.z = x, y, z
    if heading is not None:
        inst.angles_w, inst.angles_x, inst.angles_y, inst.angles_z = \
            heading_to_quaternion(heading)
    inst.raw = None                     # force re-render with the new values
    path = lbf.save()
    return {"guid": f"0x{guid:08X}", "x": x, "y": y, "z": z,
            "heading": heading if heading is not None else inst.heading,
            "file": str(path),
            "reloadCommand": f"/reload-landblock 0x{landblock:04X}"}
