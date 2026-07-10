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

    def __init__(self, dat_path: str, _is_companion: bool = False):
        self.path       = dat_path
        self.block_size = 0
        self.entries:   Dict[int, DatEntry] = {}
        self._stream:   Optional[io.RawIOBase] = None
        self.highres:   Optional["DatDatabase"] = None
        self._open()
        # Auto-attach client_highres.dat from the same folder: it carries the
        # full-resolution versions of 0x06 textures (the portal copies of some
        # sprites — e.g. wisp glows — are tiny or entirely key-color).
        if not _is_companion:
            try:
                hr = Path(dat_path).parent / "client_highres.dat"
                if hr.exists():
                    self.highres = DatDatabase(str(hr), _is_companion=True)
            except Exception:
                self.highres = None

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
        # Textures (0x06): prefer the high-resolution copy when available
        if self.highres is not None and (object_id >> 24) == 0x06:
            hi = self.highres.read_file(object_id)
            if hi is not None:
                return hi
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
        if self.highres is not None:
            self.highres.close()
            self.highres = None

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

    def to_rgba(self, palette: Optional[List[int]] = None,
                colorkey: bool = False) -> bytes:
        """Convert any supported format to raw RGBA8 bytes.

        colorkey: for ClipMap surfaces — palette index 0 is the transparent
        key color (how AC renders sprite-style textures like wisp glows).
        """
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
                if colorkey and idx == 0:
                    out[i*4:i*4+4] = (0, 0, 0, 0)   # ClipMap key → transparent
                    continue
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
    """Parse a SurfaceTexture (0x05xxxxxx) and return the best Texture (0x06)
    id that actually exists in this dat. Layout: Id(u32) Unknown(i32)
    UnknownByte(u8) Textures[List<uint>: Int32 count + count×u32].

    Multi-entry lists put the highest-resolution mip first, but that copy often
    lives in client_highres.dat rather than client_portal.dat — so walk the
    list in order and take the first id our database can actually read.
    """
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
        first = None
        for _ in range(count):
            tex_id, off = _u32(data, off)
            if first is None:
                first = tex_id
            if db.read_file(tex_id) is not None:
                return tex_id
        return first
    except Exception:
        return None


def parse_clothing_base_effect(db: DatDatabase, clothing_id: int,
                               setup_id: int) -> Optional[Dict[int, Tuple[int, Dict[int, int]]]]:
    """Parse a ClothingTable (0x10xxxxxx) and return the base effect for one
    setup: {part_index: (replacement_gfxobj_id, {old_surface_tex: new_surface_tex})}.

    Layout (verified against client_portal.dat 0x10000618):
      Id(u32) numBaseEffects(u16) numSubPalEffects(u16)
      numBaseEffects × [ SetupId(u32) numObjEffects(u32)
                         numObjEffects × [ PartIndex(u32) ModelId(u32)
                            numTexEffects(u32) × [ OldTex(u32) NewTex(u32) ] ] ]
    SubPal effects (dye palettes) follow but are not needed for texture render.
    Returns None if the table or the setup's entry is missing.
    """
    data = db.read_file(clothing_id)
    if not data or len(data) < 8:
        return None
    try:
        nbe, _nsp = struct.unpack_from("<HH", data, 4)
        off = 8
        for _ in range(nbe):
            entry_setup, off = _u32(data, off)
            nobj, off = _u32(data, off)
            parts: Dict[int, Tuple[int, Dict[int, int]]] = {}
            for _ in range(nobj):
                pidx, off = _u32(data, off)
                model, off = _u32(data, off)
                ntex, off = _u32(data, off)
                tmap: Dict[int, int] = {}
                for _ in range(ntex):
                    old_t, off = _u32(data, off)
                    new_t, off = _u32(data, off)
                    tmap[old_t] = new_t
                parts[pidx] = (model, tmap)
            if entry_setup == setup_id:
                return parts
        return None
    except Exception:
        return None


