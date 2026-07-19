"""
landblock.py — ACE-World landblock instance file engine.

Reads, merges and writes the per-landblock SQL files that live in a server's
``3-Core/6 LandBlockExtendedData/SQL`` folder (``0007.sql``, ``584A.sql``, …).
Those files are what ``/reload-landblock`` re-reads, so placing a weenie in the
world means adding a ``landblock_instance`` row to the right file.

Conventions here were derived from — and verified against — the 3,692 retail
landblock files (323,134 instances). See ``CONVENTIONS`` below.

Design note: merging **preserves existing text verbatim**. Rows we did not
author are never re-serialized, so a save can't perturb retail float formatting
or comments. Only new rows are rendered by this module. All 3,692 retail files
round-trip byte-identically through :meth:`LandblockFile.parse` →
:meth:`LandblockFile.render`.

Guid reuse caveat: :meth:`LandblockFile.next_sequence` never recycles a
sequence within a session, including after :meth:`LandblockFile.remove_instance`.
Across sessions it can't — once a removed row is saved away, nothing in the file
records that it ever existed (712 retail files have exactly these gaps). If you
remove the highest-numbered instance, save, and later add another, the new row
takes the freed guid. That only matters if something outside this landblock's
file still references the old guid, so prefer removing via this module (which
cleans links) and avoid hand-editing guids elsewhere.

    lb = LandblockFile.load(sql_dir, 0x0007)     # or .create(...) if missing
    guid = lb.add_instance(wcid=800001, cell=0x0111,
                           x=24.75, y=-40.0, z=0.0, heading_deg=90,
                           name="My Custom NPC")
    lb.save()
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# ── Conventions (verified against retail ACE-World data) ─────────────────────
#
# file name      "%04X.sql" upper-case, landblock id high 16 bits   (3692/3692)
# header         DELETE FROM `landblock_instance` WHERE `landblock` = 0x%04X;
# guid           0x70000000 | (landblock << 12) | sequence          (323133/323134)
#                sequence is 12 bits, so 4096 instances per landblock.
#                The single retail outlier (0x75C450BA in 584A.sql) is preserved
#                on read but never produced on write.
# obj_Cell_Id    (landblock << 16) | cell                           (323134/323134)
# columns        one fixed column set, see _INSERT_COLS             (323134/323134)
# link columns   `parent_GUID`, `child_GUID`, `last_Modified`       (12539/12539)
# last_Modified  '2005-02-09 10:00:00' everywhere                   (323134/323134)
# line endings   LF, file ends with exactly one newline
#
GUID_BASE = 0x70000000
GUID_SEQ_BITS = 12
GUID_SEQ_MAX = (1 << GUID_SEQ_BITS) - 1        # 0xFFF — 4096 per landblock

DEFAULT_TIMESTAMP = "2005-02-09 10:00:00"

_INSERT_COLS = (
    "`guid`, `weenie_Class_Id`, `obj_Cell_Id`, `origin_X`, `origin_Y`, "
    "`origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`, "
    "`is_Link_Child`, `last_Modified`"
)
_LINK_COLS = "`parent_GUID`, `child_GUID`, `last_Modified`"


class LandblockError(Exception):
    """Raised when a landblock file is malformed or a placement is invalid."""


# ── numeric formatting ───────────────────────────────────────────────────────

def _f32(value: float) -> float:
    """Round a Python float to the nearest float32, as the DB column stores."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fmt_float(value: float) -> str:
    """
    Six significant digits, never scientific notation — the retail format.

    Verified against every numeric field in the retail corpus: 2,261,709 of
    2,261,938 values are exactly ``%.6g``. The 229 exceptions are all tiny
    magnitudes written in plain decimal (``0.000001``, not ``1e-06``), which
    the fallback below reproduces.
    """
    f = _f32(value)
    if f == int(f) and abs(f) < 1e16:
        return str(int(f))
    s = f"{f:.6g}"
    if "e" in s or "E" in s:
        s = f"{f:.10f}".rstrip("0").rstrip(".")
        return s or "0"
    return s


def heading_to_quaternion(degrees: float) -> Tuple[float, float, float, float]:
    """
    AC heading (degrees, 0 = north, increasing clockwise) → (w, x, y, z).

    Rotation is about Z only, which is why every retail row has
    ``angles_X = angles_Y = 0``.
    """
    half = math.radians(degrees) / 2.0
    # ``+ 0.0`` folds -0.0 to 0.0 so heading 0 renders "0.000000", not
    # "-0.000000", matching every identity rotation in the retail corpus.
    return (math.cos(half) + 0.0, 0.0, 0.0, -math.sin(half) + 0.0)


