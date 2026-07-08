"""Report: the user- and agent-facing explanation of a processing run.

Reports explain findings, applied actions, skipped actions, and limitations in
calm, non-marketing language. The report engine (M11) renders these; this type
defines the structured payload behind any rendering.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    """Structured explanation of what was found, done, skipped, and left uncertain."""

    id: str
    summary: str = ""
    findings: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    export_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "summary": self.summary,
            "findings": list(self.findings),
            "actions": list(self.actions),
            "limitations": list(self.limitations),
            "export_path": self.export_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Report":
        return cls(
            id=d["id"],
            summary=d.get("summary", ""),
            findings=tuple(d.get("findings", ())),
            actions=tuple(d.get("actions", ())),
            limitations=tuple(d.get("limitations", ())),
            export_path=d.get("export_path"),
        )
