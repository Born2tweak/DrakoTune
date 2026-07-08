"""AudioAsset and DiagnosticResult: the input file and its measurements.

AudioAsset describes a stored recording (private by default). DiagnosticResult
groups the observations produced for one asset by a specific analyzer version,
along with integrity flags (e.g. clipping) that gate downstream processing.
"""

from dataclasses import dataclass, field

from src.shared_types.observation import Observation
from src.shared_types.versions import ANALYZER_VERSION


@dataclass(frozen=True)
class AudioAsset:
    """A stored recording. Originals are private; paths are storage references."""

    id: str
    owner_id: str
    original_storage_path: str
    sample_rate: int
    channels: int
    duration: float
    processed_storage_path: str | None = None
    created_at: str = ""  # ISO-8601 timestamp

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "original_storage_path": self.original_storage_path,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration": self.duration,
            "processed_storage_path": self.processed_storage_path,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AudioAsset":
        return cls(
            id=d["id"],
            owner_id=d["owner_id"],
            original_storage_path=d["original_storage_path"],
            sample_rate=int(d["sample_rate"]),
            channels=int(d["channels"]),
            duration=float(d["duration"]),
            processed_storage_path=d.get("processed_storage_path"),
            created_at=d.get("created_at", ""),
        )


@dataclass(frozen=True)
class DiagnosticResult:
    """All observations produced for one asset by one analyzer version."""

    id: str
    audio_asset_id: str
    analyzer_version: str = ANALYZER_VERSION
    measurement_context: dict = field(default_factory=dict)
    observations: tuple[Observation, ...] = ()
    integrity_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "audio_asset_id": self.audio_asset_id,
            "analyzer_version": self.analyzer_version,
            "measurement_context": dict(self.measurement_context),
            "observations": [o.to_dict() for o in self.observations],
            "integrity_flags": list(self.integrity_flags),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DiagnosticResult":
        return cls(
            id=d["id"],
            audio_asset_id=d["audio_asset_id"],
            analyzer_version=d.get("analyzer_version", ANALYZER_VERSION),
            measurement_context=dict(d.get("measurement_context", {})),
            observations=tuple(Observation.from_dict(o) for o in d.get("observations", [])),
            integrity_flags=tuple(d.get("integrity_flags", ())),
        )
