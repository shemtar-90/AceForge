"""
landblock_dat.py — client_cell_1.dat landblock reader and terrain mesh builder.

Supplies the *canvas* for world placement: the terrain surface a user clicks on,
plus the static scenery that gives it context. Placement itself is written by
:mod:`aceforge.landblock`; nothing here touches server data.

Kept separate from :mod:`aceforge.dat_loader` on purpose — that module owns the
portal.dat model pipeline and its GLB cache is keyed by ``_PARSER_VERSION``.
Adding terrain there would invalidate every cached character/item model for a
feature that doesn't use them.

    cell = DatDatabase(cell_dat_path)
    portal = DatDatabase(portal_dat_path)
    lb = read_landblock(cell, portal, 0xC6A9)
    mesh = build_terrain_mesh(lb)          # positions/normals/colors/indices
    z = lb.height_at(96.0, 96.0)           # exact terrain Z for placement

Coordinates are landblock-local metres: x and y both run 0…192, matching the
``origin_X``/``origin_Y`` of an outdoor ``landblock_instance`` row (cell 0x0000).
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import struct
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .dat_loader import (
    DatDatabase, REGION_ID, _pack_glb, _parse_polygon_flat,
    parse_surface_texture, parse_terrain_textures, parse_texture,
)

# ── constants ────────────────────────────────────────────────────────────────

CELL_SIZE = 24.0          # metres between terrain vertices
LANDBLOCK_CELLS = 8       # cells per edge
LANDBLOCK_VERTS = 9       # vertices per edge (cells + 1)
LANDBLOCK_SIZE = CELL_SIZE * LANDBLOCK_CELLS       # 192.0 m
VERTS_PER_LANDBLOCK = LANDBLOCK_VERTS * LANDBLOCK_VERTS   # 81

#: Terrain type index → display colour. Names come from the Region's
#: TerrainTypes list (see ``dat_loader.parse_terrain_textures``); the colours
#: are ours, chosen so a landblock reads clearly as a placement canvas.
TERRAIN_COLORS: Dict[int, Tuple[int, int, int]] = {
    0:  (122, 118, 110),   # BarrenRock
    1:  (104, 138,  66),   # Grassland
    2:  (222, 236, 242),   # Ice
    3:  ( 82, 130,  48),   # LushGrass
    4:  ( 88, 102,  66),   # MarshSparseSwamp
    5:  (110,  88,  62),   # MudRichDirt
    6:  ( 52,  48,  56),   # ObsidianPlain
    7:  (134, 112,  82),   # PackedDirt
    8:  (140, 124,  92),   # PatchyDirt
    9:  (120, 136,  78),   # PatchyGrassland
    10: (214, 196, 138),   # sand-yellow
    11: (176, 172, 158),   # sand-grey
    12: (164, 152, 128),   # sand-rockStrewn
    13: (140, 130, 112),   # SedimentaryRock
    14: (128, 124, 112),   # SemiBarrenRock
    15: (240, 244, 248),   # Snow
    16: ( 74, 128, 158),   # WaterRunning
    17: ( 68, 116, 148),   # WaterStandingFresh
    18: ( 78, 140, 172),   # WaterShallowSea
    19: ( 84, 146, 176),   # WaterShallowStillSea
    20: ( 40,  84, 124),   # WaterDeepSea
    21: ( 74, 100,  54),   # forestfloor
    22: ( 80, 132, 160),   # FauxWaterRunning
    23: ( 96, 128,  72),   # SeaSlime
    24: (150, 116,  84),   # Argila
    25: (128,  58,  40),   # Volcano1
    26: (108,  46,  34),   # Volcano2
    27: (168, 208, 226),   # BlueIce
    28: ( 92, 122,  70),   # Moss
    29: ( 68,  92,  54),   # DarkMoss
    30: (142, 128,  74),   # olthoi
    31: (118, 106,  88),   # DesolateLands
}
_DEFAULT_COLOR = (128, 128, 128)


class LandblockDatError(Exception):
    """Raised when a landblock cannot be read from cell.dat."""


# ── ids ──────────────────────────────────────────────────────────────────────

def terrain_file_id(landblock: int) -> int:
    """cell.dat file id holding a landblock's terrain (``0xXXXXFFFF``)."""
    return ((landblock & 0xFFFF) << 16) | 0xFFFF


def info_file_id(landblock: int) -> int:
    """cell.dat file id holding a landblock's static objects (``0xXXXXFFFE``)."""
    return ((landblock & 0xFFFF) << 16) | 0xFFFE


def landblock_xy(landblock: int) -> Tuple[int, int]:
    """Landblock id → (x, y) grid coords. Ids are ``x << 8 | y``."""
    return (landblock >> 8) & 0xFF, landblock & 0xFF


# ── height table ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=4)
def _land_height_table_cached(portal_path: str) -> Tuple[float, ...]:
    db = DatDatabase(portal_path)
    try:
        return tuple(read_land_height_table(db))
    finally:
        db.close()


def read_land_height_table(portal_db: DatDatabase) -> List[float]:
    """
    The Region's 256-entry LandHeightTable: height byte → metres.

    Located by signature rather than by walking the Region's nested structs —
    the table is the file's only run of 256 float32 that starts at 0.0 and rises
    monotonically, which a scan confirms is unique (exactly one candidate, at
    offset 0x34, running 0 → 700).
    """
    data = portal_db.read_file(REGION_ID)
    if not data or len(data) < 256 * 4:
        raise LandblockDatError("region file missing or too small")
    for off in range(0, len(data) - 256 * 4, 4):
        vals = struct.unpack_from("<256f", data, off)
        if vals[0] != 0.0 or vals[255] <= 0.0:
            continue
        if not all(0.0 <= v <= 1000.0 for v in vals):
            continue
        if all(vals[i] <= vals[i + 1] for i in range(255)):
            return list(vals)
    raise LandblockDatError("LandHeightTable not found in region file")


