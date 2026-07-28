"""Human-language macros over a mode graph (DT-97).

The point of this layer is that nobody should need the words "multiband band 3"
to change how their vocal sounds. A macro is a single control in ordinary
language that adjusts whichever processors actually govern that impression.

Contract, deliberately narrow:

  * 50 means "leave the mode alone". A macro at its centre is exactly the
    authored chain, so the modes stay the reference point.
  * A macro only ever adjusts processors the chain ALREADY contains. It never
    adds a capability. If a mode has no send, turning Space up does nothing —
    and `applied_to` reports that honestly rather than pretending.
  * Every adjustment goes through the registry's clamp on render, so a macro
    cannot push a processor outside its safe range.

That last point matters: these are controls over an authored chain, not a search.
Nothing here optimises against a distance objective, so none of the Q-016
gaming concerns apply.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.dsp_engine.graph import GraphNode, Parallel, Processor, Send, Serial

MACRO_NAMES = ("repair", "smoothness", "body", "clarity", "presence", "space")
CENTRE = 50.0


@dataclass
class MacroApplication:
    """What a macro set actually changed, for the inspector to report."""

    changed: list[str] = field(default_factory=list)
    inert: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"changed": list(self.changed), "inert": list(self.inert)}


def _scale(value: float) -> float:
    """Map a 0..100 macro to -1..+1 around the centre."""
    return (float(value) - CENTRE) / CENTRE


# Each macro lists (processor, parameter, units-of-change-at-full-deflection).
# Units are in the parameter's own scale; the registry clamps the result.
_MACRO_TARGETS: dict[str, tuple[tuple[str, str, float], ...]] = {
    "repair": (
        ("NoiseGate", "threshold_db", 8.0),
        ("HumNotch", "gain_db", -4.0),
        ("ResonanceSuppressor", "max_reduction_db", 4.0),
    ),
    "smoothness": (
        ("DeEsser", "max_reduction_db", 3.0),
        ("DynamicEQ", "max_reduction_db", 3.0),
        ("LowpassFilter", "cutoff_frequency_hz", -4000.0),
    ),
    "body": (
        ("LowShelfFilter", "gain_db", 3.0),
        ("HighpassFilter", "cutoff_frequency_hz", -25.0),
    ),
    "clarity": (
        ("PeakFilter", "gain_db", 2.0),
        ("HighShelfFilter", "gain_db", 2.5),
    ),
    "presence": (
        ("Compressor", "threshold_db", -5.0),
        ("VocalRider", "max_boost_db", 3.0),
        ("Saturation", "mix", 0.2),
    ),
    "space": (
        ("__send__", "level", 0.12),
        ("Reverb", "room_size", 0.15),
    ),
}


def _adjust_processor(node: Processor, macros: dict[str, float],
                      report: MacroApplication) -> None:
    for macro, targets in _MACRO_TARGETS.items():
        amount = _scale(macros.get(macro, CENTRE))
        if amount == 0.0:
            continue
        for proc, param, span in targets:
            if proc != node.processor or param not in node.parameters:
                continue
            node.parameters[param] = node.parameters[param] + amount * span
            label = f"{macro}->{proc}.{param}"
            if label not in report.changed:
                report.changed.append(label)


def _apply(node: GraphNode, macros: dict[str, float],
           report: MacroApplication) -> GraphNode:
    if isinstance(node, Processor):
        clone = Processor(node.processor, dict(node.parameters), node.objective_id)
        _adjust_processor(clone, macros, report)
        return clone

    if isinstance(node, Serial):
        return Serial([_apply(n, macros, report) for n in node.nodes])

    if isinstance(node, Parallel):
        return Parallel(branch=_apply(node.branch, macros, report),
                        blend=node.blend, label=node.label)

    if isinstance(node, Send):
        space = _scale(macros.get("space", CENTRE))
        level = node.level
        if space != 0.0:
            level = max(0.0, min(1.0, level + space * 0.12))
            label = f"space->{node.label}.level"
            if label not in report.changed:
                report.changed.append(label)
        return Send(branch=_apply(node.branch, macros, report),
                    level=level, duck=node.duck, label=node.label)

    return node


def apply_macros(
    graph: GraphNode, macros: dict[str, float] | None
) -> tuple[GraphNode, MacroApplication]:
    """Return a macro-adjusted copy of `graph` plus a report of what changed.

    The input graph is never mutated: a revision must be reproducible from the
    mode name plus the macro values, which requires the authored chain to stay
    intact.
    """
    report = MacroApplication()
    if not macros:
        return graph, report

    cleaned = {
        k: float(v) for k, v in macros.items()
        if k in MACRO_NAMES and isinstance(v, (int, float))
    }
    if not cleaned:
        return graph, report

    adjusted = _apply(graph, cleaned, report)

    for name, value in cleaned.items():
        if value == CENTRE:
            continue
        if not any(entry.startswith(f"{name}->") for entry in report.changed):
            # Honest reporting: this mode has nothing for that macro to move.
            report.inert.append(name)

    return adjusted, report


def parse_macros(raw: str | None) -> dict[str, float]:
    """Parse the client's macro payload, ignoring anything unrecognised."""
    if not raw:
        return {}
    import json

    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in data.items():
        if key in MACRO_NAMES and isinstance(value, (int, float)):
            out[key] = max(0.0, min(100.0, float(value)))
    return out