def parse_motion_table_default(db: DatDatabase, mt_id: int) -> Optional[Tuple[int, int, int, float]]:
    """Parse a MotionTable (0x09xxxxxx) and return the default idle cycle's
    first AnimData as (anim_id, low_frame, high_frame, framerate).

    Layout (validated byte-exact against client_portal.dat 0x09000001):
      Id(u32) DefaultStyle(u32)
      numStyleDefaults(u32) × [style u32, motion u32]
      numCycles(u32) × [key u32, MotionData]
      numModifiers / numLinks follow (not needed).
    MotionData: numAnims(u8) bitfield(u8) flags(u8) pad(u8),
      numAnims × AnimData[id u32, low i32, high i32, framerate f32],
      then optional velocity vec3 (flags&1) and omega vec3 (flags&2).
    Cycle key = (style & 0xFFFF) << 16 | (motion & 0xFFFF).
    """
    data = db.read_file(mt_id)
    if not data or len(data) < 12:
        return None
    try:
        default_style, = struct.unpack_from("<I", data, 4)
        off = 8
        nsd, = struct.unpack_from("<I", data, off); off += 4
        style_defaults = {}
        for _ in range(nsd):
            k, v = struct.unpack_from("<II", data, off); off += 8
            style_defaults[k] = v
        ncyc, = struct.unpack_from("<I", data, off); off += 4
        cycles: Dict[int, list] = {}
        order = []
        for _ in range(ncyc):
            k, = struct.unpack_from("<I", data, off); off += 4
            na, _bf, fl, _pad = struct.unpack_from("<BBBB", data, off); off += 4
            anims = []
            for _ in range(na):
                aid, lo, hi = struct.unpack_from("<Iii", data, off)
                fr, = struct.unpack_from("<f", data, off + 12)
                off += 16
                anims.append((aid, lo, hi, fr))
            if fl & 1: off += 12
            if fl & 2: off += 12
            if anims and (anims[0][0] >> 24) == 0x03:
                cycles[k] = anims
                order.append(k)
        if not cycles:
            return None
        style16 = default_style & 0xFFFF
        motion = style_defaults.get(default_style, 0)
        anims = cycles.get((style16 << 16) | (motion & 0xFFFF))
        if not anims:
            # any cycle belonging to the default style, else the first cycle
            for k in order:
                if (k >> 16) == style16:
                    anims = cycles[k]; break
        if not anims:
            anims = cycles[order[0]]
        return anims[0]
    except Exception:
        return None


# AnimationHook payload sizes in dwords (after the 8-byte type+direction
# header). Unknown types abort the parse — better a static model than garbage.
_HOOK_DWORDS = {
    0x01: 1, 0x02: 1, 0x03: 7, 0x04: 0, 0x06: 1, 0x07: 4, 0x08: 3, 0x09: 4,
    0x0A: 3, 0x0B: 4, 0x0C: 2, 0x0D: 10, 0x0E: 1, 0x0F: 1, 0x10: 1, 0x11: 0,
    0x12: 1, 0x13: 2, 0x14: 3, 0x15: 4, 0x16: 3, 0x17: 2, 0x18: 3, 0x19: 1,
    0x1A: 10,
}


def parse_animation(db: DatDatabase, anim_id: int) -> Optional[list]:
    """Parse an Animation (0x03xxxxxx) into frames[f][p] = ((x,y,z),(qw,qx,qy,qz)).

    Layout: Id(u32) Flags(u32) NumParts(u32) NumFrames(u32),
    optional object-level PosFrames (Flags&1: NumFrames × 7 floats), then per
    frame: NumParts × [origin vec3 + quat wxyz] + numHooks(u32) + hooks.
    Returns None on any structural surprise (unknown hook type, bad counts).
    """
    data = db.read_file(anim_id)
    if not data or len(data) < 16:
        return None
    try:
        _aid, flags, nparts, nframes = struct.unpack_from("<IIII", data, 0)
        if not (0 < nparts <= 512 and 0 < nframes <= 4096):
            return None
        off = 16
        if flags & 1:
            off += 28 * nframes
        frames = []
        for _f in range(nframes):
            if off + 28 * nparts + 4 > len(data):
                return None
            parts = []
            for _p in range(nparts):
                x, y, z, qw, qx, qy, qz = struct.unpack_from("<7f", data, off)
                off += 28
                parts.append(((x, y, z), (qw, qx, qy, qz)))
            nh, = struct.unpack_from("<I", data, off); off += 4
            for _h in range(nh):
                ht, = struct.unpack_from("<I", data, off)
                nd = _HOOK_DWORDS.get(ht)
                if nd is None:
                    return None
                off += 8 + 4 * nd
            frames.append(parts)
        return frames
    except Exception:
        return None