# ── terrain split (ported from the AC client) ────────────────────────────────

_U32 = 0xFFFFFFFF


def is_sw_to_ne_cut(global_cell_x: int, global_cell_y: int) -> bool:
    """
    Which diagonal splits a terrain cell into two triangles.

    The client picks this pseudo-randomly per global cell in
    ``LandblockStruct.ConstructPolygons``; getting it wrong tilts every sloped
    cell the wrong way, so heights sampled off the mesh disagree with the
    server. Ported verbatim — the C# does signed 32-bit multiplies with
    wraparound then reinterprets as unsigned, which the masking below matches
    bit for bit.
    """
    magic_a = (global_cell_x * 214614067 + 1813693831) & _U32
    magic_b = (global_cell_x * 1109124029) & _U32
    split = (global_cell_y * magic_a - magic_b - 1369149221) & _U32
    return split * 2.3283064e-10 >= 0.5


# ── model ────────────────────────────────────────────────────────────────────

@dataclass
class StaticObject:
    """A piece of scenery baked into the landblock (building, tree, prop)."""
    setup_id: int                    # 0x01xxxxxx Setup / 0x0Dxxxxxx GfxObj
    x: float
    y: float
    z: float
    angles_w: float
    angles_x: float
    angles_y: float
    angles_z: float


@dataclass
class Landblock:
    """One landblock's terrain grid plus its static scenery."""
    landblock: int
    #: 81 raw terrain words, indexed ``x * 9 + y``.
    terrain: List[int]
    #: 81 height-table indices, same ordering.
    height_index: List[int]
    #: The 256-entry table those indices point into.
    height_table: List[float]
    has_objects: bool = False
    static_objects: List[StaticObject] = field(default_factory=list)
    num_cells: int = 0

    # ── per-vertex accessors ────────────────────────────────────────────────

    @staticmethod
    def _vi(vx: int, vy: int) -> int:
        return min(vx, 8) * LANDBLOCK_VERTS + min(vy, 8)

    def height(self, vx: int, vy: int) -> float:
        """Terrain Z at a grid vertex (0-8, 0-8), in metres."""
        return self.height_table[self.height_index[self._vi(vx, vy)]]

    def terrain_type(self, vx: int, vy: int) -> int:
        """Terrain type index (0-31) at a grid vertex — indexes TERRAIN_COLORS."""
        return (self.terrain[self._vi(vx, vy)] >> 2) & 0x1F

    def road(self, vx: int, vy: int) -> int:
        return self.terrain[self._vi(vx, vy)] & 0x3

    def scenery(self, vx: int, vy: int) -> int:
        return (self.terrain[self._vi(vx, vy)] >> 11) & 0x1F

    # ── sampling ────────────────────────────────────────────────────────────

    def height_at(self, x: float, y: float) -> float:
        """
        Exact terrain Z at landblock-local (x, y) in metres.

        Interpolates within whichever triangle the point falls in, honouring the
        cell's split direction, so this agrees with what the client and the
        rendered mesh both show. Ported from ACME's ``TerrainHeightSampler``.
        """
        x = min(max(x, 0.0), LANDBLOCK_SIZE)
        y = min(max(y, 0.0), LANDBLOCK_SIZE)

        cx = min(int(x / CELL_SIZE), LANDBLOCK_CELLS - 1)
        cy = min(int(y / CELL_SIZE), LANDBLOCK_CELLS - 1)
        fx = (x - cx * CELL_SIZE) / CELL_SIZE
        fy = (y - cy * CELL_SIZE) / CELL_SIZE

        h_sw = self.height(cx, cy)
        h_se = self.height(cx + 1, cy)
        h_nw = self.height(cx, cy + 1)
        h_ne = self.height(cx + 1, cy + 1)

        lbx, lby = landblock_xy(self.landblock)
        if is_sw_to_ne_cut(lbx * LANDBLOCK_CELLS + cx, lby * LANDBLOCK_CELLS + cy):
            if fx > fy:
                return h_sw + fx * (h_se - h_sw) + fy * (h_ne - h_se)
            return h_sw + fx * (h_ne - h_nw) + fy * (h_nw - h_sw)
        if fx + fy <= 1.0:
            return h_sw + fx * (h_se - h_sw) + fy * (h_nw - h_sw)
        return h_ne + (1.0 - fx) * (h_nw - h_ne) + (1.0 - fy) * (h_se - h_ne)

    # ── convenience for placement ───────────────────────────────────────────

    def placement_at(self, x: float, y: float,
                     z_offset: float = 0.0) -> Dict[str, float | int]:
        """
        Turn a click on this landblock into the fields an outdoor
        ``landblock_instance`` row needs.

        Outdoor rows always use cell ``0x0000`` with landblock-local origins —
        that holds for all 40,289 outdoor rows in the retail corpus.
        """
        return {
            "landblock": self.landblock,
            "cell": 0x0000,
            "x": round(x, 6),
            "y": round(y, 6),
            "z": round(self.height_at(x, y) + z_offset, 6),
        }


