"""
dat_loader.py — Asheron's Call client_portal.dat reader and GLB exporter

Parses the AC binary DAT format (B-tree block-chain file container) and
extracts 3D model data (Setup → GfxObj geometry + textures) into GLB files
that Three.js can render directly.

No external dependencies — pure Python stdlib (struct, io, os, json, zlib).

Supported file types from client_portal.dat:
  0x01xxxxxx — GfxObj   (geometry: vertices, polygons, surface refs)
  0x02xxxxxx — Setup    (assembles GfxObjs into a complete model)
  0x04xxxxxx — Palette  (indexed color table)
  0x05xxxxxx — SurfaceTexture (texture ID → mipmap IDs)
  0x06xxxxxx — Texture  (raw image: PFID_R8G8B8, PFID_A8R8G8B8, PFID_P8, etc.)
  0x08xxxxxx — Surface  (texture + render flags)

Usage:
    db  = DatDatabase(r"C:\\AC\\client_portal.dat")
    glb = export_setup_glb(db, 0x02000001)   # returns bytes or None
"""

from __future__ import annotations

import io
import json
import math
import os
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── DAT header / directory constants ─────────────────────────────────────────

DAT_HEADER_OFFSET = 0x140
ENTRY_SIZE        = 6 * 4          # 6 × uint32 per DatFile entry
DIR_HEADER_SIZE   = 4 + 4 + 62 * (ENTRY_SIZE + 4)   # approx; see DatDirectoryHeader


# ── Low-level DAT reading ─────────────────────────────────────────────────────

def _read_blocks(stream: io.RawIOBase, offset: int, size: int, block_size: int) -> bytes:
    """
    Reconstruct a DAT file from its block chain.
    Each block starts with a 4-byte pointer to the next block (0 = last).
    """
    buf = bytearray()
    stream.seek(offset)
    remaining = size

    while remaining > 0:
        header = stream.read(4)
        if len(header) < 4:
            break
        next_addr = struct.unpack_from("<I", header)[0]

        readable = min(block_size - 4, remaining)
        chunk    = stream.read(readable)
        buf      += chunk
        remaining -= len(chunk)

        if next_addr == 0 or remaining <= 0:
            break
        stream.seek(next_addr)

    return bytes(buf)


@dataclass
class DatEntry:
    object_id:   int
    file_offset: int
    file_size:   int


def _read_directory(stream: io.RawIOBase, offset: int, block_size: int,
                    entries: Dict[int, DatEntry]) -> None:
    """
    Recursively walk the B-tree and collect all DatEntry records.

    DatDirectoryHeader layout (from ACE source DatDirectoryHeader.cs):
      Branches[0x3E]  — 62 × uint32 = 248 bytes  (child sector offsets)
      EntryCount      — 1  × uint32 = 4 bytes
      Entries[]       — EntryCount × DatFile (6 × uint32 = 24 bytes each)

    Branches and entries are NOT interleaved — all 62 branches come first,
    then the count, then all entries sequentially.
    """
    NUM_BRANCHES = 0x3E   # 62

    # Calculate directory header size: 62 branches + 1 count + up to 61 entries
    # We need at least (62+1)*4 bytes = 252 bytes for the branch+count section
    header_min = NUM_BRANCHES * 4 + 4   # branches + EntryCount
    max_entries = NUM_BRANCHES - 1       # max 61 file entries per node

    dir_size = header_min + max_entries * ENTRY_SIZE
    block_data = _read_blocks(stream, offset, dir_size, block_size)
    if len(block_data) < header_min:
        return

    r = io.BytesIO(block_data)

    # Read all 62 branch pointers
    branches = []
    for _ in range(NUM_BRANCHES):
        b_bytes = r.read(4)
        if len(b_bytes) < 4:
            break
        branches.append(struct.unpack_from("<I", b_bytes)[0])

    # Read entry count
    count_bytes = r.read(4)
    if len(count_bytes) < 4:
        return
    entry_count = struct.unpack_from("<I", count_bytes)[0]

    if entry_count > max_entries:
        return  # corrupted or wrong offset

    # Read file entries sequentially
    for i in range(entry_count):
        raw_entry = r.read(ENTRY_SIZE)
        if len(raw_entry) < ENTRY_SIZE:
            break
        _bit_flags, obj_id, file_off, file_size, date, iteration = struct.unpack_from("<6I", raw_entry)
        if obj_id and file_size:
            entries[obj_id] = DatEntry(obj_id, file_off, file_size)

    # Recurse into branch directories (entry_count + 1 active branches)
    for i in range(min(entry_count + 1, len(branches))):
        if branches[i]:
            _read_directory(stream, branches[i], block_size, entries)


