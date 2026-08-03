"""Mode contracts: authored production chains (DT-95).

Before this, "modes" were two preset labels whose entire difference was one
gentle glue compressor — which is why changing them never sounded like anything.
A mode here is a full topology: which processors, in what order, in what routing,
with which parameter ranges, and how intensity changes the *shape* of the graph
rather than just scaling numbers.

Honest naming is enforced by contract (see MILESTONES/DT_93_106.md):

  * There is no denoising in the engine — only a gate. Rescue V1 says gate.
  * There is no dereverberation. Rescue V1 does not claim room removal; it does
    tonal room *reduction*, which is a different and weaker thing.
  * `Reverb` is a generic algorithmic room, never described as a plate.
  * `PitchShift` is transposition. No mode uses it as tuning, and no mode
    surfaces it as pitch correction.

Modes are authored, bounded and safety-checked. They do not depend on the
automated search objective (Q-016) being resolved, because nothing here is
selected by optimising a distance — a human chose these values and a human can
listen to the result.
"""

from src.modes.macros import MACRO_NAMES, apply_macros, parse_macros
from src.modes.contracts import (
    EXPERIMENTAL_MODES,
    INTENSITY_ORDER,
    Intensity,
    ModeSpec,
    build_graph,
    describe_mode,
    get_mode,
    is_experimental,
    list_modes,
    production_modes,
)

__all__ = [
    "MACRO_NAMES",
    "apply_macros",
    "parse_macros",
    "EXPERIMENTAL_MODES",
    "INTENSITY_ORDER",
    "Intensity",
    "ModeSpec",
    "build_graph",
    "describe_mode",
    "get_mode",
    "is_experimental",
    "list_modes",
    "production_modes",
]