# ── reading ──────────────────────────────────────────────────────────────────

def read_landblock(cell_db: DatDatabase,
                   portal_db: DatDatabase,
                   landblock: int,
                   with_objects: bool = True) -> Landblock:
    """
    Read a landblock's terrain (and optionally its static scenery).

    Terrain file layout (252 bytes, verified against cell.dat)::

        uint32  id                 0xXXXXFFFF
        uint32  hasObjects
        uint16  terrain[81]        x-major: index = x * 9 + y
        uint8   height[81]         indices into the LandHeightTable
    """
    data = cell_db.read_file(terrain_file_id(landblock))
    if not data or len(data) < 8 + 81 * 2 + 81:
        raise LandblockDatError(
            f"landblock 0x{landblock:04X} has no terrain in cell.dat"
        )

    _id, has_objects = struct.unpack_from("<II", data, 0)
    terrain = list(struct.unpack_from("<81H", data, 8))
    heights = list(struct.unpack_from("<81B", data, 8 + 81 * 2))

    lb = Landblock(
        landblock=landblock,
        terrain=terrain,
        height_index=heights,
        height_table=read_land_height_table(portal_db),
        has_objects=bool(has_objects),
    )
    if with_objects and has_objects:
        _read_landblock_info(cell_db, lb)
    return lb


def _read_landblock_info(cell_db: DatDatabase, lb: Landblock) -> None:
    """
    Parse ``0xXXXXFFFE`` — the landblock's static scenery.

    Layout::

        uint32  id
        uint32  numCells            EnvCell count (dungeon/interior cells)
        uint32  objectCount
        stab    objects[objectCount]    32 bytes: uint32 id, 3f origin, 4f quat
        uint16  numBuildings
        uint16  packMask
        …buildings (not parsed; they resolve through EnvCells)
    """
    data = cell_db.read_file(info_file_id(lb.landblock))
    if not data or len(data) < 12:
        return
    _id, num_cells, obj_count = struct.unpack_from("<III", data, 0)
    lb.num_cells = num_cells
    if obj_count > 4096 or 12 + obj_count * 32 > len(data):
        return                        # refuse to trust a bad count
    off = 12
    for _ in range(obj_count):
        oid, ox, oy, oz, qw, qx, qy, qz = struct.unpack_from("<I7f", data, off)
        lb.static_objects.append(StaticObject(oid, ox, oy, oz, qw, qx, qy, qz))
        off += 32


# ── EnvCells (dungeon / building interiors) ──────────────────────────────────
#
# Dungeon content lives in EnvCells, not on the terrain: 97% of a typical
# server's landblock_instance rows sit in cells >= 0x0100. Those rows are
# positioned in the *cell frame's* coordinate space, which is NOT the terrain
# space — x runs past 192 and y is negative — so a dungeon gets its own view
# rather than markers layered on the surface.

#: Interior cells are a regular 10 x 10 x 6 m grid. Verified against 3,000
#: retail indoor rows: offsets from the frame straddle 0 symmetrically in x/y
#: (p05 -3.9, p95 +3.8) so the frame is the cell **centre**, while dz is >= 0
#: with p95 +0.20 so it is the **floor**, not the mid-height.
ENVCELL_SIZE_XY = 10.0
ENVCELL_HEIGHT = 6.0

#: First interior cell id. Below this is outdoor terrain (cell 0x0000).
ENVCELL_FIRST = 0x0100
ENVCELL_LAST = 0xFF00