class DatDatabase:
    """Minimal client_portal.dat reader — indexes all files, reads on demand."""

    def __init__(self, dat_path: str):
        self.path       = dat_path
        self.block_size = 0
        self.entries:   Dict[int, DatEntry] = {}
        self._stream:   Optional[io.RawIOBase] = None
        self._open()

    def _open(self) -> None:
        f = open(self.path, "rb")
        self._stream = f

        f.seek(DAT_HEADER_OFFSET)
        # DatDatabaseHeader (from ACE source DatDatabaseHeader.cs):
        # [0]  FileType      uint32
        # [1]  BlockSize     uint32
        # [2]  FileSize      uint32
        # [3]  DataSet       uint32  (DatDatabaseType: 1=portal, 2=cell, 4=language)
        # [4]  DataSubset    uint32
        # [5]  FreeHead      uint32
        # [6]  FreeTail      uint32
        # [7]  FreeCount     uint32
        # [8]  BTree         uint32  ← root B-tree sector offset
        # [9]  NewLRU        uint32
        # [10] OldLRU        uint32
        # [11] UseLRU        uint32
        # [12] MasterMapID   uint32
        # [13] EnginePackVer uint32
        # [14] GamePackVer   uint32
        # then 16 bytes VersionMajor + 4 bytes VersionMinor
        header_data = f.read(15 * 4)
        if len(header_data) < 15 * 4:
            raise ValueError("DAT header too short — not a valid AC DAT file")
        h = struct.unpack_from("<15I", header_data)
        self.block_size  = h[1]   # BlockSize  (index 1)
        btree_root       = h[8]   # BTree      (index 8)
        self.dat_type    = h[3]   # DataSet    (index 3, 1=portal)

        if self.block_size < 64 or self.block_size > 65536:
            raise ValueError(f"Unexpected block size {self.block_size} — wrong DAT file?")

        # Walk the B-tree
        _read_directory(f, btree_root, self.block_size, self.entries)

    def read_file(self, object_id: int) -> Optional[bytes]:
        """Read and reassemble a file from the DAT by its object ID."""
        entry = self.entries.get(object_id)
        if entry is None:
            return None
        return _read_blocks(self._stream, entry.file_offset,
                            entry.file_size, self.block_size)

    def files_by_type(self, high_byte: int) -> List[int]:
        """Return all object IDs whose high byte matches (e.g. 0x02 for Setups)."""
        prefix = high_byte << 24
        mask   = 0xFF000000
        return [oid for oid in self.entries if (oid & mask) == prefix]

    def close(self) -> None:
        if self._stream:
            self._stream.close()
            self._stream = None

    def __del__(self):
        self.close()


# ── Struct helpers ────────────────────────────────────────────────────────────