def parse_clothing_subpals(db: DatDatabase, clothing_id: int,
                           palette_template: int) -> list:
    """Parse a ClothingTable's SubPalEffects for one palette template.
    Returns [(palette_or_paletteset_id, [(offset, num_colors), ...]), ...].

    Both dictionaries in a ClothingTable are PackedHashTables: u16 count +
    u16 buckets, then count × (key u32 + value). CloSubPalEffect = Icon u32 +
    List<CloSubPalette>; CloSubPalette = List<Range(offset u32, count u32)>
    then PaletteSet u32 (verified against 0x10000215 — Shadow).
    """
    data = db.read_file(clothing_id)
    if not data or len(data) < 8:
        return []
    try:
        nbe, _buckets = struct.unpack_from("<HH", data, 4)
        off = 8
        # Skip ClothingBaseEffects
        for _ in range(nbe):
            off += 4                                    # setup id
            nobj, = struct.unpack_from("<I", data, off); off += 4
            for _ in range(nobj):
                off += 8                                # part idx + model id
                ntex, = struct.unpack_from("<I", data, off); off += 4 + 8 * ntex
        nsp, _b2 = struct.unpack_from("<HH", data, off); off += 4
        for _ in range(nsp):
            key, = struct.unpack_from("<I", data, off); off += 4
            _icon, = struct.unpack_from("<I", data, off); off += 4
            nsub, = struct.unpack_from("<i", data, off); off += 4
            subs = []
            for _ in range(nsub):
                nr, = struct.unpack_from("<i", data, off); off += 4
                ranges = []
                for _ in range(nr):
                    o_, n_ = struct.unpack_from("<II", data, off); off += 8
                    ranges.append((o_, n_))
                palset, = struct.unpack_from("<I", data, off); off += 4
                subs.append((palset, ranges))
            if key == palette_template:
                return subs
        return []
    except Exception:
        return []


def resolve_palette_id(db: DatDatabase, pid: int, shade: float) -> int:
    """Resolve a PaletteSet (0x0F) to a concrete Palette (0x04) by shade."""
    if (pid >> 24) != 0x0F:
        return pid
    data = db.read_file(pid)
    if not data or len(data) < 8:
        return 0
    try:
        count, = struct.unpack_from("<I", data, 4)
        if count <= 0:
            return 0
        s = min(max(shade, 0.0), 0.9999)
        idx = min(int(s * count), count - 1)
        pal, = struct.unpack_from("<I", data, 8 + 4 * idx)
        return pal
    except Exception:
        return 0


# ── Particle system (PhysicsScript 0x33 / ParticleEmitterInfo 0x32) ──────────

def parse_physics_script(db: DatDatabase, script_id: int) -> list:
    """Parse a PhysicsScript (0x33xxxxxx) and return its CreateParticle hooks:
    [{"emitter_info": id, "part": idx, "offset": (x,y,z), "quat": (w,x,y,z)}].

    Layout: Id(u32) numHooks(u32), each hook: StartTime(double) then an
    AnimationHook — HookType(u32) Direction(i32) + type-specific payload.
    CreateParticle (0x0D / 0x1A): EmitterInfoId(u32) PartIndex(u32)
    Offset Frame (origin vec3 + quat wxyz, 7 floats) EmitterId(u32).
    """
    data = db.read_file(script_id)
    if not data or len(data) < 8:
        return []
    out = []
    try:
        nhooks, = struct.unpack_from("<I", data, 4)
        off = 8
        for _ in range(nhooks):
            off += 8   # StartTime double
            ht, = struct.unpack_from("<I", data, off)
            nd = _HOOK_DWORDS.get(ht)
            if nd is None:
                break   # unknown hook — keep what we have
            if ht in (0x0D, 0x1A):
                eid, pidx = struct.unpack_from("<II", data, off + 8)
                ox, oy, oz, qw, qx, qy, qz = struct.unpack_from("<7f", data, off + 16)
                out.append({"emitter_info": eid, "part": pidx,
                            "offset": (ox, oy, oz), "quat": (qw, qx, qy, qz)})
            off += 8 + 4 * nd
    except Exception:
        pass
    return out


def parse_particle_emitter_info(db: DatDatabase, eid: int) -> Optional[dict]:
    """Parse a ParticleEmitterInfo (0x32xxxxxx). Field order verified against
    ACE.DatLoader.FileTypes.ParticleEmitterInfo and byte-checked on
    client_portal.dat 0x320004D7 (176 bytes)."""
    d = db.read_file(eid)
    if not d or len(d) < 176:
        return None
    try:
        etype, ptype = struct.unpack_from("<ii", d, 8)
        gfx_id, hw_gfx = struct.unpack_from("<II", d, 16)
        birthrate, = struct.unpack_from("<d", d, 24)
        max_p, init_p, total_p = struct.unpack_from("<3i", d, 32)
        total_sec, = struct.unpack_from("<d", d, 44)
        lifespan, = struct.unpack_from("<d", d, 52)
        lifespan_rand, = struct.unpack_from("<d", d, 60)
        vals = struct.unpack_from("<27f", d, 68)
        offset_dir = vals[0:3]; min_off, max_off = vals[3], vals[4]
        a = vals[5:8]; min_a, max_a = vals[8], vals[9]
        b = vals[10:13]; min_b, max_b = vals[13], vals[14]
        c = vals[15:18]; min_c, max_c = vals[18], vals[19]
        (start_scale, final_scale, scale_rand,
         start_trans, final_trans, trans_rand) = vals[20:26]
        is_parent_local, = struct.unpack_from("<i", d, 172)
        return {
            "etype": etype, "ptype": ptype,
            "gfx": gfx_id, "hw_gfx": hw_gfx, "birthrate": birthrate,
            "max": max_p, "init": init_p, "total": total_p,
            "total_sec": total_sec, "lifespan": lifespan,
            "lifespan_rand": lifespan_rand,
            "offset_dir": offset_dir, "min_off": min_off, "max_off": max_off,
            "a": a, "min_a": min_a, "max_a": max_a,
            "b": b, "min_b": min_b, "max_b": max_b,
            "c": c, "min_c": min_c, "max_c": max_c,
            "start_scale": start_scale, "final_scale": final_scale,
            "scale_rand": scale_rand, "start_trans": start_trans,
            "final_trans": final_trans, "trans_rand": trans_rand,
            "parent_local": is_parent_local,
        }
    except Exception:
        return None