def quaternion_to_heading(w: float, z: float) -> float:
    """Inverse of :func:`heading_to_quaternion`, normalised to [0, 360)."""
    return math.degrees(2.0 * math.atan2(-z, w)) % 360.0


# ── ids ──────────────────────────────────────────────────────────────────────

def make_guid(landblock: int, sequence: int) -> int:
    """Build a static instance guid. See ``CONVENTIONS``."""
    if not 0 <= landblock <= 0xFFFF:
        raise LandblockError(f"landblock 0x{landblock:X} out of range")
    if not 0 <= sequence <= GUID_SEQ_MAX:
        raise LandblockError(
            f"sequence {sequence} exceeds {GUID_SEQ_MAX} — landblock "
            f"0x{landblock:04X} is full (4096 instances max)"
        )
    return GUID_BASE | (landblock << GUID_SEQ_BITS) | sequence


def guid_landblock(guid: int) -> int:
    return (guid & 0x0FFFF000) >> GUID_SEQ_BITS


def guid_sequence(guid: int) -> int:
    return guid & GUID_SEQ_MAX


def make_obj_cell_id(landblock: int, cell: int) -> int:
    """
    ``(landblock << 16) | cell``.

    Cell is 0x100+ for indoor/dungeon cells; outdoor placements use the
    landblock's own cell range (0x0001-0x003F) — pass the cell you got from
    ``@teleloc`` or from a terrain pick.
    """
    if not 0 <= landblock <= 0xFFFF:
        raise LandblockError(f"landblock 0x{landblock:X} out of range")
    if not 0 <= cell <= 0xFFFF:
        raise LandblockError(f"cell 0x{cell:X} out of range")
    return (landblock << 16) | cell


# ── model ────────────────────────────────────────────────────────────────────

@dataclass
class Instance:
    """One ``landblock_instance`` row."""
    guid: int
    wcid: int
    obj_cell_id: int
    x: float
    y: float
    z: float
    angles_w: float = 1.0
    angles_x: float = 0.0
    angles_y: float = 0.0
    angles_z: float = 0.0
    is_link_child: bool = False
    last_modified: str = DEFAULT_TIMESTAMP
    name: str = ""
    #: Verbatim source text when parsed from an existing file. Rendering
    #: prefers this so untouched rows survive a save byte-for-byte.
    raw: Optional[str] = None

    @property
    def cell(self) -> int:
        return self.obj_cell_id & 0xFFFF

    @property
    def landblock(self) -> int:
        return (self.obj_cell_id >> 16) & 0xFFFF

    @property
    def heading(self) -> float:
        return quaternion_to_heading(self.angles_w, self.angles_z)

    def render(self) -> str:
        """Serialize to the house SQL format (header comment + teleloc)."""
        if self.raw is not None:
            return self.raw
        comment = f" /* {self.name} */" if self.name else ""
        link = " True" if self.is_link_child else "False"
        return (
            f"INSERT INTO `landblock_instance` ({_INSERT_COLS})\n"
            f"VALUES (0x{self.guid:08X}, {self.wcid:5d}, 0x{self.obj_cell_id:08X}, "
            f"{fmt_float(self.x)}, {fmt_float(self.y)}, {fmt_float(self.z)}, "
            f"{fmt_float(self.angles_w)}, {fmt_float(self.angles_x)}, "
            f"{fmt_float(self.angles_y)}, {fmt_float(self.angles_z)}, "
            f"{link}, '{self.last_modified}');{comment}\n"
            f"/* @teleloc 0x{self.obj_cell_id:08X} "
            f"[{self.x:.6f} {self.y:.6f} {self.z:.6f}] "
            f"{self.angles_w:.6f} {self.angles_x:.6f} "
            f"{self.angles_y:.6f} {self.angles_z:.6f} */\n"
        )


@dataclass
class Link:
    """One ``landblock_instance_link`` parent→child edge."""
    parent_guid: int
    child_guid: int
    last_modified: str = DEFAULT_TIMESTAMP
    child_name: str = ""
    child_wcid: Optional[int] = None
    #: Verbatim comment body when parsed. Retail names sometimes carry a
    #: trailing space ("Scribe Muhiza bint Murqidh  (6861)"), so round-tripping
    #: reuses the original text rather than rebuilding it from name + wcid.
    comment_raw: Optional[str] = None

    def render_row(self) -> str:
        if self.comment_raw is not None:
            comment = f" /*{self.comment_raw}*/" if self.comment_raw else ""
        elif self.child_name:
            wcid = f" ({self.child_wcid})" if self.child_wcid is not None else ""
            comment = f" /* {self.child_name}{wcid} */"
        else:
            comment = ""
        return (f"(0x{self.parent_guid:08X}, 0x{self.child_guid:08X}, "
                f"'{self.last_modified}'){comment}")


