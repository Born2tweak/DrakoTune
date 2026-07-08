"""ProcessingRecord: the aggregate that ties one processing run together.

A ProcessingRecord bundles the asset, its diagnostics, the processing plan, the
evaluation, and the report under a single schema version. It is the "minimal
processing record" the pipeline emits today; later milestones fill in the
currently-empty sections (real plans in M09, evaluation in M10, report in M11).
"""

from dataclasses import dataclass

from src.shared_types.asset import AudioAsset, DiagnosticResult
from src.shared_types.decision import ProcessingPlan
from src.shared_types.evaluation import EvaluationResult
from src.shared_types.report import Report
from src.shared_types.versions import SCHEMA_VERSION


@dataclass(frozen=True)
class ProcessingRecord:
    """One processing run, versioned end to end."""

    id: str
    schema_version: str = SCHEMA_VERSION
    asset: AudioAsset | None = None
    diagnostics: DiagnosticResult | None = None
    plan: ProcessingPlan | None = None
    evaluation: EvaluationResult | None = None
    report: Report | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "asset": self.asset.to_dict() if self.asset else None,
            "diagnostics": self.diagnostics.to_dict() if self.diagnostics else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "report": self.report.to_dict() if self.report else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingRecord":
        return cls(
            id=d["id"],
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            asset=AudioAsset.from_dict(d["asset"]) if d.get("asset") else None,
            diagnostics=(
                DiagnosticResult.from_dict(d["diagnostics"]) if d.get("diagnostics") else None
            ),
            plan=ProcessingPlan.from_dict(d["plan"]) if d.get("plan") else None,
            evaluation=(
                EvaluationResult.from_dict(d["evaluation"]) if d.get("evaluation") else None
            ),
            report=Report.from_dict(d["report"]) if d.get("report") else None,
        )
