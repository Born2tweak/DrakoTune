"""Graded-severity diagnosis calibration on the evaluation corpus (M25).

Runs every diagnosis (spectral interpretations, safety clipping, advisory
module) over corpus clean clips and recipe-labeled degraded clips, and reports:

  - per (defect family, severity): recall of the expected issue(s)
  - per issue: false-positive rate on clean clips
  - full issue x family detection matrix (cross-triggering visibility)

Ground truth comes from the degradation recipes (fixtures/degradations.py),
so "recall" here means "detects the synthetic defect model" — real-vocal
validity still requires M24-style human data. Results are committed under
reports/evaluations/<corpus>/calibration/ (no audio).

    python scripts/calibrate_corpus.py [--corpus corpus-v1]
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.diagnostics.advisory import interpret_advisory, measure_advisory  # noqa: E402
from src.diagnostics.safety import measure_safety  # noqa: E402
from src.diagnostics.spectral import interpret_spectral, measure_spectral  # noqa: E402

CALIBRATION_VERSION = "2.0.0"  # v1 = synthetic-only harness (M17)
CLIPPING_RATIO_MIN = 0.001

# family -> set of issues that SHOULD fire (any one counts as recall hit).
EXPECTED = {
    "noise": {"noise_floor"},
    "hum": {"hum"},
    "clipping": {"clipping"},
    "reverb": {"reverb"},
    "harshness": {"harshness"},
    "sibilance": {"sibilance"},
    "proximity": {"muddiness", "rumble"},
    "low_level": {"recording_level_low"},
    "codec": set(),  # no detector claims codec artifacts; spurious hits recorded
    "plosive": set(),  # M32: observation-only (negative result); spurious hits recorded
}

ALL_ISSUES = sorted({i for s in EXPECTED.values() for i in s}
                    | {"recording_level_high"})


def detect_issues(path: Path) -> set[str]:
    audio, sr = sf.read(path, dtype="float32")
    sr = int(sr)
    issues: set[str] = set()
    spectral_obs, _ = measure_spectral(audio, sr)
    issues |= {i.issue for i in interpret_spectral(spectral_obs)}
    advisory_obs, _ = measure_advisory(audio, sr)
    issues |= {i.issue for i in interpret_advisory(advisory_obs)}
    for o in measure_safety(audio, sr)[0]:
        if o.metric == "clipping_ratio" and o.value > CLIPPING_RATIO_MIN:
            issues.add("clipping")
    return issues


def run(corpus_version: str) -> Path:
    corpus_root = REPO / "data" / "derived" / corpus_version
    manifest = json.loads((corpus_root / "corpus_manifest.json").read_text(encoding="utf-8"))

    # --- clean clips: false positives ---
    clean_hits: dict[str, int] = defaultdict(int)
    clean_n = 0
    for clip in manifest["clips"]:
        clean_n += 1
        for issue in detect_issues(corpus_root / "clean" / f"{clip['clip_id']}.wav"):
            clean_hits[issue] += 1

    # --- degraded clips: recall + cross-matrix ---
    recall: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])   # (family, sev) -> [hits, n]
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    family_counts: dict[str, int] = defaultdict(int)
    for clip in manifest["clips"]:
        for deg in clip["degradations"]:
            recipe = deg["recipe"]
            family, severity = recipe["family"], recipe["severity"]
            issues = detect_issues(corpus_root / deg["file"])
            family_counts[family] += 1
            key = (family, severity)
            recall[key][1] += 1
            if issues & EXPECTED[family]:
                recall[key][0] += 1
            for issue in issues:
                matrix[family][issue] += 1

    result = {
        "calibration_version": CALIBRATION_VERSION,
        "corpus_version": corpus_version,
        "clean_clip_count": clean_n,
        "false_positive_rates": {i: round(clean_hits[i] / clean_n, 3) for i in ALL_ISSUES},
        "recall": [{"family": f, "severity": s, "hits": h, "n": n,
                    "recall": round(h / n, 3) if n else None}
                   for (f, s), (h, n) in sorted(recall.items())],
        "detection_matrix": {f: dict(m) for f, m in sorted(matrix.items())},
        "family_counts": dict(family_counts),
        "note": ("Ground truth = synthetic degradation recipes; real-vocal validity "
                 "requires human evidence (M24). Advisory issues never control DSP."),
    }

    out_dir = REPO / "reports" / "evaluations" / corpus_version / "calibration"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (out_dir / f"{stamp}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [f"# Diagnosis calibration v{CALIBRATION_VERSION} — {corpus_version} ({stamp})", "",
             f"Clean clips: {clean_n}. False-positive rates (issue fired on clean):", ""]
    lines += [f"- `{i}`: {result['false_positive_rates'][i]:.1%}" for i in ALL_ISSUES
              if result["false_positive_rates"][i] > 0] or ["- none 🎉"]
    lines += ["", "| family | severity | recall | n |", "|---|---|--:|--:|"]
    for row in result["recall"]:
        lines.append(f"| {row['family']} | {row['severity']} | {row['recall']:.0%} | {row['n']} |")
    lines += ["", "## Cross-detection matrix (family -> issues fired, count)", ""]
    for family, hits in result["detection_matrix"].items():
        expected = ", ".join(sorted(EXPECTED[family])) or "(none expected)"
        lines.append(f"- **{family}** (expect {expected}, n={family_counts[family]}): "
                     + ", ".join(f"{k}×{v}" for k, v in sorted(hits.items())))
    lines += ["", result["note"]]
    (out_dir / f"{stamp}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / (stamp + '.md')}")
    return out_dir / f"{stamp}.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="corpus-v1")
    args = parser.parse_args()
    run(args.corpus)


if __name__ == "__main__":
    main()
