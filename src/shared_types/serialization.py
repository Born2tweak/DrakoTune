"""Generic, JSON-safe serialization for canonical records.

`to_serializable` recursively converts dataclasses, enums, and tuples into
plain JSON-compatible structures. Deserialization is intentionally explicit:
each record type provides its own `from_dict`, because explicit reconstruction
is easier to read and safer than reflective magic (Bible: "Prefer explicitness
over magic").
"""

import dataclasses
from enum import Enum
from typing import Any


def to_serializable(obj: Any) -> Any:
    """Convert dataclasses/enums/tuples/lists/dicts into JSON-safe values."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_serializable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (list, tuple)):
        return [to_serializable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    return obj