# ── parsing ──────────────────────────────────────────────────────────────────

_DELETE_RE = re.compile(
    r"DELETE\s+FROM\s+`landblock_instance`\s+WHERE\s+`landblock`\s*=\s*0x([0-9A-Fa-f]+)\s*;",
    re.I,
)

_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+`landblock_instance`\s*\([^)]*\)\s*\n"
    r"VALUES\s*\(\s*0x([0-9A-Fa-f]{1,8})\s*,\s*(\d+)\s*,\s*0x([0-9A-Fa-f]{1,8})\s*,"
    r"\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,"
    r"\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,"
    r"\s*(True|False)\s*,\s*'([^']*)'\s*\)\s*;"
    r"(?:[ \t]*/\*(.*?)\*/)?"
    r"(?:[ \t]*\n[ \t]*/\*[ \t]*@teleloc.*?\*/)?",
    re.I | re.S,
)

_LINK_RE = re.compile(
    r"INSERT\s+INTO\s+`landblock_instance_link`\s*\([^)]*\)\s*\n"
    r"VALUES\s*(.*?);",
    re.I | re.S,
)

_LINK_ROW_RE = re.compile(
    r"\(\s*0x([0-9A-Fa-f]{1,8})\s*,\s*0x([0-9A-Fa-f]{1,8})\s*,\s*'([^']*)'\s*\)"
    r"(?:\s*/\*(.*?)\*/)?",
    re.S,
)


def _parse_instances(text: str) -> List[Instance]:
    out: List[Instance] = []
    for m in _INSERT_RE.finditer(text):
        comment = (m.group(13) or "").strip()
        out.append(Instance(
            guid=int(m.group(1), 16),
            wcid=int(m.group(2)),
            obj_cell_id=int(m.group(3), 16),
            x=float(m.group(4)), y=float(m.group(5)), z=float(m.group(6)),
            angles_w=float(m.group(7)), angles_x=float(m.group(8)),
            angles_y=float(m.group(9)), angles_z=float(m.group(10)),
            is_link_child=m.group(11).lower() == "true",
            last_modified=m.group(12),
            name=comment,
            raw=m.group(0).rstrip() + "\n",
        ))
    return out


def _parse_links(text: str) -> List[Link]:
    out: List[Link] = []
    for m in _LINK_RE.finditer(text):
        for row in _LINK_ROW_RE.finditer(m.group(1)):
            comment = (row.group(4) or "").strip()
            name, wcid = comment, None
            cm = re.match(r"^(.*?)\s*\((\d+)\)$", comment)
            if cm:
                name, wcid = cm.group(1), int(cm.group(2))
            out.append(Link(
                parent_guid=int(row.group(1), 16),
                child_guid=int(row.group(2), 16),
                last_modified=row.group(3),
                child_name=name,
                child_wcid=wcid,
                comment_raw=row.group(4) if row.group(4) is not None else None,
            ))
    return out


# ── the file ─────────────────────────────────────────────────────────────────