@dataclass
class EnvCell:
    """One interior cell — a room or corridor segment."""
    cell_id: int                      # full obj_cell_id, e.g. 0x00070100
    cell: int                         # low 16 bits, e.g. 0x0100
    x: float
    y: float
    z: float                          # floor height
    angles_w: float
    angles_x: float
    angles_y: float
    angles_z: float
    environment_id: int               # 0x0D…… Environment holding the geometry
    num_surfaces: int
    num_portals: int

    @property
    def floor_center(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


def _parse_envcell(data: bytes) -> Optional[EnvCell]:
    """
    Parse an EnvCell header far enough to place it.

    Layout::

        uint32 id; uint32 flags; uint32 cellId
        uint8  numSurfaces; uint8 numPortals; uint16 numStabs
        uint16 surfaces[numSurfaces]
        uint16 environmentId; uint16 cellStructure
        float  x, y, z, qw, qx, qy, qz          <- the frame

    Everything after the frame (portals, visible cells, static objects) is
    only needed to draw the room, which is the next tier of work.
    """
    if not data or len(data) < 20:
        return None
    try:
        cell_id, _flags, _cell_id2 = struct.unpack_from("<III", data, 0)
        off = 12
        num_surfaces, num_portals = data[off], data[off + 1]
        off += 4                                    # + uint16 numStabs
        off += 2 * num_surfaces
        environment_id, _cell_structure = struct.unpack_from("<HH", data, off)
        off += 4
        x, y, z, qw, qx, qy, qz = struct.unpack_from("<7f", data, off)
    except struct.error:
        return None
    return EnvCell(cell_id=cell_id, cell=cell_id & 0xFFFF,
                   x=x, y=y, z=z,
                   angles_w=qw, angles_x=qx, angles_y=qy, angles_z=qz,
                   environment_id=environment_id,
                   num_surfaces=num_surfaces, num_portals=num_portals)


def read_envcells(cell_db: DatDatabase, landblock: int) -> List[EnvCell]:
    """Every interior cell in a landblock, ascending by cell id."""
    prefix = (landblock & 0xFFFF) << 16
    ids = sorted(fid for fid in cell_db.entries
                 if (fid >> 16) == (landblock & 0xFFFF)
                 and ENVCELL_FIRST <= (fid & 0xFFFF) < ENVCELL_LAST)
    out: List[EnvCell] = []
    for fid in ids:
        cell = _parse_envcell(cell_db.read_file(fid))
        if cell is not None:
            out.append(cell)
    return out


@dataclass
class DungeonMesh:
    """
    Interior cells as clickable floors plus wireframe outlines.

    Solid boxes would occlude the rooms behind them, so each cell contributes a
    floor quad (what you click to place on) and the 12 edges of its box (what
    makes the layout readable). Real wall/ceiling geometry comes from the
    Environment files and is the next tier.
    """
    positions: List[float]
    normals: List[float]
    colors: List[float]
    indices: List[int]
    edges: List[float]                # line-segment pairs, xyz each
    bounds: Tuple[float, float, float, float, float, float]  # minx,miny,minz,maxx,maxy,maxz
    levels: List[float]               # distinct floor heights, ascending
    #: Per-triangle storey index into ``levels``. Lets the viewer isolate one
    #: floor of a multi-level dungeon without re-reading the DAT.
    tri_level: List[int] = field(default_factory=list)
    #: Per-triangle surface kind: 0 floor, 1 wall, 2 ceiling.
    tri_kind: List[int] = field(default_factory=list)
    #: Per-triangle height within its own cell, 0-255 mapping 0..1 of the cell's
    #: vertical span. This — not :attr:`tri_kind` — drives the cutaway view.
    #: Classifying "ceiling" by a horizontal normal misses vaulted and domed
    #: roofs entirely (in retail landblock 0007's town network only 134 of ~2,400
    #: triangles read as flat ceilings; the rest of the roof registers as wall),
    #: so visibility slices by height instead, which is shape-agnostic.
    tri_height: List[int] = field(default_factory=list)

    @property
    def cell_count(self) -> int:
        """Quads for the box fallback; for real rooms use triangle_count."""
        return len(self.positions) // 12          # 4 verts per cell

    @property
    def triangle_count(self) -> int:
        return len(self.indices) // 3

    def to_base64(self) -> Dict[str, object]:
        def b64f(vals: Sequence[float]) -> str:
            return base64.b64encode(
                struct.pack(f"<{len(vals)}f", *vals)).decode("ascii")
        minx, miny, minz, maxx, maxy, maxz = self.bounds
        return {
            "positions": b64f(self.positions),
            "normals": b64f(self.normals),
            "colors": b64f(self.colors),
            "indices": base64.b64encode(
                struct.pack(f"<{len(self.indices)}I", *self.indices)).decode("ascii"),
            "edges": b64f(self.edges),
            "triLevel": base64.b64encode(bytes(self.tri_level)).decode("ascii"),
            "triKind": base64.b64encode(bytes(self.tri_kind)).decode("ascii"),
            "triHeight": base64.b64encode(bytes(self.tri_height)).decode("ascii"),
            "cellCount": self.cell_count,
            "triangleCount": self.triangle_count,
            "bounds": {"minX": minx, "minY": miny, "minZ": minz,
                       "maxX": maxx, "maxY": maxy, "maxZ": maxz},
            "levels": self.levels,
        }


#: Floor tint per storey, cycled. Distinct hues make a multi-level dungeon
#: readable from outside without needing to slice it.
_LEVEL_COLORS = [
    (0.42, 0.47, 0.58), (0.50, 0.44, 0.36), (0.38, 0.52, 0.46),
    (0.53, 0.42, 0.50), (0.46, 0.50, 0.38), (0.36, 0.45, 0.55),
]


# ── Environment geometry (the actual room shapes) ───────────────────────────
#
# An EnvCell says *where* a room is; its Environment says what shape it is.
# Environments live in portal.dat as 0x0D…… and hold one or more CellStructs;
# the EnvCell's cell_structure field picks which one.
#
# Layout, derived by hand and verified across all 773 retail environments::
#
#     uint32 id
#     uint32 numCellStructs
#     per struct:
#         uint32 key
#         uint32 numVertices
#         uint32 numPolygons
#         uint32 numPhysicsPolygons
#         int32  vertexType          <- CVertexArray starts here
#         uint32 numVertices         (repeats the count above)
#         vertex[]                   u16 idx, u16 numUV, vec3 pos, vec3 normal,
#                                    vec2 uv[numUV]
#         (u16 key + Polygon)[numPolygons]
#         … physics polygons and BSP tree follow; not needed to draw or hit-test
#
# Vertices are cell-local: centred on x/y with the floor at z=0, spanning
# roughly -5..5 and 0..6, which is exactly how the EnvCell frame is defined.

ENVIRONMENT_TYPE = 0x0D


@dataclass
class CellGeometry:
    """One CellStruct — a room shape in cell-local coordinates."""
    key: int
    vertices: Dict[int, Tuple[float, float, float]]
    #: Triangulated polygons as vertex-id triples.
    triangles: List[Tuple[int, int, int]]

    def bounds(self) -> Tuple[float, float, float, float, float, float]:
        if not self.vertices:
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        xs = [v[0] for v in self.vertices.values()]
        ys = [v[1] for v in self.vertices.values()]
        zs = [v[2] for v in self.vertices.values()]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def environment_file_id(environment_id: int) -> int:
    """EnvCell's 16-bit environment field → the portal.dat file id."""
    return (ENVIRONMENT_TYPE << 24) | (environment_id & 0x00FFFFFF)


def parse_environment(portal_db: DatDatabase,
                      environment_id: int) -> Dict[int, CellGeometry]:
    """
    Parse an Environment into ``{cell_struct_key: CellGeometry}``.

    Returns {} rather than raising if the file is missing or malformed — a
    single bad room should not take down a whole landblock's view.
    """
    data = portal_db.read_file(environment_file_id(environment_id))
    if not data or len(data) < 8:
        return {}
    out: Dict[int, CellGeometry] = {}
    try:
        off = 4                                   # skip id
        num_structs, = struct.unpack_from("<I", data, off)
        off += 4
        if num_structs > 4096:
            return {}
        for _ in range(num_structs):
            key, = struct.unpack_from("<I", data, off)
            off += 4
            n_verts, n_polys, _n_phys = struct.unpack_from("<3I", data, off)
            off += 12
            _vtype, n_verts2 = struct.unpack_from("<iI", data, off)
            off += 8
            if n_verts2 > 65535 or n_polys > 65535:
                return out
            vertices: Dict[int, Tuple[float, float, float]] = {}
            for _ in range(n_verts2):
                vidx, n_uv = struct.unpack_from("<HH", data, off)
                off += 4
                px, py, pz = struct.unpack_from("<3f", data, off)
                off += 24                          # position + normal
                off += 8 * n_uv
                vertices[vidx] = (px, py, pz)
            triangles: List[Tuple[int, int, int]] = []
            for _ in range(n_polys):
                off += 2                           # polygon dictionary key
                poly, off = _parse_polygon_flat(data, off)
                ids = poly.vertex_ids
                # Polygons are convex fans; triangulate around the first vertex.
                for i in range(1, len(ids) - 1):
                    triangles.append((ids[0], ids[i], ids[i + 1]))
            out[key] = CellGeometry(key=key, vertices=vertices,
                                    triangles=triangles)
            # Physics polygons and the BSP tree follow. Their length varies and
            # we don't need them, so stop after the first struct unless more
            # were declared — multi-struct environments are re-read per key.
            if num_structs == 1:
                break
    except (struct.error, IndexError):
        return out
    return out


def _rotate(q: Tuple[float, float, float, float],
            v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Rotate a vector by quaternion (w, x, y, z)."""
    w, x, y, z = q
    vx, vy, vz = v
    # t = 2 * (q_vec x v); v' = v + w*t + q_vec x t
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (vx + w * tx + (y * tz - z * ty),
            vy + w * ty + (z * tx - x * tz),
            vz + w * tz + (x * ty - y * tx))


def cell_local_point(cell: EnvCell,
                     point: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """World point → the cell's local space (inverse of its frame transform)."""
    d = (point[0] - cell.x, point[1] - cell.y, point[2] - cell.z)
    conj = (cell.angles_w, -cell.angles_x, -cell.angles_y, -cell.angles_z)
    return _rotate(conj, d)


def resolve_cell_candidates(
    cells: Sequence[EnvCell],
    geoms: Dict[int, CellGeometry],
    point: Tuple[float, float, float],
    epsilon: float = 1.0,
) -> List[Tuple[int, float]]:
    """
    Which interior cells could contain ``point``, best first.

    Ranked by how far *inside* the cell's local AABB the point sits, so a point
    well within one room outranks one grazing another's edge.

    **This is a shortlist, not an answer.** Measured against 11,198 retail
    indoor rows: the point resolves to exactly one candidate and that candidate
    is right only 37% of the time; a single candidate is still wrong 6% of the
    time it occurs; 23% of positions match no cell at all. Cell membership is
    genuinely not recoverable from a position — AC stores it, it doesn't derive
    it — so callers must let the user confirm rather than auto-assigning.
    """
    out: List[Tuple[int, float]] = []
    for cell in cells:
        geom = geoms.get(cell.environment_id)
        if geom is None or not geom.vertices:
            continue
        b = geom.bounds()
        lx, ly, lz = cell_local_point(cell, point)
        if not (b[0] - epsilon <= lx <= b[3] + epsilon
                and b[1] - epsilon <= ly <= b[4] + epsilon
                and b[2] - epsilon <= lz <= b[5] + epsilon):
            continue
        depth = min(lx - b[0], b[3] - lx, ly - b[1],
                    b[4] - ly, lz - b[2], b[5] - lz)
        out.append((cell.cell, depth))
    out.sort(key=lambda t: -t[1])
    return out


def cell_world_triangles(cell: EnvCell,
                         geom: CellGeometry) -> List[Tuple[Tuple[float, float, float], ...]]:
    """
    A cell's triangles transformed into the landblock's interior space.

    Cell-local vertices are rotated by the cell's quaternion and translated to
    its frame — the same transform the client applies, which is what makes the
    result line up with the stored ``origin_X/Y/Z`` of indoor instances.
    """
    q = (cell.angles_w, cell.angles_x, cell.angles_y, cell.angles_z)
    out = []
    for a, b, c in geom.triangles:
        tri = []
        ok = True
        for vid in (a, b, c):
            v = geom.vertices.get(vid)
            if v is None:
                ok = False
                break
            rx, ry, rz = _rotate(q, v)
            tri.append((rx + cell.x, ry + cell.y, rz + cell.z))
        if ok:
            out.append(tuple(tri))
    return out


def group_cells_by_frame(cells: Sequence[EnvCell]) -> List[Tuple[Tuple[float, float, float], List[EnvCell]]]:
    """
    Group cells that share a frame position.

    Many EnvCells sit at the *same* origin — up to 28 of them in one retail
    building — because the frame belongs to the containing structure and each
    cell's real extent lives in its Environment geometry. So a frame is a
    *location*, not a room, and it can't be used to tell cells apart.
    """
    groups: Dict[Tuple[float, float, float], List[EnvCell]] = {}
    for c in cells:
        groups.setdefault((round(c.x, 2), round(c.y, 2), round(c.z, 2)), []).append(c)
    return sorted(groups.items(), key=lambda kv: (kv[0][2], kv[0][1], kv[0][0]))


def build_room_mesh(cells: Sequence[EnvCell],
                    geoms: Dict[int, CellGeometry]) -> DungeonMesh:
    """
    The real room surfaces, from Environment geometry.

    Each cell's CellStruct triangles are rotated and translated by its frame,
    which is the same transform the client applies — so the result lines up
    with the stored ``origin_X/Y/Z`` of indoor rows.

    Note the geometry is *surfaces*, not closed solids: a cell can be a bare
    floor, a wall slice, or a thin slab. That's why containment uses the local
    AABB (see :func:`resolve_cell_candidates`) rather than a ray-parity test,
    which needs watertight meshes and gives nonsense here.
    """
    positions: List[float] = []
    normals: List[float] = []
    colors: List[float] = []
    indices: List[int] = []
    edges: List[float] = []

    if not cells:
        return DungeonMesh([], [], [], [], [], (0, 0, 0, 0, 0, 0), [])

    levels = sorted({round(c.z, 3) for c in cells})
    level_index = {z: i for i, z in enumerate(levels)}
    minx = miny = minz = float("inf")
    maxx = maxy = maxz = float("-inf")

    tri_level: List[int] = []
    tri_kind: List[int] = []
    tri_height: List[int] = []

    for cell in cells:
        geom = geoms.get(cell.environment_id)
        if geom is None or not geom.triangles:
            continue
        lvl = level_index[round(cell.z, 3)]
        color = _LEVEL_COLORS[lvl % len(_LEVEL_COLORS)]
        gb = geom.bounds()
        span = max(gb[5] - gb[2], 0.001)          # cell height, for the mid-line
        for tri in cell_world_triangles(cell, geom):
            a, b, c = tri
            nx, ny, nz = _normal(a, b, c)
            # Near-horizontal surfaces are floor or ceiling depending on whether
            # they sit in the lower or upper half of their own cell; everything
            # else is wall. Winding varies, so classify on |nz| not its sign.
            height = (a[2] + b[2] + c[2]) / 3.0 - cell.z
            if abs(nz) > 0.7:
                kind = 0 if height < span * 0.5 else 2
            else:
                kind = 1
            frac = 0.0 if span <= 0 else height / span
            tri_height.append(max(0, min(255, int(frac * 255.0))))
            base = len(positions) // 3
            for v in tri:
                positions.extend(v)
                normals.extend((nx, ny, nz))
                colors.extend(color)
                minx, miny, minz = min(minx, v[0]), min(miny, v[1]), min(minz, v[2])
                maxx, maxy, maxz = max(maxx, v[0]), max(maxy, v[1]), max(maxz, v[2])
            indices.extend((base, base + 1, base + 2))
            tri_level.append(min(lvl, 255))
            tri_kind.append(kind)

    if not positions:
        return DungeonMesh([], [], [], [], [], (0, 0, 0, 0, 0, 0), levels)
    return DungeonMesh(positions, normals, colors, indices, edges,
                       (minx, miny, minz, maxx, maxy, maxz), levels,
                       tri_level, tri_kind, tri_height)


def build_dungeon_mesh(cells: Sequence[EnvCell]) -> DungeonMesh:
    """
    Fallback placeholder: floor quads + box wireframes, one box per frame.

    Used only when Environment geometry is unavailable. Drawing a box per
    *cell* would stack up to 28 identical boxes on one spot and imply detail we
    don't have, so boxes are per distinct frame position.
    """
    positions: List[float] = []
    normals: List[float] = []
    colors: List[float] = []
    indices: List[int] = []
    edges: List[float] = []

    if not cells:
        return DungeonMesh([], [], [], [], [], (0, 0, 0, 0, 0, 0), [])

    groups = group_cells_by_frame(cells)
    levels = sorted({round(c.z, 3) for c in cells})
    level_index = {z: i for i, z in enumerate(levels)}
    h = ENVCELL_SIZE_XY / 2.0

    minx = miny = minz = float("inf")
    maxx = maxy = maxz = float("-inf")

    for (cx, cy, cz), members in groups:
        c = members[0]
        x0, x1 = cx - h, cx + h
        y0, y1 = cy - h, cy + h
        z0, z1 = cz, cz + ENVCELL_HEIGHT
        minx, miny, minz = min(minx, x0), min(miny, y0), min(minz, z0)
        maxx, maxy, maxz = max(maxx, x1), max(maxy, y1), max(maxz, z1)

        base = len(positions) // 3
        for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            positions.extend((px, py, z0))
            normals.extend((0.0, 0.0, 1.0))
            colors.extend(_LEVEL_COLORS[level_index[round(c.z, 3)] % len(_LEVEL_COLORS)])
        indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))

        # 12 edges of the cell box
        low = ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))
        high = ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
        for i in range(4):
            j = (i + 1) % 4
            edges.extend(low[i] + low[j])          # floor ring
            edges.extend(high[i] + high[j])        # ceiling ring
            edges.extend(low[i] + high[i])         # vertical

    return DungeonMesh(positions, normals, colors, indices, edges,
                       (minx, miny, minz, maxx, maxy, maxz), levels)