def _u32(data: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<I", data, off)[0], off + 4

def _i16(data: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<h", data, off)[0], off + 2

def _u16(data: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<H", data, off)[0], off + 2

def _u8(data: bytes, off: int) -> Tuple[int, int]:
    return data[off], off + 1

def _i32(data: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<i", data, off)[0], off + 4

def _vec3(data: bytes, off: int) -> Tuple[Tuple[float, float, float], int]:
    x, y, z = struct.unpack_from("<3f", data, off)
    return (x, y, z), off + 12

def _vec2(data: bytes, off: int) -> Tuple[Tuple[float, float], int]:
    u, v = struct.unpack_from("<2f", data, off)
    return (u, v), off + 8

def _smart_array_count(data: bytes, off: int) -> Tuple[int, int]:
    """AC 'smart array': length-prefixed with either u16 or u32 depending on value."""
    n, off = _u16(data, off)
    if n == 0xFFFF:
        n, off = _u32(data, off)
    return n, off


def _packed_dword(data: bytes, off: int) -> Tuple[int, int]:
    """
    AC PackedDWORD: variable-length integer encoding.
    If high bit of first byte is 0: value is just that byte (7-bit value, 0-127).
    If bits 7-6 are 10: 2-byte value (14-bit, mask off top 2 bits).
    If bits 7-6 are 11: 4-byte value (30-bit, mask off top 2 bits).
    """
    b0 = data[off]
    if (b0 & 0x80) == 0:
        return b0, off + 1
    elif (b0 & 0xC0) == 0x80:
        val = struct.unpack_from(">H", data, off)[0] & 0x3FFF
        return val, off + 2
    else:
        val = struct.unpack_from(">I", data, off)[0] & 0x3FFFFFFF
        return val, off + 4


# ── Texture parsing ───────────────────────────────────────────────────────────

# SurfacePixelFormat values we can handle
PFID_R8G8B8    = 0x14
PFID_A8R8G8B8  = 0x15
PFID_DXT1      = 0x31
PFID_DXT5      = 0x33
PFID_P8        = 0x12   # indexed, 8-bit
PFID_INDEX16   = 0x65   # indexed, 16-bit

@dataclass
class AcTexture:
    width:   int
    height:  int
    fmt:     int
    data:    bytes
    palette_id: Optional[int]

    def to_rgba(self, palette: Optional[List[int]] = None) -> bytes:
        """Convert any supported format to raw RGBA8 bytes."""
        w, h = self.width, self.height

        if self.fmt == PFID_A8R8G8B8:
            # BGRA → RGBA
            out = bytearray(w * h * 4)
            for i in range(w * h):
                b, g, r, a = self.data[i*4], self.data[i*4+1], self.data[i*4+2], self.data[i*4+3]
                out[i*4:i*4+4] = (r, g, b, a)
            return bytes(out)

        if self.fmt == PFID_R8G8B8:
            out = bytearray(w * h * 4)
            for i in range(w * h):
                b, g, r = self.data[i*3], self.data[i*3+1], self.data[i*3+2]
                out[i*4:i*4+4] = (r, g, b, 255)
            return bytes(out)

        if self.fmt in (PFID_P8, PFID_INDEX16) and palette:
            out = bytearray(w * h * 4)
            stride = 2 if self.fmt == PFID_INDEX16 else 1
            for i in range(w * h):
                idx = struct.unpack_from("<H" if stride == 2 else "B",
                                        self.data, i * stride)[0]
                color = palette[idx % len(palette)] if idx < len(palette) else 0xFFFFFFFF
                r = (color >> 16) & 0xFF
                g = (color >>  8) & 0xFF
                b =  color        & 0xFF
                a = (color >> 24) & 0xFF
                out[i*4:i*4+4] = (r, g, b, a if a else 255)
            return bytes(out)

        if self.fmt in (PFID_DXT1, PFID_DXT5):
            return _decode_dxt(self.data, w, h, self.fmt == PFID_DXT5)

        # Unknown — return grey
        return bytes([180, 180, 180, 255] * (w * h))


def _decode_dxt(data: bytes, w: int, h: int, is_dxt5: bool) -> bytes:
    """Minimal DXT1/DXT5 decoder."""
    out = bytearray(w * h * 4)
    off = 0
    bw  = max(1, (w + 3) // 4)
    bh  = max(1, (h + 3) // 4)

    def rgb565(v: int) -> Tuple[int, int, int]:
        r = ((v >> 11) & 0x1F) * 255 // 31
        g = ((v >>  5) & 0x3F) * 255 // 63
        b =  (v        & 0x1F) * 255 // 31
        return r, g, b

    for by_ in range(bh):
        for bx in range(bw):
            if is_dxt5:
                # alpha block
                a0, a1 = data[off], data[off+1]
                abits   = int.from_bytes(data[off+2:off+8], "little")
                off    += 8
                alphas  = [0]*8
                alphas[0] = a0; alphas[1] = a1
                if a0 > a1:
                    for i in range(2, 8): alphas[i] = ((8-i)*a0 + (i-1)*a1) // 7
                else:
                    for i in range(2, 6): alphas[i] = ((6-i)*a0 + (i-1)*a1) // 5
                    alphas[6] = 0; alphas[7] = 255
            else:
                alphas = None; abits = 0

            c0v, c1v = struct.unpack_from("<HH", data, off)
            cbits    = struct.unpack_from("<I", data, off+4)[0]
            off     += 8
            c0 = rgb565(c0v); c1 = rgb565(c1v)
            if c0v > c1v:
                cols = [c0, c1,
                        tuple((2*c0[i]+c1[i])//3 for i in range(3)),
                        tuple((c0[i]+2*c1[i])//3 for i in range(3))]
                alphas_c = [255]*4
            else:
                cols = [c0, c1,
                        tuple((c0[i]+c1[i])//2 for i in range(3)),
                        (0,0,0)]
                alphas_c = [255, 255, 255, 0]

            for py in range(4):
                for px in range(4):
                    ci = (cbits >> (2*(py*4+px))) & 3
                    ix = bx*4+px; iy = by_*4+py
                    if ix >= w or iy >= h:
                        continue
                    pidx  = (iy*w+ix)*4
                    r,g,b = cols[ci]
                    a = alphas[int((abits >> (3*(py*4+px))) & 7)] if is_dxt5 else alphas_c[ci]
                    out[pidx:pidx+4] = (r, g, b, a)
    return bytes(out)


def parse_texture(db: DatDatabase, tex_id: int,
                  palette: Optional[List[int]] = None) -> Optional[AcTexture]:
    """Parse a Texture (0x06xxxxxx) entry into an AcTexture."""
    data = db.read_file(tex_id)
    if not data:
        return None
    try:
        off = 0
        obj_id, off = _u32(data, off)
        unknown, off = _i32(data, off)
        width,   off = _i32(data, off)
        height,  off = _i32(data, off)
        fmt,     off = _u32(data, off)
        length,  off = _i32(data, off)
        src = data[off:off+length]; off += length
        pal_id = None
        if fmt in (PFID_P8, PFID_INDEX16) and off + 4 <= len(data):
            pal_id, _ = _u32(data, off)
        return AcTexture(width, height, fmt, src, pal_id)
    except Exception:
        return None


def parse_palette(db: DatDatabase, pal_id: int) -> Optional[List[int]]:
    """Parse a Palette (0x04xxxxxx) into a list of ARGB uint32 values."""
    data = db.read_file(pal_id)
    if not data:
        return None
    try:
        off = 4  # skip object_id
        count, off = _u32(data, off)
        colors = []
        for _ in range(count):
            c, off = _u32(data, off)
            colors.append(c)
        return colors
    except Exception:
        return None


def parse_surface_texture(db: DatDatabase, st_id: int) -> Optional[int]:
    """Parse a SurfaceTexture (0x05xxxxxx) and return the highest-res texture ID."""
    data = db.read_file(st_id)
    if not data:
        return None
    try:
        off = 4  # skip object_id
        unknown, off = _u32(data, off)
        count, off   = _u32(data, off)
        if count == 0:
            return None
        tex_id, _ = _u32(data, off)
        return tex_id
    except Exception:
        return None


# ── GfxObj parsing ────────────────────────────────────────────────────────────

@dataclass
class SWVertex:
    pos: Tuple[float, float, float]
    nrm: Tuple[float, float, float]
    uvs: List[Tuple[float, float]]


@dataclass
class AcPolygon:
    surface_idx: int   # index into GfxObj.surfaces
    vertex_ids:  List[int]
    uv_indices:  List[int]


@dataclass
class GfxObj:
    obj_id:   int
    surfaces: List[int]          # surface (0x08xxxxxx) IDs
    vertices: Dict[int, SWVertex]
    polygons: List[AcPolygon]


# BSP node type constants (4-char ASCII tags stored little-endian as uint32)
_BSP_LEAF = 0x4641454c   # 'LEAF' as LE u32
_BSP_PORT = 0x54524f50   # 'PORT' as LE u32
# Interior node types — tag bytes read as little-endian u32
_BSP_INTERIOR = {
    0x6e6e5042,   # 'BPnn' — no children
    0x6e495042,   # 'BPIn' — positive child only
    0x4e497042,   # 'BpIN' — negative child only
    0x4e6e7042,   # 'BpnN' — negative child only (alt)
    0x4e495042,   # 'BPIN' — both children
    0x4e6e5042,   # 'BPnN' — both children (alt)
}
_BSP_HAS_POS = {0x6e495042, 0x4e495042, 0x4e6e5042}   # BPIn, BPIN, BPnN
_BSP_HAS_NEG = {0x4e497042, 0x4e6e7042, 0x4e495042, 0x4e6e5042}  # BpIN, BpnN, BPIN, BPnN


def _skip_bsp_tree(data: bytes, off: int, bsp_type: str = "Drawing",
                   _depth: int = 0) -> int:
    """
    Skip over a BSP tree without interpreting it.

    Structure (from ACE source BSPNode.cs, BSPLeaf.cs, BSPPortal.cs):

    All nodes:
      type_tag   uint32  (4-char ASCII tag)

    LEAF node:
      LeafIndex  int32
      [if Physics: Solid(i32) + Sphere(16) + numPolys(u32) + numPolys×u16]

    PORT node:
      Plane      16 bytes (vec3 + float)
      PosNode    (recursive)
      NegNode    (recursive)
      [if Drawing: Sphere(16) + numPolys(u32) + numPortals(u32) + polys×u16 + portals×4]

    Interior BPxx nodes:
      Plane      16 bytes
      [conditional children based on type tag]
      [if not Cell: Sphere(16)]
      [if Drawing: numPolys(u32) + polys×u16]
    """
    SPHERE = 16   # vec3 origin + float radius
    PLANE  = 16   # vec3 N + float D

    if off + 4 > len(data):
        return len(data)  # gracefully stop at end of buffer
    node_type, off = _u32(data, off)
    tag = struct.pack("<I", node_type).decode("ascii", errors="replace")

    if node_type == _BSP_LEAF:
        # LeafIndex (int32)
        off += 4
        if bsp_type == "Physics":
            # Solid (int32) + Sphere (16) + numPolys (u32) + polys×u16
            off += 4 + SPHERE
            num_polys, off = _u32(data, off)
            off += num_polys * 2
        return off

    if node_type == _BSP_PORT:
        # Plane + PosNode + NegNode
        off += PLANE
        off = _skip_bsp_tree(data, off, bsp_type, _depth+1)
        off = _skip_bsp_tree(data, off, bsp_type, _depth+1)
        if bsp_type == "Drawing":
            # Sphere + numPolys + numPortals + polys×u16 + portals×4
            off += SPHERE
            num_polys,   off = _u32(data, off)
            num_portals, off = _u32(data, off)
            off += num_polys   * 2
            off += num_portals * 4   # PortalPoly = i16 + i16
        return off

    # Interior BPxx nodes
    # Plane always present
    off += PLANE

    has_pos = node_type in _BSP_HAS_POS
    has_neg = node_type in _BSP_HAS_NEG

    if has_pos:
        off = _skip_bsp_tree(data, off, bsp_type, _depth+1)
    if has_neg:
        off = _skip_bsp_tree(data, off, bsp_type, _depth+1)

    # Sphere (present if not Cell)
    if bsp_type != "Cell":
        off += SPHERE

    # Drawing nodes also have poly references
    if bsp_type == "Drawing":
        num_polys, off = _u32(data, off)
        off += num_polys * 2   # polygon indices as u16

    return off


def parse_gfxobj(data: bytes) -> Optional[GfxObj]:
    """Parse a GfxObj (0x01xxxxxx) binary blob into a GfxObj dataclass."""
    try:
        off = 0
        obj_id, off = _u32(data, off)
        flags,  off = _u32(data, off)

        HAS_PHYSICS = 0x1
        HAS_DRAWING = 0x2
        HAS_DEGRADE = 0x4

        _checkpoints = [f"s:fl={flags:#x}b={len(data)}"]

        # Surface count auto-detect: try u8, u16, u32 — pick first sane value
        _candidates = [
            ("u8",  data[off],                                  off + 1),
            ("u16", struct.unpack_from("<H", data, off)[0],     off + 2),
            ("u32", struct.unpack_from("<I", data, off)[0],     off + 4),
        ]
        nsurfaces, off, _sfmt = 0, off, "?"
        for _fmt, _n, _nxt in _candidates:
            if _n <= 64 and _nxt + _n * 4 <= len(data):
                nsurfaces, off, _sfmt = _n, _nxt, _fmt
                break
        else:
            u8v  = data[_candidates[0][2]-1]
            u16v = _candidates[1][1]
            u32v = _candidates[2][1]
            raise RuntimeError(f"Bad surface count at {_candidates[0][2]-1}: u8={u8v} u16={u16v} u32={u32v}")
        surfaces = []
        for _ in range(nsurfaces):
            sid, off = _u32(data, off)
            surfaces.append(sid)
        _checkpoints.append(f"surfs({nsurfaces},{_sfmt})@{off}")

        # CVertexArray
        vtype, off = _i32(data, off)
        nverts, off = _u32(data, off)
        vertices: Dict[int, SWVertex] = {}
        for vi in range(nverts):
            vidx, off  = _u16(data, off)
            nuv, off   = _u16(data, off)
            pos,  off  = _vec3(data, off)
            nrm,  off  = _vec3(data, off)
            uvs = []
            for _ in range(nuv):
                uv, off = _vec2(data, off)
                uvs.append(uv)
            vertices[vidx] = SWVertex(pos, nrm, uvs)
        _checkpoints.append(f"verts({nverts})@{off}")

        # Physics BSP (skip)
        if flags & HAS_PHYSICS:
            nphy, off = _smart_array_count(data, off)
            for _ in range(nphy):
                _pidx, off = _u16(data, off)
                _pdata, off = _parse_polygon_flat(data, off)
            off = _skip_bsp_tree(data, off, 'Physics')
            _checkpoints.append(f"physBSP@{off}")

        # SortCenter
        _sort_center, off = _vec3(data, off)
        _checkpoints.append(f"sc@{off}")

        # Drawing polygons
        polygons: List[AcPolygon] = []
        if flags & HAS_DRAWING:
            _sc_end = off
            ndraw, off = _smart_array_count(data, off)
            # Dump 40 bytes starting from 20 bytes before sort center end
            _dump_start = max(0, _sc_end - 20)
            _hex_ctx = data[_dump_start:_dump_start+48].hex()
            _checkpoints.append(f"ndraw({ndraw})@{off}|bytes@{_dump_start}:{_hex_ctx}")
            for _pi in range(ndraw):
                _poly_start = off
                _didx, off = _u16(data, off)   # dictionary key
                _poly_hex = data[off:off+8].hex() if off+8 <= len(data) else "short"
                poly, off  = _parse_polygon_flat(data, off)
                polygons.append(poly)
                if _pi == 0:
                    _checkpoints.append(f"p0@{off}(k={_didx},npts={len(poly.vertex_ids)},h={_poly_hex})")
            _checkpoints.append(f"drwpoly@{off}")
            off = _skip_bsp_tree(data, off, 'Drawing')
            _checkpoints.append(f"drwBSP@{off}")

        # DID degrade ref
        if flags & HAS_DEGRADE:
            _checkpoints.append(f"deg@{off}")
            _degrade, off = _u32(data, off)

        return GfxObj(obj_id, surfaces, vertices, polygons)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"parse_gfxobj failed at checkpoints {_checkpoints}: {e}"
        )
        return None  # parse failed — caller skips this GfxObj


def _parse_polygon_flat(data: bytes, off: int) -> Tuple[AcPolygon, int]:
    """Parse a Polygon struct and return (AcPolygon, new_offset)."""
    if off + 10 > len(data):   # minimum polygon = 10 bytes
        return AcPolygon(0, [], []), len(data)

    numpts, off  = _u8(data, off)
    stippling, off = _u8(data, off)
    sides,  off  = _i32(data, off)
    possurf, off = _u16(data, off)
    negsurf, off = _u16(data, off)

    # Sanity-check numpts — a real polygon won't have hundreds of points
    if numpts > 64:
        return AcPolygon(0, [], []), off

    vids = []
    for _ in range(numpts):
        if off + 2 > len(data): break
        vid, off = _u16(data, off)  # vertex indices are unsigned, match the vertex dict keys
        vids.append(vid)

    NO_POS = 0x04
    NO_NEG = 0x08
    puvidx = []
    if not (stippling & NO_POS):
        for _ in range(numpts):
            if off >= len(data): break
            u, off = _u8(data, off)
            puvidx.append(u)

    if sides == 0x2 and not (stippling & NO_NEG):  # CullMode.Clockwise
        for _ in range(numpts):
            if off >= len(data): break
            _, off = _u8(data, off)   # neg UV indices — skip

    surf_idx = possurf if possurf != 0xFFFF else 0  # 0xFFFF = no surface
    return AcPolygon(surf_idx, vids, puvidx), off


# ── Setup parsing ─────────────────────────────────────────────────────────────

@dataclass
class SetupPart:
    gfxobj_id: int

@dataclass
class PartFrame:
    """Position + rotation for one part in the default placement pose."""
    ox: float; oy: float; oz: float          # origin (translation)
    qw: float; qx: float; qy: float; qz: float  # quaternion (rotation)

@dataclass
class AcSetup:
    setup_id:     int
    parts:        List[SetupPart]
    default_scale: float
    frames:       List[PartFrame]   # one per part, from placement frame 0


def _parse_frame(data: bytes, off: int) -> Tuple["PartFrame", int]:
    """Parse one Frame (Origin + Quaternion) = 28 bytes."""
    ox, oy, oz, qw, qx, qy, qz = struct.unpack_from("<7f", data, off)
    return PartFrame(ox, oy, oz, qw, qx, qy, qz), off + 28


def parse_setup(data: bytes) -> Optional[AcSetup]:
    """
    Parse a Setup (0x02xxxxxx) binary blob, including placement frame transforms.

    Binary layout (from ACE DatLoader/FileTypes/Setup.cs):
      uint32  setup_id
      uint32  flags
        0x1 = HasParent       -> uint32[nparts] parent indices
        0x2 = HasDefaultScale -> Vector3[nparts] per-part scale
      uint32  num_parts
      uint32[num_parts]  gfxobj_ids
      [if HasParent]        uint32[nparts]
      [if HasDefaultScale]  float[nparts*3]
      uint32  num_cylspheres  + CylSphere[n] (5 floats each = 20 bytes)
      uint32  num_spheres     + Sphere[n]    (4 floats each = 16 bytes)
      float   height, radius, step_down_height, step_up_height
      Sphere  sorting_sphere  (16 bytes)
      Sphere  selection_sphere (16 bytes)
      uint32  num_lights      + Light[n] (skipped, variable size — use try/except)
      uint32  default_anim    (DID)
      uint32  default_script  (DID)
      float   default_scale
      uint32  num_placementtypes
      for each placement type:
        uint32  placement_id
        uint32  num_animframes
        for each animframe:
          Frame[num_parts]   (28 bytes each: vec3 origin + quat)
    """
    import math
    try:
        off = 0
        setup_id, off = _u32(data, off)
        flags,    off = _u32(data, off)

        HAS_PARENT        = 0x1
        HAS_DEFAULT_SCALE = 0x2

        nparts, off = _u32(data, off)
        parts = []
        for _ in range(nparts):
            gid, off = _u32(data, off)
            parts.append(SetupPart(gid))

        if flags & HAS_PARENT:
            for _ in range(nparts):
                _, off = _u32(data, off)

        if flags & HAS_DEFAULT_SCALE:
            off += 4   # DefaultScale is one float for whole setup, NOT per-part

        import logging as _log
        _logger = _log.getLogger(__name__)

        def _rd_u32(label):
            nonlocal off
            v = struct.unpack_from("<I", data, off)[0]
            _logger.warning(f"  [{off:4d}] {label} = {v} (0x{v:08X})")
            off += 4
            return v

        def _rd_f32(label):
            nonlocal off
            v = struct.unpack_from("<f", data, off)[0]
            _logger.warning(f"  [{off:4d}] {label} = {v:.6f}")
            off += 4
            return v

        def _skip(n, label):
            nonlocal off
            _logger.warning(f"  [{off:4d}] skip {n} bytes ({label})")
            off += n

        _logger.warning(f"parse_setup trace: id=0x{setup_id:08X} flags=0x{flags:08X} nparts={nparts} off={off} buflen={len(data)}")

        # Array counts use PackedDWORD (variable length), not u32
        def _rd_packed(label):
            nonlocal off
            v, off = _packed_dword(data, off)
            _logger.warning(f"  [{off:4d}] {label} = {v} (PackedDWORD)")
            return v

        ncyl = _rd_packed("num_cylspheres")
        if ncyl > 64: raise RuntimeError(f"Bad CylSphere count: {ncyl}")
        _skip(ncyl * 20, f"{ncyl} CylSpheres")

        nsph = _rd_packed("num_spheres")
        if nsph > 64: raise RuntimeError(f"Bad Sphere count: {nsph}")
        _skip(nsph * 16, f"{nsph} Spheres")

        _rd_f32("height")
        _rd_f32("radius")
        _rd_f32("step_down_height")
        _rd_f32("step_up_height")

        _skip(16, "sorting_sphere")
        _skip(16, "selection_sphere")

        nlights = _rd_packed("num_lights")
        if nlights > 64: raise RuntimeError(f"Bad Light count: {nlights}")
        _skip(nlights * 44, f"{nlights} Lights")

        # Dump next 32 bytes raw to see what's actually here
        _logger.warning(f"  [{off:4d}] next 32 raw bytes: {data[off:off+32].hex()}")

        # Scan for valid placement type count by trying different byte offsets
        # Valid: n_ptypes in 1-10, placement_id in 0-7, n_aframes in 1-10
        frames: List[PartFrame] = [PartFrame(0,0,0, 1,0,0,0)] * nparts
        n_ptypes = None
        scan_start = off
        for skip in [0, 4, 8, 12, 16, 20]:
            toff = scan_start + skip
            if toff + 20 > len(data): break
            try:
                tc, t1 = _packed_dword(data, toff)
                if not (1 <= tc <= 10): continue
                pid, t2 = _packed_dword(data, t1)
                if not (0 <= pid <= 7): continue
                naf, t3 = _packed_dword(data, t2)
                if not (1 <= naf <= 10): continue
                # Check that enough bytes remain for the frame data
                needed = naf * nparts * 28
                if t3 + needed > len(data) + 28: continue  # allow slight overrun
                _logger.warning(f"  SCAN: skip={skip} → n_ptypes={tc} pid={pid} naf={naf} (start={toff})")
                off = toff
                n_ptypes = tc
                break
            except Exception as se:
                _logger.warning(f"  SCAN skip={skip} failed: {se}")

        if n_ptypes is None:
            raise RuntimeError(f"Cannot find valid placement frames near offset {scan_start}")

        default_scale = 1.0
        for pt_i in range(n_ptypes):
            placement_id, off = _packed_dword(data, off)
            n_aframes, off    = _packed_dword(data, off)
            _logger.warning(f"  [{off:4d}] placement_id={placement_id} n_aframes={n_aframes}")
            for af_i in range(n_aframes):
                part_frames = []
                for _ in range(nparts):
                    pf, off = _parse_frame(data, off)
                    part_frames.append(pf)
                # Use the first placement type, first animframe as default rest pose
                if pt_i == 0 and af_i == 0:
                    frames = part_frames

        return AcSetup(setup_id, parts, default_scale, frames)
    except Exception as e:
        # Fall back to no-transform if parse fails
        import logging
        logging.getLogger(__name__).warning(f"parse_setup placement frames failed: {e}")
        return AcSetup(setup_id, parts, 1.0,
                       [PartFrame(0,0,0, 1,0,0,0)] * len(parts))


# ── GLB builder (minimal but valid GLTF 2.0 binary) ──────────────────────────

def _pack_glb(json_str: str, bin_data: bytes) -> bytes:
    """Pack a GLTF JSON chunk + BIN chunk into a GLB container."""
    # Pad JSON to 4-byte boundary with spaces
    json_bytes = json_str.encode("utf-8")
    json_pad   = (4 - len(json_bytes) % 4) % 4
    json_bytes += b" " * json_pad

    # Pad BIN to 4-byte boundary with zeros
    bin_pad  = (4 - len(bin_data) % 4) % 4
    bin_data = bin_data + b"\x00" * bin_pad

    json_chunk_len = len(json_bytes)
    bin_chunk_len  = len(bin_data)

    total = 12 + (8 + json_chunk_len) + (8 + bin_chunk_len)

    out = io.BytesIO()
    out.write(b"glTF")                              # magic
    out.write(struct.pack("<II", 2, total))          # version=2, total_length
    out.write(struct.pack("<I", json_chunk_len))
    out.write(b"JSON")
    out.write(json_bytes)
    out.write(struct.pack("<I", bin_chunk_len))
    out.write(b"BIN\x00")
    out.write(bin_data)
    return out.getvalue()


def export_setup_glb(db: DatDatabase, setup_id: int,
                     max_textures: int = 8) -> Optional[bytes]:
    """
    Read a Setup + its GfxObjs + textures from the DAT and return GLB bytes.
    Returns None if the setup is not found or has no renderable geometry.
    """
    raw = db.read_file(setup_id)
    if not raw:
        return None

    setup = parse_setup(raw)
    if not setup or not setup.parts:
        return None

    # ── Collect geometry ──────────────────────────────────────────────────────
    meshes        = []      # list of (vertices, indices, tex_index)
    texture_ids   = []      # ordered list of surface_texture IDs to embed
    tex_id_map    = {}      # surface_texture_id → index in texture_ids

    def get_tex_index(surf_id: int) -> int:
        st_id = parse_surface_texture(db, surf_id)
        if st_id is None:
            return -1
        if st_id not in tex_id_map:
            if len(texture_ids) >= max_textures:
                return -1
            tex_id_map[st_id] = len(texture_ids)
            texture_ids.append(st_id)
        return tex_id_map[st_id]

    import math

    def quat_rotate(q, v):
        """Rotate vector v by quaternion q (qw,qx,qy,qz)."""
        qw, qx, qy, qz = q
        # v' = q * (0,v) * q_conj
        tx = 2.0 * (qy * v[2] - qz * v[1])
        ty = 2.0 * (qz * v[0] - qx * v[2])
        tz = 2.0 * (qx * v[1] - qy * v[0])
        return (
            v[0] + qw * tx + qy * tz - qz * ty,
            v[1] + qw * ty + qz * tx - qx * tz,
            v[2] + qw * tz + qx * ty - qy * tx,
        )

    for part_idx, part in enumerate(setup.parts):
        raw_g = db.read_file(part.gfxobj_id)
        if not raw_g:
            continue
        gfx = parse_gfxobj(raw_g)
        if not gfx or not gfx.polygons:
            continue

        # Get this part's placement transform (rest pose)
        if part_idx < len(setup.frames):
            pf = setup.frames[part_idx]
            has_transform = not (pf.ox == 0 and pf.oy == 0 and pf.oz == 0
                                 and abs(pf.qw - 1.0) < 1e-5)
        else:
            has_transform = False

        # Triangulate polygons with transform applied
        for poly in gfx.polygons:
            if len(poly.vertex_ids) < 3:
                continue

            tex_idx = -1
            if 0 <= poly.surface_idx < len(gfx.surfaces):
                surf_id = gfx.surfaces[poly.surface_idx]
                surf_data = db.read_file(surf_id)
                if surf_data and len(surf_data) >= 12:
                    st_id_raw, _ = _u32(surf_data, 8)
                    tex_idx = get_tex_index(st_id_raw)

            verts = []
            for i, vid in enumerate(poly.vertex_ids):
                v = gfx.vertices.get(vid)
                if v is None:
                    continue
                _uvi = poly.uv_indices[i] if (poly.uv_indices and i < len(poly.uv_indices)) else 0
                uv = v.uvs[_uvi] if (v.uvs and _uvi < len(v.uvs)) else (0.0, 0.0)

                # Apply placement frame transform: rotate then translate
                if has_transform:
                    q = (pf.qw, pf.qx, pf.qy, pf.qz)
                    pos = quat_rotate(q, v.pos)
                    pos = (pos[0] + pf.ox, pos[1] + pf.oy, pos[2] + pf.oz)
                    nrm = quat_rotate(q, v.nrm)
                else:
                    pos, nrm = v.pos, v.nrm

                verts.append((pos, nrm, uv))

            # Fan triangulation
            indices = []
            for i in range(1, len(verts) - 1):
                indices += [0, i, i + 1]

            if verts and indices:
                meshes.append((verts, indices, tex_idx))

    if not meshes:
        import logging
        logging.getLogger(__name__).warning(
            f"export_setup_glb: no renderable meshes for setup 0x{setup_id:08X} "
            f"({len(setup.parts)} parts checked)"
        )
        return None

    # ── Build GLTF binary buffer ──────────────────────────────────────────────
    bin_buf  = io.BytesIO()
    bufviews = []
    accessors = []

    def add_accessor(data_bytes: bytes, count: int, dtype: str,
                     component_type: int, acc_type: str,
                     min_vals=None, max_vals=None) -> int:
        bv_offset = bin_buf.tell()
        bin_buf.write(data_bytes)
        bv_idx = len(bufviews)
        bufviews.append({
            "buffer": 0,
            "byteOffset": bv_offset,
            "byteLength": len(data_bytes),
        })
        acc = {
            "bufferView":    bv_idx,
            "byteOffset":    0,
            "componentType": component_type,
            "count":         count,
            "type":          acc_type,
        }
        if min_vals is not None: acc["min"] = min_vals
        if max_vals is not None: acc["max"] = max_vals
        accessors.append(acc)
        return len(accessors) - 1

    # ── Embed textures as PNG chunks ──────────────────────────────────────────
    images_json    = []
    materials_json = []
    samplers_json  = [{"magFilter": 9728, "minFilter": 9728,
                       "wrapS": 10497, "wrapT": 10497}]
    textures_json  = []

    for st_id in texture_ids:
        tex_id_hi = parse_surface_texture(db, st_id) or st_id
        tex_obj   = parse_texture(db, tex_id_hi)
        rgba      = None
        w = h = 4

        if tex_obj:
            w, h = tex_obj.width, tex_obj.height
            pal = None
            if tex_obj.palette_id:
                pal = parse_palette(db, tex_obj.palette_id)
            try:
                rgba = tex_obj.to_rgba(pal)
            except Exception:
                pass

        if not rgba:
            rgba = bytes([180, 180, 180, 255] * (w * h))
            w = h = 1

        png_bytes = _rgba_to_png(rgba, w, h)

        img_bv_off = bin_buf.tell()
        bin_buf.write(png_bytes)
        bv_idx = len(bufviews)
        bufviews.append({
            "buffer": 0,
            "byteOffset": img_bv_off,
            "byteLength": len(png_bytes),
        })
        img_idx = len(images_json)
        images_json.append({"bufferView": bv_idx, "mimeType": "image/png"})
        tex_idx_gltf = len(textures_json)
        textures_json.append({"sampler": 0, "source": img_idx})
        mat_idx = len(materials_json)
        materials_json.append({
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": tex_idx_gltf},
                "metallicFactor":   0.0,
                "roughnessFactor":  0.8,
            },
            "doubleSided": True,
        })
        # Remap tex_id_map values to material indices (same ordering)

    # Default untextured material
    default_mat_idx = len(materials_json)
    materials_json.append({
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.7, 0.7, 0.7, 1.0],
            "metallicFactor":  0.0,
            "roughnessFactor": 0.8,
        },
        "doubleSided": True,
    })

    # ── Build mesh primitives ─────────────────────────────────────────────────
    primitives = []
    FLOAT = 5126   # GL_FLOAT
    UINT16 = 5123  # GL_UNSIGNED_SHORT
    UINT32 = 5125  # GL_UNSIGNED_INT

    for verts, indices, tex_idx in meshes:
        if not verts:
            continue

        pos_data = b"".join(struct.pack("<3f", *v[0]) for v in verts)
        nrm_data = b"".join(struct.pack("<3f", *v[1]) for v in verts)
        uv_data  = b"".join(struct.pack("<2f", *v[2]) for v in verts)

        use_u32 = len(verts) > 65535
        idx_fmt  = "<I" if use_u32 else "<H"
        idx_data = b"".join(struct.pack(idx_fmt, i) for i in indices)

        positions = [(v[0][0], v[0][1], v[0][2]) for v in verts]
        min_p = [min(p[i] for p in positions) for i in range(3)]
        max_p = [max(p[i] for p in positions) for i in range(3)]

        pos_acc = add_accessor(pos_data, len(verts), "VEC3", FLOAT, "VEC3",
                               min_p, max_p)
        nrm_acc = add_accessor(nrm_data, len(verts), "VEC3", FLOAT, "VEC3")
        uv_acc  = add_accessor(uv_data,  len(verts), "VEC2", FLOAT, "VEC2")
        idx_acc = add_accessor(idx_data, len(indices), "SCALAR",
                               UINT32 if use_u32 else UINT16, "SCALAR")

        mat_idx = tex_idx if 0 <= tex_idx < len(materials_json) - 1 else default_mat_idx

        primitives.append({
            "attributes": {
                "POSITION": pos_acc,
                "NORMAL":   nrm_acc,
                "TEXCOORD_0": uv_acc,
            },
            "indices":  idx_acc,
            "material": mat_idx,
            "mode":     4,   # TRIANGLES
        })

    if not primitives:
        return None

    bin_bytes = bin_buf.getvalue()

    gltf = {
        "asset": {"version": "2.0", "generator": "ACEForge DatLoader"},
        "scene":  0,
        "scenes": [{"nodes": [0]}],
        "nodes":  [{"mesh": 0, "name": f"Setup_0x{setup_id:08X}"}],
        "meshes": [{"name": f"0x{setup_id:08X}", "primitives": primitives}],
        "materials":  materials_json,
        "textures":   textures_json,
        "images":     images_json,
        "samplers":   samplers_json,
        "accessors":  accessors,
        "bufferViews": bufviews,
        "buffers": [{"byteLength": len(bin_bytes)}],
    }

    return _pack_glb(json.dumps(gltf, separators=(",", ":")), bin_bytes)


# ── Minimal PNG encoder (no external deps) ───────────────────────────────────

def _rgba_to_png(rgba: bytes, w: int, h: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    raw = b""
    for y in range(h):
        raw += b"\x00" + rgba[y*w*4:(y+1)*w*4]

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6))
            + chunk(b"IEND", b""))


# ── Cache helpers (used by app_api.py) ───────────────────────────────────────

# Increment this when parse logic changes — forces cache invalidation
_PARSER_VERSION = "v10"

def get_cache_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    d = Path(appdata) / "ACEForge" / "model_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cached_glb_path(setup_id: int) -> Path:
    # Version in filename forces re-parse when parser changes
    return get_cache_dir() / f"{setup_id:08X}_{_PARSER_VERSION}.glb"


def get_or_export_glb(db: DatDatabase, setup_id: int) -> Optional[Path]:
    """Return path to cached GLB, exporting from DAT if needed."""
    p = cached_glb_path(setup_id)
    if p.exists():
        return p
    glb = export_setup_glb(db, setup_id)
    if glb is None:
        return None
    p.write_bytes(glb)
    return p
