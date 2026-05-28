"""
ACEForge Weenie Model
In-memory data model for a single weenie being built in manual mode.
All tables are stored as lists of dicts matching the SQL column structure.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WeenieModel:
    # weenie table
    class_id: int = 0
    class_name: str = ""
    weenie_type: int = 10  # Creature by default

    # Property tables — each row is a dict with column values
    int_props:    list[dict] = field(default_factory=list)
    bool_props:   list[dict] = field(default_factory=list)
    float_props:  list[dict] = field(default_factory=list)
    string_props: list[dict] = field(default_factory=list)
    did_props:    list[dict] = field(default_factory=list)
    int64_props:  list[dict] = field(default_factory=list)

    attributes:   list[dict] = field(default_factory=list)
    attribute2nd: list[dict] = field(default_factory=list)
    skills:       list[dict] = field(default_factory=list)
    body_parts:   list[dict] = field(default_factory=list)
    spell_book:   list[dict] = field(default_factory=list)

    # Emotes: list of {category, probability, weenie_class_id, style, substyle,
    #                  quest, vendor_type, min_health, max_health, actions: [...]}
    emotes:       list[dict] = field(default_factory=list)

    # Create list rows
    create_list:  list[dict] = field(default_factory=list)

    # Generator rows
    generator:    list[dict] = field(default_factory=list)

    # Event filter event IDs
    event_filters: list[int] = field(default_factory=list)

    def get_name(self) -> str:
        """Pull the Name string prop if set."""
        for p in self.string_props:
            if p.get("type") == 1:
                return p.get("value", self.class_name or "Unnamed")
        return self.class_name or "Unnamed"

    def add_int(self, type_id: int, value: int):
        self._remove_prop(self.int_props, type_id)
        self.int_props.append({"type": type_id, "value": value})

    def add_bool(self, type_id: int, value: bool):
        self._remove_prop(self.bool_props, type_id)
        self.bool_props.append({"type": type_id, "value": value})

    def add_float(self, type_id: int, value: float):
        self._remove_prop(self.float_props, type_id)
        self.float_props.append({"type": type_id, "value": value})

    def add_string(self, type_id: int, value: str):
        self._remove_prop(self.string_props, type_id)
        self.string_props.append({"type": type_id, "value": value})

    def add_did(self, type_id: int, value: str):
        self._remove_prop(self.did_props, type_id)
        self.did_props.append({"type": type_id, "value": value})

    def _remove_prop(self, table: list, type_id: int):
        for i, row in enumerate(table):
            if row.get("type") == type_id:
                table.pop(i)
                return

    def get_int(self, type_id: int, default=None):
        for p in self.int_props:
            if p["type"] == type_id:
                return p["value"]
        return default

    def get_bool(self, type_id: int, default=None):
        for p in self.bool_props:
            if p["type"] == type_id:
                return p["value"]
        return default

    def get_float(self, type_id: int, default=None):
        for p in self.float_props:
            if p["type"] == type_id:
                return p["value"]
        return default

    def get_string(self, type_id: int, default=""):
        for p in self.string_props:
            if p["type"] == type_id:
                return p["value"]
        return default

    def get_did(self, type_id: int, default=""):
        for p in self.did_props:
            if p["type"] == type_id:
                return p["value"]
        return default

    def to_dict(self) -> dict:
        """Serialize to plain dict for JSON storage."""
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "weenie_type": self.weenie_type,
            "int_props": self.int_props,
            "bool_props": self.bool_props,
            "float_props": self.float_props,
            "string_props": self.string_props,
            "did_props": self.did_props,
            "int64_props": self.int64_props,
            "attributes": self.attributes,
            "attribute2nd": self.attribute2nd,
            "skills": self.skills,
            "body_parts": self.body_parts,
            "spell_book": self.spell_book,
            "emotes": self.emotes,
            "create_list": self.create_list,
            "generator": self.generator,
            "event_filters": self.event_filters,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WeenieModel":
        m = cls()
        for key, val in d.items():
            if hasattr(m, key):
                setattr(m, key, val)
        return m