def particle_gfx_size(db: DatDatabase, gfx_id: int) -> float:
    """Half-extent of a particle GfxObj — AC's emitter StartScale/FinalScale
    multiply the particle model's own size, so the world size of a rendered
    particle is (gfxobj half-extent × scale)."""
    try:
        gfx = parse_gfxobj(db.read_file(gfx_id))
        if not gfx or not gfx.vertices:
            return 0.25
        xs = [v.pos[0] for v in gfx.vertices.values()]
        ys = [v.pos[1] for v in gfx.vertices.values()]
        zs = [v.pos[2] for v in gfx.vertices.values()]
        ext = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
        return max(0.01, ext * 0.5)
    except Exception:
        return 0.25


def particle_gfx_tint(db: DatDatabase, gfx_id: int) -> Tuple[float, float, float]:
    """Average visible color of a particle GfxObj's texture — used to tint the
    point-sprite stand-ins the viewer draws for this emitter."""
    default = (0.85, 0.9, 1.0)
    try:
        gfx = parse_gfxobj(db.read_file(gfx_id))
        if not gfx or not gfx.surfaces:
            return default
        surf = db.read_file(gfx.surfaces[0])
        if not surf or len(surf) < 12:
            return default
        stype, = struct.unpack_from("<I", surf, 0)
        if not (stype & 0x6):   # solid color surface
            cv, = struct.unpack_from("<I", surf, 4)
            return (((cv >> 16) & 0xFF) / 255.0, ((cv >> 8) & 0xFF) / 255.0,
                    (cv & 0xFF) / 255.0)
        tex_id, = struct.unpack_from("<I", surf, 4)
        st = parse_surface_texture(db, tex_id)
        t = parse_texture(db, st) if st else None
        if not t:
            return default
        pal = parse_palette(db, t.palette_id) if t.palette_id else None
        rgba = t.to_rgba(pal, colorkey=bool(stype & 0x4))
        rs = gs = bs = n = 0
        for i in range(0, len(rgba), 4):
            if rgba[i + 3] > 0 and (rgba[i] | rgba[i+1] | rgba[i+2]):
                rs += rgba[i]; gs += rgba[i+1]; bs += rgba[i+2]; n += 1
        if not n:
            return default
        return (rs / n / 255.0, gs / n / 255.0, bs / n / 255.0)
    except Exception:
        return default


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
                     max_textures: int = 8,
                     clothing_id: int = 0,
                     motion_id: int = 0,
                     palette_template: int = 0,
                     shade: float = 0.0) -> Optional[bytes]:
    """
    Read a Setup + its GfxObjs + textures from the DAT and return GLB bytes.
    Returns None if the setup is not found or has no renderable geometry.

    clothing_id: optional ClothingTable (0x10xxxxxx). Armor/clothing weenies
    point their Setup at the base body parts; the ClothingTable swaps each
    covered part's GfxObj for the armor version and overrides its textures.
    """
    raw = db.read_file(setup_id)
    if not raw:
        return None

    setup = parse_setup(raw)
    if not setup or not setup.parts:
        return None

    clo_parts = parse_clothing_base_effect(db, clothing_id, setup_id) if clothing_id else None

    # Palette dye: the ClothingTable's SubPalEffects for the weenie's
    # PaletteTemplate overwrite ranges of the texture palettes with colors from
    # a PaletteSet resolved by Shade. This is what turns the shared human body
    # models into Shadows (full 2048-color palette replacement) and drives all
    # armor dye colors.
    pal_overrides = []
    if clothing_id and palette_template:
        for palset, ranges in parse_clothing_subpals(db, clothing_id, palette_template):
            src_id = resolve_palette_id(db, palset, shade)
            src = parse_palette(db, src_id) if src_id else None
            if src and ranges:
                pal_overrides.append((src, ranges))

    # Ambient particle emitters come from the setup's DefaultScript (0x33) —
    # the last five dwords of a Setup are DefaultAnimation, DefaultScript,
    # DefaultMotionTable, DefaultSoundTable, DefaultScriptTable. Parsed early
    # so geometry collection can drop the invisible particle-anchor quads.
    emit_hooks = []
    try:
        if len(raw) >= 20:
            _da, _dscript, _dm, _ds, _dt = struct.unpack_from("<5I", raw, len(raw) - 20)
            if (_dscript >> 24) == 0x33:
                emit_hooks = parse_physics_script(db, _dscript)
    except Exception:
        emit_hooks = []

    # Memoized "is this surface entirely key-color?" check (ClipMap with every
    # pixel transparent = an invisible particle-anchor quad).
    _allkey_cache: Dict[int, bool] = {}
    def _surface_allkey(sid):
        if sid in _allkey_cache:
            return _allkey_cache[sid]
        res = False
        try:
            surf = db.read_file(sid)
            if surf and len(surf) >= 12:
                st_, = struct.unpack_from("<I", surf, 0)
                if st_ & 0x4:
                    tex_, = struct.unpack_from("<I", surf, 4)
                    stx = parse_surface_texture(db, tex_)
                    tx = parse_texture(db, stx) if stx else None
                    if tx:
                        pl = parse_palette(db, tx.palette_id) if tx.palette_id else None
                        res = not any(tx.to_rgba(pl, colorkey=True)[3::4])
        except Exception:
            res = False
        _allkey_cache[sid] = res
        return res

    # Default idle animation from the MotionTable (0x09), if provided. Frames
    # give every part a full transform per tick, replacing the placement frame.
    anim_frames = None
    anim_framerate = 30.0
    if motion_id:
        _md = parse_motion_table_default(db, motion_id)
        if _md:
            _aid, _lo, _hi, _fr = _md
            _frames = parse_animation(db, _aid)
            if _frames:
                lo = max(0, _lo)
                hi = _hi if 0 <= _hi < len(_frames) else len(_frames) - 1
                if lo >= len(_frames) or lo > hi:
                    lo, hi = 0, len(_frames) - 1
                anim_frames = _frames[lo:hi + 1]
                anim_framerate = _fr if _fr and _fr > 0 else 30.0
                if len(anim_frames) < 2:
                    anim_frames = None   # nothing to animate

    # ── Collect geometry ──────────────────────────────────────────────────────
    # Per-part: vertices stay in part-local space; the part's placement frame
    # becomes a glTF node transform so animation frames can drive it directly.
    # meshes: list of (part_idx, vertices, indices, surface_id, tex_map)
    meshes = []
    part_nodes = {}   # part_idx -> ((ox,oy,oz), (qw,qx,qy,qz)) rest pose

    # Pre-scan: parse every part's GfxObj once and classify particle-anchor
    # quads (1–2 polygon sprites whose surfaces are entirely key-color). When
    # the setup has real emitters AND other visible geometry, anchors are
    # dropped — the particles are the visual. All-anchor models (wisps) keep
    # their quads as glow stand-ins so something renders alongside particles.
    _parsed = {}
    _anchor = {}
    for part_idx, part in enumerate(setup.parts):
        gfx_id, tex_map = part.gfxobj_id, None
        if clo_parts and part_idx in clo_parts:
            gfx_id, tex_map = clo_parts[part_idx]
            gfx_id = gfx_id or part.gfxobj_id
        raw_g = db.read_file(gfx_id)
        gfx = parse_gfxobj(raw_g) if raw_g else None
        if not gfx or not gfx.polygons:
            continue
        _parsed[part_idx] = (gfx, tex_map)
        _anchor[part_idx] = (len(gfx.polygons) <= 2 and bool(gfx.surfaces)
                             and all(_surface_allkey(s) for s in set(gfx.surfaces)))
    # When emitters exist, anchors never render — the particles are the visual.
    # (Models that end up with zero meshes export as emitter-only GLBs.)
    _skip_anchors = bool(emit_hooks)

    for part_idx, part in enumerate(setup.parts):
        if part_idx not in _parsed:
            continue
        gfx, tex_map = _parsed[part_idx]

        # Billboard hint: a 1–2 polygon part is a sprite quad (wisp glow etc.)
        part_is_sprite = len(gfx.polygons) <= 2

        # Rest-pose placement transform → node TRS
        if part_idx < len(setup.frames):
            pf = setup.frames[part_idx]
            part_nodes[part_idx] = ((pf.ox, pf.oy, pf.oz),
                                    (pf.qw, pf.qx, pf.qy, pf.qz))
        else:
            part_nodes[part_idx] = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0))

        # Invisible particle-anchor quads: the particles are the visual —
        # rendering the anchor as a glow doubles the effect and looks wrong.
        if _skip_anchors and _anchor.get(part_idx):
            continue

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
                verts.append((v.pos, v.nrm, uv))

            # Fan triangulation
            indices = []
            for i in range(1, len(verts) - 1):
                indices += [0, i, i + 1]

            if verts and indices:
                meshes.append((part_idx, verts, indices, mesh_surf_id, tex_map,
                               part_is_sprite))

    if not meshes and not emit_hooks:
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

    def material_for_surface(surface_id, tex_map=None, sprite=False):
        # Cache key includes the clothing texture remap — the same base surface
        # can resolve to different armor textures on different parts — and the
        # sprite hint (billboard glow vs. tinted-solid for all-key ClipMaps).
        key = (surface_id, frozenset(tex_map.items()) if tex_map else None,
               sprite)
        if key in _surf_mat_cache:
            return _surf_mat_cache[key]
        mat = None
        surf = db.read_file(surface_id) if surface_id else None
        if surf and len(surf) >= 8:
            try:
                # Surface (0x08) files carry NO leading Id dword (unlike GfxObj/
                # Setup): layout is [Type][TexId|Color][PalId][...][Translucency],
                # confirmed against client_portal.dat (e.g. 0x0800120B =
                # 00000002 05002BC3 00000000 ...).
                stype, _ = _u32(surf, 0)
                if stype & (ST_BASE1_IMAGE | ST_BASE1_CLIPMAP):
                    orig_tex_id, _ = _u32(surf, 4)    # SurfaceTexture (0x05)
                    orig_pal_id, _ = _u32(surf, 8)    # Palette (0x04), may be 0
                    if tex_map:
                        orig_tex_id = tex_map.get(orig_tex_id, orig_tex_id)
                    st_tex = parse_surface_texture(db, orig_tex_id)
                    tex_obj = parse_texture(db, st_tex) if st_tex else None
                    if tex_obj:
                        pid = orig_pal_id or tex_obj.palette_id
                        pal = parse_palette(db, pid) if pid else None
                        if pal and pal_overrides:
                            pal = list(pal)
                            for _src, _ranges in pal_overrides:
                                for _o, _n in _ranges:
                                    for _k in range(_n):
                                        if _o + _k < len(pal) and _o + _k < len(_src):
                                            pal[_o + _k] = _src[_o + _k]
                        # ClipMap = sprite-style color-keyed transparency
                        # (palette index 0 → transparent), e.g. wisp glows.
                        is_clip = bool(stype & ST_BASE1_CLIPMAP)
                        rgba = None
                        try: rgba = tex_obj.to_rgba(pal, colorkey=is_clip)
                        except Exception: rgba = None
                        all_key = bool(rgba and is_clip and not any(rgba[3::4]))
                        if all_key:
                            # Fully key-color ClipMap: in-game these are drawn
                            # by particle emitters (wisps, Virindi shrouds…).
                            # Tint from the palette's average visible color.
                            tint = (200, 220, 255)
                            if pal:
                                cs = [c for c in pal[1:257] if (c & 0xFFFFFF)]
                                if cs:
                                    n_ = len(cs)
                                    tint = (sum((c >> 16) & 0xFF for c in cs)//n_,
                                            sum((c >> 8) & 0xFF for c in cs)//n_,
                                            sum(c & 0xFF for c in cs)//n_)
                            if sprite:
                                # Billboard quad (wisp glow): soft radial glow,
                                # additively blended in the viewer.
                                gw = 64
                                buf = bytearray(gw*gw*4)
                                for yy in range(gw):
                                    for xx in range(gw):
                                        dx = (xx - gw/2 + .5)/(gw/2)
                                        dy = (yy - gw/2 + .5)/(gw/2)
                                        a = max(0.0, 1.0 - (dx*dx + dy*dy)) ** 2
                                        o = (yy*gw + xx)*4
                                        buf[o:o+4] = (tint[0], tint[1], tint[2],
                                                      int(255*a))
                                tgltf = _embed_texture(bytes(buf), gw, gw)
                                mat = {"pbrMetallicRoughness": {
                                           "baseColorTexture": {"index": tgltf},
                                           "metallicFactor": 0.0,
                                           "roughnessFactor": 0.9},
                                       "doubleSided": True,
                                       "alphaMode": "BLEND"}
                            else:
                                # Larger geometry (Virindi robe): render as a
                                # normally-lit solid tinted from the palette —
                                # a stretched glow texture looks wrong here.
                                mat = {"pbrMetallicRoughness": {
                                           "baseColorFactor": [tint[0]/255.0,
                                                               tint[1]/255.0,
                                                               tint[2]/255.0, 1.0],
                                           "metallicFactor": 0.0,
                                           "roughnessFactor": 0.9},
                                       "doubleSided": True}
                        elif rgba:
                            tgltf = _embed_texture(rgba, tex_obj.width, tex_obj.height)
                            mat = {"pbrMetallicRoughness": {
                                       "baseColorTexture": {"index": tgltf},
                                       "metallicFactor": 0.0, "roughnessFactor": 0.9},
                                   "doubleSided": True}
                            if is_clip:
                                mat["alphaMode"] = "MASK"
                                mat["alphaCutoff"] = 0.5
                else:
                    color_value, _ = _u32(surf, 4)    # solid ARGB
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
        _surf_mat_cache[key] = idx
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

    # ── Build mesh primitives, grouped per setup part ────────────────────────
    # Each part becomes its own glTF node + mesh so animation frames can drive
    # part transforms. Static models render identically (node = placement frame).
    FLOAT = 5126   # GL_FLOAT
    UINT16 = 5123  # GL_UNSIGNED_SHORT
    UINT32 = 5125  # GL_UNSIGNED_INT

    part_prims: Dict[int, list] = {}   # part_idx -> [primitive, ...]

    for part_idx, verts, indices, surf_id, part_tex_map, part_sprite in meshes:
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

        mat_idx = material_for_surface(surf_id, part_tex_map, part_sprite) if surf_id else default_mat_idx

        part_prims.setdefault(part_idx, []).append({
            "attributes": {
                "POSITION": pos_acc,
                "NORMAL":   nrm_acc,
                "TEXCOORD_0": uv_acc,
            },
            "indices":  idx_acc,
            "material": mat_idx,
            "mode":     4,   # TRIANGLES
        })

    if not part_prims and not emit_hooks:
        return None

    # ── Nodes + meshes: one per part, TRS from the rest-pose placement frame ──
    meshes_json = []
    nodes_json  = []
    node_of_part = {}   # part_idx -> node index
    for part_idx in sorted(part_prims):
        (ox, oy, oz), (qw, qx, qy, qz) = part_nodes.get(
            part_idx, ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)))
        m_idx = len(meshes_json)
        meshes_json.append({"name": f"part{part_idx}",
                            "primitives": part_prims[part_idx]})
        node_of_part[part_idx] = len(nodes_json)
        nodes_json.append({
            "mesh": m_idx,
            "name": f"part{part_idx}",
            "translation": [ox, oy, oz],
            "rotation": [qx, qy, qz, qw],   # glTF quats are xyzw; AC is wxyz
        })

    # ── Animation: per-part translation + rotation channels ──────────────────
    animations_json = []
    if anim_frames:
        n_anim_parts = len(anim_frames[0])
        nframes = len(anim_frames)
        times = b"".join(struct.pack("<f", f / anim_framerate) for f in range(nframes))
        time_acc = add_accessor(times, nframes, "SCALAR", FLOAT, "SCALAR",
                                [0.0], [(nframes - 1) / anim_framerate])
        samplers, channels = [], []
        for part_idx, node_idx in node_of_part.items():
            if part_idx >= n_anim_parts:
                continue   # part not driven by this animation — stays at rest
            tdata = b"".join(struct.pack("<3f", *anim_frames[f][part_idx][0])
                             for f in range(nframes))
            # AC quats are (w,x,y,z); glTF wants (x,y,z,w)
            rdata = b"".join(struct.pack("<4f",
                                         anim_frames[f][part_idx][1][1],
                                         anim_frames[f][part_idx][1][2],
                                         anim_frames[f][part_idx][1][3],
                                         anim_frames[f][part_idx][1][0])
                             for f in range(nframes))
            t_acc = add_accessor(tdata, nframes, "VEC3", FLOAT, "VEC3")
            r_acc = add_accessor(rdata, nframes, "VEC4", FLOAT, "VEC4")
            for path, out_acc in (("translation", t_acc), ("rotation", r_acc)):
                channels.append({"sampler": len(samplers),
                                 "target": {"node": node_idx, "path": path}})
                samplers.append({"input": time_acc, "output": out_acc,
                                 "interpolation": "LINEAR"})
        if channels:
            animations_json.append({"name": "idle", "samplers": samplers,
                                    "channels": channels})

    # ── Particle emitters from the setup's DefaultScript (0x33) ──────────────
    extras_emitters = []
    try:
        if emit_hooks:
                def _qrot(q, v):
                    qw, qx, qy, qz = q
                    tx = 2.0 * (qy * v[2] - qz * v[1])
                    ty = 2.0 * (qz * v[0] - qx * v[2])
                    tz = 2.0 * (qx * v[1] - qy * v[0])
                    return (v[0] + qw*tx + qy*tz - qz*ty,
                            v[1] + qw*ty + qz*tx - qx*tz,
                            v[2] + qw*tz + qx*ty - qy*tx)
                for hook in emit_hooks:
                    info = parse_particle_emitter_info(db, hook["emitter_info"])
                    if not info:
                        continue
                    tint = particle_gfx_tint(db, info["gfx"])
                    node = node_of_part.get(hook["part"])
                    pos = hook["offset"]
                    if node is None:
                        # Anchor part has no rendered geometry (skipped anchor
                        # quad) — bake its rest placement frame into the offset.
                        pn = part_nodes.get(hook["part"])
                        if pn:
                            (ox, oy, oz), q = pn
                            rx, ry, rz = _qrot(q, pos)
                            pos = (rx + ox, ry + oy, rz + oz)
                    ent = {
                        "node": node,
                        "ptype": info["ptype"],
                        "pos": [round(v, 4) for v in pos],
                        "size": round(particle_gfx_size(db, info["gfx"]), 4),
                        "birthrate": round(info["birthrate"], 5),
                        "max": min(info["max"], 256),
                        "lifespan": round(info["lifespan"], 3),
                        "lifespanRand": round(info["lifespan_rand"], 3),
                        "offsetDir": [round(v, 4) for v in info["offset_dir"]],
                        "minOff": round(info["min_off"], 4),
                        "maxOff": round(info["max_off"], 4),
                        "a": [round(v, 4) for v in info["a"]],
                        "minA": round(info["min_a"], 4), "maxA": round(info["max_a"], 4),
                        "b": [round(v, 4) for v in info["b"]],
                        "minB": round(info["min_b"], 4), "maxB": round(info["max_b"], 4),
                        "c": [round(v, 4) for v in info["c"]],
                        "minC": round(info["min_c"], 4), "maxC": round(info["max_c"], 4),
                        "startScale": round(info["start_scale"], 4),
                        "finalScale": round(info["final_scale"], 4),
                        "scaleRand": round(info["scale_rand"], 4),
                        "startTrans": round(info["start_trans"], 4),
                        "finalTrans": round(info["final_trans"], 4),
                        "tint": [round(v, 3) for v in tint],
                    }
                    extras_emitters.append(ent)
    except Exception:
        pass

    bin_bytes = bin_buf.getvalue()

    gltf = {
        "asset": {"version": "2.0", "generator": "ACEForge DatLoader"},
        "scene":  0,
        "scenes": [{"nodes": list(range(len(nodes_json)))}],
        "nodes":  nodes_json,
        "meshes": meshes_json,
        "materials":  materials_json,
        "textures":   textures_json,
        "images":     images_json,
        "samplers":   samplers_json,
        "accessors":  accessors,
        "bufferViews": bufviews,
        "buffers": [{"byteLength": len(bin_bytes)}],
    }
    if animations_json:
        gltf["animations"] = animations_json
    if extras_emitters:
        gltf["extras"] = {"emitters": extras_emitters}
        # Bounds hint so emitter-only models (wisps) still frame correctly
        exs = [e["pos"][0] for e in extras_emitters]
        eys = [e["pos"][1] for e in extras_emitters]
        ezs = [e["pos"][2] for e in extras_emitters]
        reach = max(e["size"] * max(abs(e["startScale"]), abs(e["finalScale"]),
                                    0.5) + e["maxOff"]
                    for e in extras_emitters)
        gltf["extras"]["bounds"] = {
            "center": [round((min(exs)+max(exs))/2, 3),
                       round((min(eys)+max(eys))/2, 3),
                       round((min(ezs)+max(ezs))/2, 3)],
            "span": round(max(max(exs)-min(exs), max(eys)-min(eys),
                              max(ezs)-min(ezs), 0.1) + 2*reach, 3),
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
_PARSER_VERSION = "v18"

def get_cache_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    d = Path(appdata) / "ACEForge" / "model_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cached_glb_path(setup_id: int, clothing_id: int = 0,
                    motion_id: int = 0, palette_template: int = 0,
                    shade: float = 0.0) -> Path:
    # Version in filename forces re-parse when parser changes; clothing id
    # distinguishes the same body setup dressed in different armor, motion id
    # distinguishes animated vs static, and palette/shade distinguish dyes.
    clo = f"_C{clothing_id:08X}" if clothing_id else ""
    mot = f"_M{motion_id:08X}" if motion_id else ""
    dye = f"_P{palette_template}S{int(shade*1000)}" if palette_template else ""
    return get_cache_dir() / f"{setup_id:08X}{clo}{mot}{dye}_{_PARSER_VERSION}.glb"


def get_or_export_glb(db: DatDatabase, setup_id: int,
                      clothing_id: int = 0,
                      motion_id: int = 0,
                      palette_template: int = 0,
                      shade: float = 0.0) -> Optional[Path]:
    """Return path to cached GLB, exporting from DAT if needed."""
    p = cached_glb_path(setup_id, clothing_id, motion_id, palette_template, shade)
    if p.exists():
        return p
    glb = export_setup_glb(db, setup_id, clothing_id=clothing_id,
                           motion_id=motion_id,
                           palette_template=palette_template, shade=shade)
    if glb is None:
        return None
    p.write_bytes(glb)
    return p
