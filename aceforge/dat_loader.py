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
    AC compressed UInt32 (ReadCompressedUInt32 in ACE BinaryReaderExtensions).
      high bit of b0 clear         -> value = b0                       (1 byte)
      bit7 set, bit6 clear         -> ((b0 & 0x7F) << 8) | b1          (2 bytes, big-endian)
      bit7 & bit6 set              -> (((b0 & 0x3F) << 8 | b1) << 16) | u16le(b2,b3)  (4 bytes)
    """
    b0 = data[off]
    if (b0 & 0x80) == 0:
        return b0, off + 1
    b1 = data[off + 1]
    if (b0 & 0x40) == 0:
        return (((b0 & 0x7F) << 8) | b1), off + 2
    s = struct.unpack_from("<H", data, off + 2)[0]   # trailing uint16 is little-endian
    return (((((b0 & 0x3F) << 8) | b1) << 16) | s), off + 4


# ── Texture parsing ───────────────────────────────────────────────────────────

# SurfacePixelFormat values (canonical ACE SurfacePixelFormat enum — decimal).
# The DXT ids are FourCC codes ('DXT1'/'DXT5'), not small ints.
PFID_R8G8B8         = 20
PFID_A8R8G8B8       = 21
PFID_A8B8G8R8       = 32
PFID_P8             = 41    # indexed, 8-bit (most common AC texture format)
PFID_INDEX16        = 101   # indexed, 16-bit
PFID_CUSTOM_R8G8B8A8 = 240
PFID_CUSTOM_A8B8G8R8 = 241
PFID_CUSTOM_B8G8R8   = 242
PFID_DXT1           = 827611204
PFID_DXT5           = 894720068
PFID_RAW_JPEG       = 500

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

        if self.fmt in (PFID_A8R8G8B8, PFID_CUSTOM_A8B8G8R8):
            # Stored little-endian; A8R8G8B8 bytes are B,G,R,A. ABGR bytes are R,G,B,A.
            out = bytearray(w * h * 4)
            abgr = self.fmt == PFID_CUSTOM_A8B8G8R8
            for i in range(w * h):
                c0, c1, c2, a = self.data[i*4], self.data[i*4+1], self.data[i*4+2], self.data[i*4+3]
                if abgr: r, g, b = c0, c1, c2
                else:    b, g, r = c0, c1, c2
                out[i*4:i*4+4] = (r, g, b, a)
            return bytes(out)

        if self.fmt == PFID_A8B8G8R8:
            # ABGR8888 little-endian bytes = R,G,B,A
            out = bytearray(w * h * 4)
            for i in range(w * h):
                r, g, b, a = self.data[i*4], self.data[i*4+1], self.data[i*4+2], self.data[i*4+3]
                out[i*4:i*4+4] = (r, g, b, a)
            return bytes(out)

        if self.fmt == PFID_CUSTOM_R8G8B8A8:
            return bytes(self.data[:w*h*4])

        if self.fmt in (PFID_R8G8B8, PFID_CUSTOM_B8G8R8):
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
    """Parse a SurfaceTexture (0x05xxxxxx) and return its first (highest-res)
    Texture (0x06) id. Layout: Id(u32) Unknown(i32) UnknownByte(u8)
    Textures[List<uint>: Int32 count + count×u32]."""
    data = db.read_file(st_id)
    if not data:
        return None
    try:
        off = 4      # Id
        off += 4     # Unknown (int32)
        off += 1     # UnknownByte
        count, off = _i32(data, off)
        if count <= 0:
            return None
        tex_id, _ = _u32(data, off)   # mip 0 = highest resolution
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

        HAS_PHYSICS = 0x1   # GfxObjFlags.HasPhysics
        HAS_DRAWING = 0x2   # GfxObjFlags.HasDrawing
        HAS_DEGRADE = 0x8   # GfxObjFlags.HasDIDDegrade (0x4 is Unknown)

        _checkpoints = [f"s:fl={flags:#x}b={len(data)}"]

        # Surfaces: List<uint>.UnpackSmartArray -> compressed-uint32 count, then u32 ids
        nsurfaces, off = _packed_dword(data, off)
        if nsurfaces > 256:
            raise RuntimeError(f"Bad surface count {nsurfaces} at {off}")
        surfaces = []
        for _ in range(nsurfaces):
            sid, off = _u32(data, off)
            surfaces.append(sid)
        _checkpoints.append(f"surfs({nsurfaces})@{off}")

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
            nphy, off = _packed_dword(data, off)   # SmartArray = compressed uint32
            for _ in range(nphy):
                _pidx, off = _u16(data, off)
                _pdata, off = _parse_polygon_flat(data, off)
            off = _skip_bsp_tree(data, off, 'Physics')
            _checkpoints.append(f"physBSP@{off}")

        # SortCenter
        _sort_center, off = _vec3(data, off)
        _checkpoints.append(f"sc@{off}")

        # Drawing polygons — everything the renderer needs. The DrawingBSP tree
        # and the optional DIDDegrade ref follow in the file, but they're only
        # used for spatial queries / LOD, so we stop here instead of walking the
        # BSP (unneeded, and its variable structure only risks misalignment).
        polygons: List[AcPolygon] = []
        if flags & HAS_DRAWING:
            ndraw, off = _packed_dword(data, off)   # SmartArray = compressed uint32
            if ndraw > 65535:
                raise RuntimeError(f"Bad draw poly count {ndraw} at {off}")
            for _pi in range(ndraw):
                _didx, off = _u16(data, off)   # dictionary key
                poly, off  = _parse_polygon_flat(data, off)
                polygons.append(poly)
            _checkpoints.append(f"drwpoly({ndraw})@{off}")

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
    Parse a Setup (0x02xxxxxx) into its parts + per-part rest-pose placement
    frames. Byte layout follows ACE DatLoader SetupModel.Unpack exactly:

      u32  setup_id
      u32  flags               (0x1 HasParent, 0x2 HasDefaultScale)
      u32  num_parts
      u32[num_parts]           GfxObj ids (Parts)
      [HasParent]       u32[num_parts]
      [HasDefaultScale] Vector3[num_parts]        (3 floats each = 12B)
      HoldingLocations  Dictionary<int,LocationType>: i32 count,
                        each = key(i32) + PartId(i32) + Frame(28B) = 36B
      ConnectionPoints  same shape
      i32  placements_count
      for each placement:
        i32  key
        Frame[num_parts]       (28B each: vec3 origin + quat w,x,y,z)
        u32  num_hooks (+ variable AnimationHooks — empty for setup frames)

    Everything after the placements (cyl/spheres/height/lights/DIDs) is
    irrelevant to rendering and is intentionally not parsed. The Resting (101)
    placement's frames are used as the rest pose, falling back to the first
    placement's frames, then to identity.
    """
    setup_id = 0
    parts: List[SetupPart] = []
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
            off += nparts * 12   # DefaultScale = Vector3 (3 floats) per part

        # ── HoldingLocations + ConnectionPoints ──────────────────────────────
        # Both are Dictionary<int, LocationType>. Per ACE UnpackableExtensions,
        # the int-keyed dictionary uses an Int32 length, and each LocationType is
        # PartId(int32) + Frame(28 bytes). So each entry = key(4) + 4 + 28 = 36.
        for _dict_i in range(2):
            dcount, off = _i32(data, off)
            if not (0 <= dcount <= 4096):
                raise RuntimeError(f"Bad location-dict count {dcount} at off {off-4}")
            off += dcount * 36

        # ── PlacementFrames ──────────────────────────────────────────────────
        # SetupModel.Unpack reads an Int32 count, then for each placement:
        #   key(int32) + AnimationFrame{ Frame[nparts] (28B each) + numHooks(u32) + hooks }
        # We only need the rest-pose part frames; use Placement.Resting (101) when
        # present, else the first placement. Setup placement frames are hookless in
        # practice — a non-zero hook count means variable-length data we can't skip,
        # so we stop there having already captured a usable pose.
        RESTING = 101
        placements_count, off = _i32(data, off)
        if not (0 <= placements_count <= 1024):
            raise RuntimeError(f"Bad placements count {placements_count} at off {off-4}")

        first_frames = None
        resting_frames = None
        for _ in range(placements_count):
            key, off = _i32(data, off)
            part_frames = []
            for _ in range(nparts):
                pf, off = _parse_frame(data, off)
                part_frames.append(pf)
            num_hooks, off = _u32(data, off)
            if first_frames is None:
                first_frames = part_frames
            if key == RESTING:
                resting_frames = part_frames
            if num_hooks != 0:
                break

        frames = resting_frames or first_frames or ([PartFrame(0,0,0, 1,0,0,0)] * nparts)
        return AcSetup(setup_id, parts, 1.0, frames)
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
    meshes = []   # list of (vertices, indices, surface_id)  — surface_id is a 0x08 id or None

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

            mesh_surf_id = None
            if 0 <= poly.surface_idx < len(gfx.surfaces):
                mesh_surf_id = gfx.surfaces[poly.surface_idx]

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
                meshes.append((verts, indices, mesh_surf_id))

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

    # ── Materials: one per unique Surface (0x08) ──────────────────────────────
    # A Surface is either a solid ARGB color or an image (SurfaceTexture 0x05 →
    # Texture 0x06, optionally palettized). We build a glTF material per surface
    # on demand and cache it by surface id, so a whole model's worth of polygons
    # collapses to a few materials.
    images_json    = []
    materials_json = []
    samplers_json  = [{"magFilter": 9729, "minFilter": 9729,
                       "wrapS": 10497, "wrapT": 10497}]
    textures_json  = []
    _surf_mat_cache = {}   # surface_id -> material index
    ST_BASE1_SOLID   = 0x1
    ST_BASE1_IMAGE   = 0x2
    ST_BASE1_CLIPMAP = 0x4

    def _argb_to_factor(argb):
        a = (argb >> 24) & 0xFF; r = (argb >> 16) & 0xFF
        g = (argb >>  8) & 0xFF; b =  argb        & 0xFF
        if a == 0: a = 255   # AC solid colors commonly leave alpha 0 = opaque
        return [r/255.0, g/255.0, b/255.0, a/255.0]

    def _embed_texture(rgba, w, h):
        png = _rgba_to_png(rgba, w, h)
        off = bin_buf.tell(); bin_buf.write(png)
        bv = len(bufviews)
        bufviews.append({"buffer": 0, "byteOffset": off, "byteLength": len(png)})
        img = len(images_json); images_json.append({"bufferView": bv, "mimeType": "image/png"})
        t = len(textures_json); textures_json.append({"sampler": 0, "source": img})
        return t

    def material_for_surface(surface_id):
        if surface_id in _surf_mat_cache:
            return _surf_mat_cache[surface_id]
        mat = None
        surf = db.read_file(surface_id) if surface_id else None
        if surf and len(surf) >= 12:
            try:
                stype, _ = _u32(surf, 4)   # Surface: [Id][Type][...]
                if stype & (ST_BASE1_IMAGE | ST_BASE1_CLIPMAP):
                    orig_tex_id, _ = _u32(surf, 8)    # SurfaceTexture (0x05)
                    orig_pal_id, _ = _u32(surf, 12)   # Palette (0x04), may be 0
                    st_tex = parse_surface_texture(db, orig_tex_id)
                    tex_obj = parse_texture(db, st_tex) if st_tex else None
                    if tex_obj:
                        pid = orig_pal_id or tex_obj.palette_id
                        pal = parse_palette(db, pid) if pid else None
                        rgba = None
                        try: rgba = tex_obj.to_rgba(pal)
                        except Exception: rgba = None
                        if rgba:
                            tgltf = _embed_texture(rgba, tex_obj.width, tex_obj.height)
                            mat = {"pbrMetallicRoughness": {
                                       "baseColorTexture": {"index": tgltf},
                                       "metallicFactor": 0.0, "roughnessFactor": 0.9},
                                   "doubleSided": True}
                else:
                    color_value, _ = _u32(surf, 8)    # solid ARGB
                    mat = {"pbrMetallicRoughness": {
                               "baseColorFactor": _argb_to_factor(color_value),
                               "metallicFactor": 0.0, "roughnessFactor": 0.9},
                           "doubleSided": True}
            except Exception:
                mat = None
        if mat is None:
            mat = {"pbrMetallicRoughness": {
                       "baseColorFactor": [0.72, 0.72, 0.75, 1.0],
                       "metallicFactor": 0.0, "roughnessFactor": 0.9},
                   "doubleSided": True}
        idx = len(materials_json); materials_json.append(mat)
        _surf_mat_cache[surface_id] = idx
        return idx

    # Fallback material for polygons with no surface at all
    default_mat_idx = len(materials_json)
    materials_json.append({
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.72, 0.72, 0.75, 1.0],
            "metallicFactor":  0.0,
            "roughnessFactor": 0.9,
        },
        "doubleSided": True,
    })

    # ── Build mesh primitives ─────────────────────────────────────────────────
    primitives = []
    FLOAT = 5126   # GL_FLOAT
    UINT16 = 5123  # GL_UNSIGNED_SHORT
    UINT32 = 5125  # GL_UNSIGNED_INT

    for verts, indices, surf_id in meshes:
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

        mat_idx = material_for_surface(surf_id) if surf_id else default_mat_idx

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
_PARSER_VERSION = "v11"

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