@dataclass
class LandblockFile:
    """
    An ACE-World per-landblock instance file.

    Instances keep source order; new ones append. Links are regrouped by parent
    on render, which matches how retail files are laid out.
    """
    landblock: int
    path: Path
    instances: List[Instance] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    existed: bool = False
    #: Highest sequence ever handed out or seen in this file, including ones
    #: since removed. Never decreases, so a remove-then-add within one session
    #: cannot recycle a guid that other SQL may still reference.
    _seq_high_water: int = -1

    # ── construction ────────────────────────────────────────────────────────

    @staticmethod
    def file_name(landblock: int) -> str:
        return f"{landblock:04X}.sql"

    @classmethod
    def path_for(cls, sql_dir: str | Path, landblock: int) -> Path:
        """
        Where this landblock's file lives.

        Prefers an existing file whatever its case — real content repos mix
        ``C6A9.sql`` and ``c6a9.sql`` (8 of 973 in one checked repo), and on a
        case-sensitive filesystem writing the canonical upper-case name would
        create a second file that silently shadows the first. New files always
        get the canonical ``%04X.sql``.
        """
        base = Path(sql_dir)
        canonical = base / cls.file_name(landblock)
        if canonical.exists():
            return canonical
        wanted = canonical.name.lower()
        try:
            for existing in base.iterdir():
                if existing.is_file() and existing.name.lower() == wanted:
                    return existing
        except OSError:
            pass
        return canonical

    @classmethod
    def create(cls, sql_dir: str | Path, landblock: int) -> "LandblockFile":
        """A new, empty landblock file (not yet written to disk)."""
        return cls(landblock=landblock,
                   path=cls.path_for(sql_dir, landblock),
                   existed=False)

    @classmethod
    def parse(cls, text: str, landblock: int, path: Path) -> "LandblockFile":
        m = _DELETE_RE.search(text)
        if m:
            found = int(m.group(1), 16)
            if found != landblock:
                raise LandblockError(
                    f"{path.name}: DELETE header is for landblock 0x{found:04X}, "
                    f"expected 0x{landblock:04X}"
                )
        return cls(landblock=landblock, path=path,
                   instances=_parse_instances(text),
                   links=_parse_links(text),
                   existed=True)

    @classmethod
    def load(cls, sql_dir: str | Path, landblock: int) -> "LandblockFile":
        """
        Load the landblock's file, or return an empty one if it doesn't exist.

        This is the create-if-missing entry point: callers can always
        ``load(...)`` then ``add_instance(...)`` then ``save()``.
        """
        path = cls.path_for(sql_dir, landblock)
        if not path.exists():
            return cls.create(sql_dir, landblock)
        return cls.parse(path.read_text(encoding="utf-8", errors="replace"),
                         landblock, path)

    # ── queries ─────────────────────────────────────────────────────────────

    def by_guid(self, guid: int) -> Optional[Instance]:
        return next((i for i in self.instances if i.guid == guid), None)

    def children_of(self, parent_guid: int) -> List[Instance]:
        child_guids = {l.child_guid for l in self.links
                       if l.parent_guid == parent_guid}
        return [i for i in self.instances if i.guid in child_guids]

    def next_sequence(self) -> int:
        """
        One past the highest sequence this file has ever held.

        Deliberately *not* gap-filling: 712 of the 3,692 retail files have gaps
        from removed content, and reusing a freed guid would silently re-point
        any link or external reference that still names it. The high-water mark
        makes that true across removals too, not just across loads.
        """
        used = [guid_sequence(i.guid) for i in self.instances
                if guid_landblock(i.guid) == self.landblock]
        high = max(used, default=-1)
        if high > self._seq_high_water:
            self._seq_high_water = high
        return self._seq_high_water + 1

    # ── mutation ────────────────────────────────────────────────────────────

    def add_instance(
        self,
        wcid: int,
        cell: int,
        x: float,
        y: float,
        z: float,
        heading_deg: Optional[float] = None,
        quaternion: Optional[Sequence[float]] = None,
        name: str = "",
        is_link_child: bool = False,
        guid: Optional[int] = None,
    ) -> int:
        """
        Add a placement and return its guid.

        Orientation comes from ``heading_deg`` (simple case) or an explicit
        ``quaternion`` as (w, x, y, z). Omitting both means identity/north.
        """
        if quaternion is not None:
            if len(quaternion) != 4:
                raise LandblockError("quaternion must be (w, x, y, z)")
            w, qx, qy, qz = (float(v) for v in quaternion)
        elif heading_deg is not None:
            w, qx, qy, qz = heading_to_quaternion(heading_deg)
        else:
            w, qx, qy, qz = 1.0, 0.0, 0.0, 0.0

        if guid is None:
            guid = make_guid(self.landblock, self.next_sequence())
        elif self.by_guid(guid) is not None:
            raise LandblockError(f"guid 0x{guid:08X} already present")
        if guid_landblock(guid) == self.landblock:
            self._seq_high_water = max(self._seq_high_water, guid_sequence(guid))

        self.instances.append(Instance(
            guid=guid, wcid=wcid,
            obj_cell_id=make_obj_cell_id(self.landblock, cell),
            x=x, y=y, z=z,
            angles_w=w, angles_x=qx, angles_y=qy, angles_z=qz,
            is_link_child=is_link_child, name=name,
        ))
        return guid

    def add_link(self, parent_guid: int, child_guid: int) -> None:
        """
        Link a child instance to a generator parent.

        Also flips the child's ``is_Link_Child`` flag, which is what tells ACE
        the generator owns its lifecycle.
        """
        parent = self.by_guid(parent_guid)
        child = self.by_guid(child_guid)
        if parent is None:
            raise LandblockError(f"parent 0x{parent_guid:08X} not in this landblock")
        if child is None:
            raise LandblockError(f"child 0x{child_guid:08X} not in this landblock")
        if any(l.parent_guid == parent_guid and l.child_guid == child_guid
               for l in self.links):
            return
        if child.raw is not None and not child.is_link_child:
            child.raw = None          # must re-render to flip the flag
        child.is_link_child = True
        self.links.append(Link(parent_guid=parent_guid, child_guid=child_guid,
                               child_name=child.name, child_wcid=child.wcid))

    def remove_instance(self, guid: int) -> bool:
        """Remove an instance and any links touching it."""
        inst = self.by_guid(guid)
        if inst is None:
            return False
        self.instances.remove(inst)
        self.links = [l for l in self.links
                      if l.parent_guid != guid and l.child_guid != guid]
        return True

    # ── rendering ───────────────────────────────────────────────────────────

    def render(self) -> str:
        """Full file text. Untouched instances keep their original bytes."""
        parts = [f"DELETE FROM `landblock_instance` WHERE "
                 f"`landblock` = 0x{self.landblock:04X};\n"]

        links_by_parent: Dict[int, List[Link]] = {}
        for link in self.links:
            links_by_parent.setdefault(link.parent_guid, []).append(link)

        for inst in self.instances:
            parts.append("\n")
            parts.append(inst.render())
            for link_block in (links_by_parent.pop(inst.guid, None),):
                if link_block:
                    parts.append("\n")
                    parts.append(self._render_link_block(link_block))

        # Links whose parent isn't in this file (shouldn't happen, but never
        # silently drop data).
        for orphan in links_by_parent.values():
            parts.append("\n")
            parts.append(self._render_link_block(orphan))

        return "".join(parts)

    @staticmethod
    def _render_link_block(links: Sequence[Link]) -> str:
        head = f"INSERT INTO `landblock_instance_link` ({_LINK_COLS})\nVALUES "
        rows = [l.render_row() for l in links]
        body = ("\n     , ".join(rows)) + ";\n"
        return head + body

    def save(self, path: Optional[str | Path] = None) -> Path:
        """
        Write the file, creating the folder if needed.

        Uses LF endings and a temp-file swap so an interrupted write can't
        truncate a good file.
        """
        target = Path(path) if path is not None else self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(self.render(), encoding="utf-8", newline="\n")
        tmp.replace(target)
        self.path = target
        self.existed = True
        return target


