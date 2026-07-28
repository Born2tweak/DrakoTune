"""Graph execution: serial, parallel and send routing (DT-94).

The M09 executor runs a flat list of processors. That topology cannot express
the things that make a vocal sound produced rather than cleaned:

  * parallel compression - a crushed copy blended *under* the dry signal, which
    adds density without flattening the performance the way one hard serial
    compressor does;
  * effect sends - reverb/delay computed on a wet-only branch and mixed back, so
    the dry vocal stays untouched and the effect level is independently
    controllable;
  * ducking - the send level driven by the dry signal's envelope, so tails rise
    between phrases instead of washing over the words.

This module adds those topologies over the *same* bounded, clamped, plan-authored
processor contract in `processors.py`. Nodes do not decide anything; they realize
an authored graph.

Channel handling is explicit throughout (see `channels.py`): branches are
aligned to a common width and length before summing, so a widened or
tail-extending branch is never silently truncated.

The flat path is preserved exactly: a `Serial` of processor nodes produces the
same samples as `execute_plan`, pinned by tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from pedalboard import Pedalboard

from src.dsp_engine.channels import align_for_mix, normalize, to_mono
from src.dsp_engine.processors import PROCESSORS, clamp_params

# Ducking envelope resolution. 10 ms is short enough to follow syllables and long
# enough not to modulate at audio rate (which would be audible as distortion).
_ENVELOPE_MS = 10.0


class GraphNode:
    """A node transforms a canonical `(n_samples, n_channels)` float32 buffer."""

    def render(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


@dataclass
class Processor(GraphNode):
    """One registry processor with clamped parameters.

    Array processors (`spec.process`) are mono kernels; they are mapped over each
    channel independently rather than collapsing to channel 0. On mono input that
    is bit-identical to the old behavior; on stereo it stops silently discarding
    the right channel.
    """

    processor: str
    parameters: dict = field(default_factory=dict)
    objective_id: str | None = None

    def render(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        spec = PROCESSORS.get(self.processor)
        if spec is None:
            return normalize(audio)
        params, _ = clamp_params(self.processor, self.parameters)
        buf = normalize(audio)
        if spec.process is not None:
            out = [
                np.asarray(spec.process(buf[:, c], sample_rate, params), dtype=np.float32)
                for c in range(buf.shape[1])
            ]
            length = max(x.shape[0] for x in out)
            padded = [np.pad(x, (0, length - x.shape[0])) for x in out]
            return np.stack(padded, axis=1).astype(np.float32)
        board = Pedalboard([spec.factory(params)])
        return normalize(board(buf.T.astype(np.float32), sample_rate).T)

    def describe(self) -> str:
        return self.processor


@dataclass
class Serial(GraphNode):
    """Nodes in order, each fed the previous node's output."""

    nodes: list[GraphNode] = field(default_factory=list)

    def render(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        out = normalize(audio)
        for node in self.nodes:
            out = normalize(node.render(out, sample_rate))
        return out

    def describe(self) -> str:
        return " -> ".join(n.describe() for n in self.nodes) or "passthrough"


@dataclass
class Parallel(GraphNode):
    """Blend a processed branch under the dry signal.

    This is the parallel-compression topology. `blend` is the branch's share of
    the sum (0.0 = dry only, 1.0 = branch only); the dry keeps `1 - blend` so the
    result does not jump in level as the blend moves.
    """

    branch: GraphNode
    blend: float = 0.5
    label: str = "parallel"

    def render(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        dry = normalize(audio)
        wet = normalize(self.branch.render(dry, sample_rate))
        blend = float(np.clip(self.blend, 0.0, 1.0))
        dry_a, wet_a = align_for_mix(dry, wet)
        return (dry_a * (1.0 - blend) + wet_a * blend).astype(np.float32)

    def describe(self) -> str:
        return f"{self.label}[{self.branch.describe()} @ {self.blend:.2f}]"


@dataclass
class Send(GraphNode):
    """A wet-only effect branch mixed back under the dry signal.

    Unlike `Parallel`, the dry signal passes at full level and the wet branch is
    *added* at `level` - the standard send/return topology for reverb and delay,
    where the point is to place the vocal in a space without diluting it.

    When `duck` > 0 the wet level is reduced in proportion to the dry envelope,
    so the effect gets out of the way while words are happening and blooms in the
    gaps. `duck=1.0` fully suppresses the wet under peak dry signal.
    """

    branch: GraphNode
    level: float = 0.25
    duck: float = 0.0
    label: str = "send"

    def render(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        dry = normalize(audio)
        wet = normalize(self.branch.render(dry, sample_rate))
        level = float(np.clip(self.level, 0.0, 1.0))
        duck = float(np.clip(self.duck, 0.0, 1.0))

        dry_a, wet_a = align_for_mix(dry, wet)
        if duck > 0.0:
            gain = _ducking_gain(dry_a, sample_rate, duck)
            wet_a = wet_a * gain[:, None]
        return (dry_a + wet_a * level).astype(np.float32)

    def describe(self) -> str:
        duck = f", duck {self.duck:.2f}" if self.duck > 0 else ""
        return f"{self.label}[{self.branch.describe()} @ {self.level:.2f}{duck}]"


def _ducking_gain(dry: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    """Per-sample wet gain from the dry envelope: loud dry -> quiet wet.

    Smoothed with a one-pole follower in both directions so the gain never steps
    discontinuously (a step would be an audible click, not ducking).
    """
    env = np.abs(to_mono(dry)[:, 0]).astype(np.float32)
    if env.size == 0:
        return np.ones(0, dtype=np.float32)

    window = max(1, int(sample_rate * _ENVELOPE_MS / 1000.0))
    coeff = np.float32(np.exp(-1.0 / max(window, 1)))
    smoothed = np.empty_like(env)
    acc = np.float32(0.0)
    for i in range(env.size):  # one-pole attack/release follower
        acc = max(env[i], acc * coeff)
        smoothed[i] = acc

    peak = float(np.max(smoothed))
    if peak <= 0.0:
        return np.ones_like(smoothed)
    return (1.0 - amount * (smoothed / peak)).astype(np.float32)


def render_graph(
    audio: np.ndarray, sample_rate: int, node: GraphNode
) -> np.ndarray:
    """Render a graph, returning a canonical buffer. Applies no output safety.

    Output safety stays in the executor so every render path shares one ceiling.
    """
    return normalize(node.render(normalize(audio), sample_rate))
