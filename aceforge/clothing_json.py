"""
clothing_json.py — ClothingTable ↔ JSON for the CustomClothingBase ACE mod

Converts the canonical table dict produced by dat_loader.parse_clothing_table_full()
to and from the JSON that OptimShi's CustomClothingBase server mod consumes:

    https://github.com/OptimShi/CustomClothingBase

The mod merges these files into the ClothingTable at DAT-unpack time, so a
custom look ships as a server-side JSON file plus a weenie pointing at the
ClothingBase id (DID 7). Players download nothing.

Format rules, taken from the mod's own deserializer rather than its examples
(PatchClass.OnWorldOpen, HexConverter.cs, ClothingTableEx.cs):

  * A HexUintJsonConverter is registered on JsonSerializerOptions.Converters,
    which applies it to *every* uint property. So Index, ModelId, Old/NewTexture,
    Icon, PaletteSet, Offset and NumColors all accept a hex string ("0x1F"),
    a decimal string ("31"), or a bare number (31). We emit "0x%08X" — matching
    what the mod's own /clothingbase-export command writes.

  * Dictionary keys are asymmetric, and this is the sharp edge. A
    HexKeyDictionaryConverter is registered for Dictionary<uint,
    ClothingBaseEffect(Ex)> but NOT for Dictionary<uint, CloSubPalEffectEx>.
    ClothingBaseEffects keys therefore go through TryParseHex (hex or decimal),
    while ClothingSubPalEffects keys fall back to System.Text.Json's default
    numeric-key handling, which is DECIMAL ONLY. A hex key under
    ClothingSubPalEffects throws on the server. We read either and always
    write base-effect keys as hex, subpal keys as decimal.

  * The mod merges per key, replacing wholesale — a base effect for a setup, or
    a subpal effect for a template, is substituted entire, never deep-merged.
    A file therefore only needs the keys it actually changes.
"""

from __future__ import annotations

import json
from typing import Optional

# ClothingTable id range. The mod's stub path only fires inside this window
# (PatchClass.PreGetReaderForFile), so an id outside it can never be a new
# entry — it would silently do nothing on the server.
CLOTHING_ID_MIN = 0x10000001
CLOTHING_ID_MAX = 0x10FFFFFF


class ClothingJsonError(ValueError):
    """Raised when JSON cannot be read as a ClothingTable."""


def range_ok(clothing_id: int) -> bool:
    """Is this a ClothingBase id the mod will actually act on?"""
    return CLOTHING_ID_MIN <= clothing_id <= CLOTHING_ID_MAX


def _hex(v: int) -> str:
    return "0x%08X" % v


def _uint(v, field: str) -> int:
    """Read a value the way the mod's HexUintJsonConverter does: 0x-prefixed
    strings are hex, bare strings are decimal, numbers are decimal."""
    if isinstance(v, bool):
        raise ClothingJsonError(f"{field}: expected a number, got a boolean")
    if isinstance(v, int):
        n = v
    elif isinstance(v, str):
        s = v.strip()
        try:
            n = int(s[2:], 16) if s[:2].lower() == "0x" else int(s, 10)
        except ValueError:
            raise ClothingJsonError(f"{field}: {v!r} is not a number") from None
    else:
        raise ClothingJsonError(f"{field}: {v!r} is not a number")
    if not 0 <= n <= 0xFFFFFFFF:
        raise ClothingJsonError(f"{field}: {n} does not fit in a uint32")
    return n


def _listof(obj, key: str, field: str) -> list:
    v = obj.get(key, [])
    if v is None:
        return []
    if not isinstance(v, list):
        raise ClothingJsonError(f"{field}.{key}: expected a list")
    return v


def table_to_json(table: dict, indent: int = 2) -> str:
    """Canonical table dict → CustomClothingBase JSON text."""
    out = {}

    base = table.get("base_effects") or {}
    if base:
        out["ClothingBaseEffects"] = {
            _hex(setup): {
                "CloObjectEffects": [
                    {
                        "Index": _hex(o["index"]),
                        "ModelId": _hex(o["model_id"]),
                        "CloTextureEffects": [
                            {"OldTexture": _hex(t["old"]),
                             "NewTexture": _hex(t["new"])}
                            for t in o.get("tex_effects", [])
                        ],
                    }
                    for o in objs
                ]
            }
            for setup, objs in sorted(base.items())
        }

    subpal = table.get("subpal_effects") or {}
    if subpal:
        # Decimal keys — see the module docstring; hex here throws server-side.
        out["ClothingSubPalEffects"] = {
            str(template): {
                "Icon": _hex(eff.get("icon", 0)),
                "CloSubPalettes": [
                    {
                        "Ranges": [
                            {"Offset": _hex(r["offset"]),
                             "NumColors": _hex(r["num_colors"])}
                            for r in sp.get("ranges", [])
                        ],
                        "PaletteSet": _hex(sp["paletteset"]),
                    }
                    for sp in eff.get("subpals", [])
                ],
            }
            for template, eff in sorted(subpal.items())
        }

    out["Id"] = _hex(table["id"])
    return json.dumps(out, indent=indent)