# ── convenience ──────────────────────────────────────────────────────────────

def place_weenie(
    sql_dir: str | Path,
    landblock: int,
    wcid: int,
    cell: int,
    x: float,
    y: float,
    z: float,
    heading_deg: float = 0.0,
    name: str = "",
    save: bool = True,
) -> Tuple[LandblockFile, int]:
    """
    Place one weenie, creating the landblock file if it doesn't exist yet.

    Returns the (file, guid). This is the single call the world editor needs
    for the common case.
    """
    lb = LandblockFile.load(sql_dir, landblock)
    guid = lb.add_instance(wcid=wcid, cell=cell, x=x, y=y, z=z,
                           heading_deg=heading_deg, name=name)
    if save:
        lb.save()
    return lb, guid


def parse_teleloc(text: str) -> Optional[Dict[str, float | int]]:
    """
    Parse an admin ``/loc`` or ``@teleloc`` string into placement fields.

    Accepts the retail comment form and the looser form the client prints::

        0x00070111 [24.750000 -40.000000 0.000000] 0.707107 0 0 -0.707107
    """
    m = re.search(
        r"0x([0-9A-Fa-f]{8})\s*\[\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\]"
        r"(?:\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+))?",
        text,
    )
    if not m:
        return None
    obj_cell = int(m.group(1), 16)
    out: Dict[str, float | int] = {
        "obj_cell_id": obj_cell,
        "landblock": (obj_cell >> 16) & 0xFFFF,
        "cell": obj_cell & 0xFFFF,
        "x": float(m.group(2)), "y": float(m.group(3)), "z": float(m.group(4)),
    }
    if m.group(5) is not None:
        out.update(angles_w=float(m.group(5)), angles_x=float(m.group(6)),
                   angles_y=float(m.group(7)), angles_z=float(m.group(8)))
    return out