# ── terrain texture atlas ────────────────────────────────────────────────────
#
# The 32 terrain types each have a 512x512 texture in portal.dat. Decoding and
# downscaling all of them takes ~6 s, far too slow to repeat on every landblock
# load, so the result is cached to disk keyed by DAT identity + tile size.
# One atlas serves every landblock.

#: Atlas grid. 32 types fit an 8x4 sheet.
ATLAS_COLS = 8
ATLAS_ROWS = 4
#: Per-tile pixels. 64 keeps the encoded sheet near 300 KB; 128 is ~1.25 MB,
#: which is a lot to hand to the web view for a background surface.
ATLAS_TILE = 64
_ATLAS_VERSION = 1          # bump to invalidate cached sheets


def _atlas_cache_path(portal_path: str, tile: int) -> Path:
    p = Path(portal_path)
    try:
        stamp = f"{p.stat().st_size}:{int(p.stat().st_mtime)}"
    except OSError:
        stamp = "0:0"
    key = hashlib.sha1(f"{p.resolve()}|{stamp}|{tile}|{_ATLAS_VERSION}"
                       .encode()).hexdigest()[:16]
    base = Path(os.environ.get("APPDATA", Path.home())) / "ACEForge" / "cache"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"terrain_atlas_{key}.png"


def build_terrain_atlas(portal_db: DatDatabase, portal_path: str,
                        tile: int = ATLAS_TILE) -> Optional[bytes]:
    """
    A single PNG holding all 32 terrain textures on an 8x4 grid, tile-indexed
    by terrain type. Returns None if Pillow is unavailable.

    Cached to ``%APPDATA%/ACEForge/cache`` — building it decodes 32 DXT textures
    and is far too slow to do per load.
    """
    cache = _atlas_cache_path(portal_path, tile)
    if cache.exists():
        try:
            return cache.read_bytes()
        except OSError:
            pass
    try:
        from PIL import Image
    except ImportError:
        return None

    sheet = Image.new("RGB", (ATLAS_COLS * tile, ATLAS_ROWS * tile), (110, 110, 110))
    for entry in parse_terrain_textures(portal_db):
        idx = entry["index"]
        if idx >= ATLAS_COLS * ATLAS_ROWS:
            continue
        tex_id = parse_surface_texture(portal_db, entry["texture"])
        tex = parse_texture(portal_db, tex_id) if tex_id else None
        if tex is None:
            continue
        img = Image.frombytes("RGBA", (tex.width, tex.height),
                              bytes(tex.to_rgba())).convert("RGB")
        img = img.resize((tile, tile), Image.LANCZOS)
        sheet.paste(img, ((idx % ATLAS_COLS) * tile, (idx // ATLAS_COLS) * tile))

    buf = io.BytesIO()
    sheet.save(buf, "PNG", optimize=True)
    data = buf.getvalue()
    try:
        cache.write_bytes(data)
    except OSError:
        pass
    return data


def landblock_exists(cell_db: DatDatabase, landblock: int) -> bool:
    return terrain_file_id(landblock) in cell_db.entries


def list_landblocks(cell_db: DatDatabase) -> List[int]:
    """Every landblock id that has terrain, ascending (65,025 in retail)."""
    return sorted((fid >> 16) & 0xFFFF
                  for fid in cell_db.entries
                  if (fid & 0xFFFF) == 0xFFFF)


# ── mesh building ────────────────────────────────────────────────────────────

@dataclass
class TerrainMesh:
    """
    A landblock's terrain as flat arrays, ready for a GPU buffer.

    Three vertices per triangle (64 cells x 2 triangles x 3 = 384), not a shared
    9x9 grid. Two reasons: adjacent cells may split along opposite diagonals and
    carry different terrain types, so sharing corners would average textures
    across a boundary and bend the surface away from what the client draws; and
    texture blending needs each fragment to know all three of its triangle's
    corner types, which only works if the corners aren't shared.
    """
    positions: List[float]      # xyz triples
    normals: List[float]
    colors: List[float]         # rgb triples, 0-1 — the untextured fallback
    indices: List[int]
    min_z: float
    max_z: float
    #: Per-vertex UV. Tiles once per 24 m cell so textures keep real-world scale.
    uvs: List[float] = field(default_factory=list)
    #: Per-vertex vec3 of the triangle's three corner terrain types. Identical
    #: on all three vertices, so it survives interpolation unchanged.
    types: List[float] = field(default_factory=list)
    #: Per-vertex barycentric weight — (1,0,0), (0,1,0), (0,0,1). Interpolated
    #: across the face it gives each fragment the blend of the three corners.
    weights: List[float] = field(default_factory=list)

    @property
    def vertex_count(self) -> int:
        return len(self.positions) // 3

    @property
    def triangle_count(self) -> int:
        return len(self.indices) // 3

    def to_base64(self) -> Dict[str, object]:
        """Typed arrays as base64 — what the web view consumes."""
        def b64f(vals: Sequence[float]) -> str:
            return base64.b64encode(
                struct.pack(f"<{len(vals)}f", *vals)).decode("ascii")
        return {
            "positions": b64f(self.positions),
            "normals": b64f(self.normals),
            "colors": b64f(self.colors),
            "uvs": b64f(self.uvs),
            "types": b64f(self.types),
            "weights": b64f(self.weights),
            "indices": base64.b64encode(
                struct.pack(f"<{len(self.indices)}I", *self.indices)
            ).decode("ascii"),
            "vertexCount": self.vertex_count,
            "triangleCount": self.triangle_count,
            "minZ": self.min_z,
            "maxZ": self.max_z,
            "size": LANDBLOCK_SIZE,
            "atlasCols": ATLAS_COLS,
            "atlasRows": ATLAS_ROWS,
        }


def _normal(a: Sequence[float], b: Sequence[float],
            c: Sequence[float]) -> Tuple[float, float, float]:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = (nx * nx + ny * ny + nz * nz) ** 0.5
    if length == 0.0:
        return 0.0, 0.0, 1.0
    return nx / length, ny / length, nz / length


_BARYCENTRIC = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def build_terrain_mesh(lb: Landblock) -> TerrainMesh:
    """Build the clickable terrain surface for one landblock."""
    positions: List[float] = []
    normals: List[float] = []
    colors: List[float] = []
    uvs: List[float] = []
    types_out: List[float] = []
    weights: List[float] = []
    indices: List[int] = []
    min_z, max_z = float("inf"), float("-inf")
    lbx, lby = landblock_xy(lb.landblock)

    for cx in range(LANDBLOCK_CELLS):
        for cy in range(LANDBLOCK_CELLS):
            x0, y0 = cx * CELL_SIZE, cy * CELL_SIZE
            x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE
            corners = (
                (x0, y0, lb.height(cx,     cy)),        # 0 SW
                (x1, y0, lb.height(cx + 1, cy)),        # 1 SE
                (x1, y1, lb.height(cx + 1, cy + 1)),    # 2 NE
                (x0, y1, lb.height(cx,     cy + 1)),    # 3 NW
            )
            corner_types = (lb.terrain_type(cx,     cy),
                            lb.terrain_type(cx + 1, cy),
                            lb.terrain_type(cx + 1, cy + 1),
                            lb.terrain_type(cx,     cy + 1))

            sw_ne = is_sw_to_ne_cut(lbx * LANDBLOCK_CELLS + cx,
                                    lby * LANDBLOCK_CELLS + cy)
            tris = ((0, 1, 2), (0, 2, 3)) if sw_ne else ((0, 1, 3), (1, 2, 3))

            for tri in tris:
                a, b, c = (corners[i] for i in tri)
                nx, ny, nz = _normal(a, b, c)
                # All three vertices carry the same triple of corner types, so
                # interpolation leaves it intact; only the weight varies.
                t3 = tuple(float(corner_types[i]) for i in tri)
                base = len(positions) // 3
                for slot, idx in enumerate(tri):
                    corner = corners[idx]
                    positions.extend(corner)
                    normals.extend((nx, ny, nz))
                    r, g, bb = TERRAIN_COLORS.get(corner_types[idx], _DEFAULT_COLOR)
                    colors.extend((r / 255.0, g / 255.0, bb / 255.0))
                    # One texture repeat per 24 m cell keeps real-world scale.
                    uvs.extend((corner[0] / CELL_SIZE, corner[1] / CELL_SIZE))
                    types_out.extend(t3)
                    weights.extend(_BARYCENTRIC[slot])
                    min_z = min(min_z, corner[2])
                    max_z = max(max_z, corner[2])
                indices.extend((base, base + 1, base + 2))

    return TerrainMesh(positions, normals, colors, indices, min_z, max_z,
                       uvs, types_out, weights)


def build_terrain_glb(lb: Landblock) -> bytes:
    """
    The same mesh as a standalone GLB.

    The web view takes :meth:`TerrainMesh.to_base64` directly — terrain is
    generated, not an authored asset, so it needs no glTF loader. This exists
    for parity with ``dat_loader.export_setup_glb`` and for exporting a
    landblock to an external 3D tool.
    """
    mesh = build_terrain_mesh(lb)
    pos = struct.pack(f"<{len(mesh.positions)}f", *mesh.positions)
    nrm = struct.pack(f"<{len(mesh.normals)}f", *mesh.normals)
    col = struct.pack(f"<{len(mesh.colors)}f", *mesh.colors)
    idx = struct.pack(f"<{len(mesh.indices)}I", *mesh.indices)

    blob = b""
    views = []
    for chunk, target in ((pos, 34962), (nrm, 34962), (col, 34962), (idx, 34963)):
        pad = (4 - len(blob) % 4) % 4
        blob += b"\x00" * pad
        views.append({"buffer": 0, "byteOffset": len(blob),
                      "byteLength": len(chunk), "target": target})
        blob += chunk

    n = mesh.vertex_count
    xs = mesh.positions[0::3]
    ys = mesh.positions[1::3]
    gltf = {
        "asset": {"version": "2.0", "generator": "ACEForge landblock_dat"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": f"landblock_{lb.landblock:04X}"}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2},
            "indices": 3, "material": 0,
        }]}],
        "materials": [{
            "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 1.0},
            "doubleSided": True,
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": n, "type": "VEC3",
             "min": [min(xs), min(ys), mesh.min_z],
             "max": [max(xs), max(ys), mesh.max_z]},
            {"bufferView": 1, "componentType": 5126, "count": n, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": n, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5125, "count": len(mesh.indices),
             "type": "SCALAR"},
        ],
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }
    return _pack_glb(json.dumps(gltf, separators=(",", ":")), blob)