def table_from_json(text: str) -> dict:
    """CustomClothingBase JSON text → canonical table dict."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ClothingJsonError(f"invalid JSON: {e}") from None
    return table_from_obj(obj)


def table_from_obj(obj) -> dict:
    """Already-decoded CustomClothingBase JSON → canonical table dict.

    Liberal on input: accepts hex or decimal, string or number, for every
    value and both key sets — matching what the mod tolerates. Taking a decoded
    object (not just text) lets the editor hand its live document straight over
    for preview without a serialize/parse round trip.
    """
    if not isinstance(obj, dict):
        raise ClothingJsonError("top level must be an object")

    # PropertyNameCaseInsensitive = true on the mod side.
    keys = {k.lower(): k for k in obj}

    def field(name):
        return obj.get(keys.get(name.lower(), name))

    if field("Id") is None:
        raise ClothingJsonError('missing required "Id"')
    table = {"id": _uint(field("Id"), "Id"),
             "base_effects": {}, "subpal_effects": {}}

    base = field("ClothingBaseEffects") or {}
    if not isinstance(base, dict):
        raise ClothingJsonError("ClothingBaseEffects: expected an object")
    for skey, entry in base.items():
        setup = _uint(skey, "ClothingBaseEffects key")
        if not isinstance(entry, dict):
            raise ClothingJsonError(f"ClothingBaseEffects[{skey}]: expected an object")
        objs = []
        for i, o in enumerate(_listof(entry, "CloObjectEffects",
                                     f"ClothingBaseEffects[{skey}]")):
            where = f"ClothingBaseEffects[{skey}].CloObjectEffects[{i}]"
            objs.append({
                "index": _uint(o.get("Index", 0), f"{where}.Index"),
                "model_id": _uint(o.get("ModelId", 0), f"{where}.ModelId"),
                "tex_effects": [
                    {"old": _uint(t.get("OldTexture", 0), f"{where}.OldTexture"),
                     "new": _uint(t.get("NewTexture", 0), f"{where}.NewTexture")}
                    for t in _listof(o, "CloTextureEffects", where)
                ],
            })
        table["base_effects"][setup] = objs

    subpal = field("ClothingSubPalEffects") or {}
    if not isinstance(subpal, dict):
        raise ClothingJsonError("ClothingSubPalEffects: expected an object")
    for tkey, entry in subpal.items():
        template = _uint(tkey, "ClothingSubPalEffects key")
        if not isinstance(entry, dict):
            raise ClothingJsonError(f"ClothingSubPalEffects[{tkey}]: expected an object")
        subs = []
        for i, sp in enumerate(_listof(entry, "CloSubPalettes",
                                       f"ClothingSubPalEffects[{tkey}]")):
            where = f"ClothingSubPalEffects[{tkey}].CloSubPalettes[{i}]"
            subs.append({
                "paletteset": _uint(sp.get("PaletteSet", 0), f"{where}.PaletteSet"),
                "ranges": [
                    {"offset": _uint(r.get("Offset", 0), f"{where}.Offset"),
                     "num_colors": _uint(r.get("NumColors", 0), f"{where}.NumColors")}
                    for r in _listof(sp, "Ranges", where)
                ],
            })
        table["subpal_effects"][template] = {
            "icon": _uint(entry.get("Icon", 0), f"ClothingSubPalEffects[{tkey}].Icon"),
            "subpals": subs,
        }

    return table


def validate_table(table: dict) -> list:
    """Problems that would bite on the server. Returns a list of strings;
    empty means clean. Advisory only — nothing here mutates the table."""
    problems = []

    cid = table.get("id", 0)
    if not CLOTHING_ID_MIN <= cid <= CLOTHING_ID_MAX:
        problems.append(
            f"Id {_hex(cid)} is outside the ClothingTable range "
            f"{_hex(CLOTHING_ID_MIN)}–{_hex(CLOTHING_ID_MAX)}; the mod will not "
            f"create a stub for it.")

    for setup, objs in (table.get("base_effects") or {}).items():
        if (setup >> 24) != 0x02:
            problems.append(f"base effect key {_hex(setup)} is not a Setup (0x02......)")
        for o in objs:
            if o["model_id"] and (o["model_id"] >> 24) != 0x01:
                problems.append(
                    f"{_hex(setup)} part {o['index']}: ModelId "
                    f"{_hex(o['model_id'])} is not a GfxObj (0x01......)")
            for t in o.get("tex_effects", []):
                for lbl, v in (("OldTexture", t["old"]), ("NewTexture", t["new"])):
                    if v and (v >> 24) != 0x05:
                        problems.append(
                            f"{_hex(setup)} part {o['index']}: {lbl} {_hex(v)} "
                            f"is not a SurfaceTexture (0x05......)")

    for template, eff in (table.get("subpal_effects") or {}).items():
        if not 0 <= template <= 0xFFFF:
            problems.append(f"subpal template key {template} is out of range")
        for sp in eff.get("subpals", []):
            ps = sp["paletteset"]
            # The mod patches PaletteSet.Unpack so a raw Palette works here too.
            if (ps >> 24) not in (0x04, 0x0F):
                problems.append(
                    f"template {template}: PaletteSet {_hex(ps)} is neither a "
                    f"PaletteSet (0x0F......) nor a Palette (0x04......)")
            for r in sp.get("ranges", []):
                if r["num_colors"] == 0:
                    problems.append(
                        f"template {template}: zero-length range at offset "
                        f"{r['offset']} has no effect")
                if r["offset"] % 8 or r["num_colors"] % 8:
                    problems.append(
                        f"template {template}: range offset={r['offset']} "
                        f"numColors={r['num_colors']} is not 8-aligned; AC "
                        f"palette subranges align to 8")

    return problems


def json_filename(clothing_id: int) -> str:
    """What the mod expects the file to be called (PatchClass.GetFilename)."""
    return "%X.json" % clothing_id
