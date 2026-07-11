"""Analyze blinded listening-test responses (M24).

Joins listener response CSVs with the session key, screens listeners on catch
trials, and evaluates the pre-registered criteria from
docs/validation/DRAKOTUNE_ALPHA_VALIDATION_PLAN.md §6:

  1. per-family preference for processed >= 65% with binomial p < 0.05
  2. clean-input do-no-harm: processed preferred <= 55%
  3. artifact reports aggregated per family
  plus inter-rater agreement (pairwise percent agreement; simple by design).

    python scripts/listening_analyze.py <session_dir> <responses1.csv> [more.csv...]

Writes <session_dir>/analysis.md + analysis.json. Also appends every response
to the durable preference log (reports/evaluations/preference_log.jsonl schema
v1) — the seed of the future preference dataset (research map #16).
"""

import csv
import json
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ANALYSIS_VERSION = "1.0.0"
CATCH_FAIL_LIMIT = 0.34        # listener excluded if > 1/3 of catch trials answered A/B
PREFERENCE_THRESHOLD = 0.65
CLEAN_MAX_PREFERENCE = 0.55
ALPHA = 0.05


def _binom_p_geq(k: int, n: int, p: float = 0.5) -> float:
    """P(X >= k) for X ~ Binomial(n, p). Exact; n is small."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def load_session(session_dir: Path) -> dict:
    key = json.loads((session_dir / "session_key.json").read_text(encoding="utf-8"))
    return {t["trial"]: t for t in key["trials"] if "skipped" not in t}


def load_responses(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("trial") and row.get("preference(A/B/none)", "").strip():
                    rows.append({k.strip(): (v or "").strip() for k, v in row.items()})
    return rows


def analyze(session_dir: Path, response_paths: list[Path], log_path: Path | None = None) -> dict:
    trials = load_session(session_dir)
    responses = load_responses(response_paths)
    if not responses:
        raise SystemExit("no completed responses found")

    # --- listener screening on catch trials ---
    catch_fails: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # listener -> [fails, total]
    for r in responses:
        t = trials.get(r["trial"])
        if t and t["kind"] == "catch":
            catch_fails[r["listener_id"]][1] += 1
            if r["preference(A/B/none)"].upper() in ("A", "B"):
                catch_fails[r["listener_id"]][0] += 1
    excluded = {lid for lid, (f, n) in catch_fails.items() if n and f / n > CATCH_FAIL_LIMIT}
    kept = [r for r in responses if r["listener_id"] not in excluded]

    # --- per-family preference ---
    per_family: dict[str, list[bool]] = defaultdict(list)
    clean_votes: list[bool] = []
    artifacts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in kept:
        t = trials.get(r["trial"])
        if t is None:
            continue
        pref = r["preference(A/B/none)"].upper()
        for col, val in r.items():
            if col.startswith("artifact_") and val in ("1", "x", "X", "yes"):
                artifacts[t["family"]][col.removeprefix("artifact_")] += 1
        if t["kind"] == "defect" and pref in ("A", "B"):
            per_family[t["family"]].append(pref == t["processed_is"])
        elif t["kind"] == "clean":
            clean_votes.append(pref == t.get("processed_is"))

    family_results = []
    for family, votes in sorted(per_family.items()):
        wins, n = sum(votes), len(votes)
        rate = wins / n if n else float("nan")
        p = _binom_p_geq(wins, n) if n else 1.0
        family_results.append({
            "family": family, "n": n, "processed_preferred": wins,
            "rate": round(rate, 3), "binomial_p": round(p, 4),
            "passes": bool(n >= 8 and rate >= PREFERENCE_THRESHOLD and p < ALPHA),
            "note": None if n >= 8 else "n < 8: underpowered, no verdict",
        })

    clean_rate = (sum(clean_votes) / len(clean_votes)) if clean_votes else None
    do_no_harm = None if clean_rate is None else bool(clean_rate <= CLEAN_MAX_PREFERENCE)

    # --- inter-rater agreement: pairwise percent agreement on shared defect trials ---
    by_listener: dict[str, dict[str, str]] = defaultdict(dict)
    for r in kept:
        t = trials.get(r["trial"])
        if t and t["kind"] == "defect":
            by_listener[r["listener_id"]][r["trial"]] = r["preference(A/B/none)"].upper()
    agreements = []
    for l1, l2 in combinations(sorted(by_listener), 2):
        shared = set(by_listener[l1]) & set(by_listener[l2])
        if shared:
            agreements.append(sum(by_listener[l1][t] == by_listener[l2][t] for t in shared) / len(shared))
    agreement = round(float(sum(agreements) / len(agreements)), 3) if agreements else None

    result = {
        "analysis_version": ANALYSIS_VERSION,
        "session": session_dir.name,
        "listeners_total": len({r["listener_id"] for r in responses}),
        "listeners_excluded_by_catch": sorted(excluded),
        "responses_used": len(kept),
        "family_results": family_results,
        "clean_preference_rate": None if clean_rate is None else round(clean_rate, 3),
        "do_no_harm_pass": do_no_harm,
        "pairwise_agreement": agreement,
        "artifacts_by_family": {k: dict(v) for k, v in artifacts.items()},
        "criteria": {"preference_threshold": PREFERENCE_THRESHOLD, "alpha": ALPHA,
                     "clean_max_preference": CLEAN_MAX_PREFERENCE,
                     "source": "docs/validation/DRAKOTUNE_ALPHA_VALIDATION_PLAN.md §6"},
    }

    (session_dir / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [f"# Listening analysis — {session_dir.name}", "",
             f"Listeners: {result['listeners_total']} ({len(excluded)} excluded by catch trials); "
             f"responses used: {len(kept)}; pairwise agreement: {agreement}", "",
             "| family | n | preferred | rate | p | verdict |", "|---|--:|--:|--:|--:|---|"]
    for fr in family_results:
        verdict = "PASS" if fr["passes"] else (fr["note"] or "fail")
        lines.append(f"| {fr['family']} | {fr['n']} | {fr['processed_preferred']} "
                     f"| {fr['rate']} | {fr['binomial_p']} | {verdict} |")
    lines += ["", f"Clean-input do-no-harm: rate={result['clean_preference_rate']} "
                  f"-> {'PASS' if do_no_harm else 'FAIL' if do_no_harm is not None else 'n/a'}"]
    (session_dir / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Durable preference log (schema v1) — no PII, no audio.
    log = log_path or Path(__file__).resolve().parent.parent / "reports" / "evaluations" / "preference_log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as fh:
        for r in kept:
            t = trials.get(r["trial"])
            if t:
                fh.write(json.dumps({"schema": 1, "session": session_dir.name,
                                     "listener": r["listener_id"], "listener_type": r.get("listener_type"),
                                     "kind": t["kind"], "family": t["family"], "severity": t["severity"],
                                     "preference": r["preference(A/B/none)"].upper(),
                                     "processed_is": t.get("processed_is"),
                                     "strength": r.get("strength(1-5)")}) + "\n")
    return result


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: listening_analyze.py <session_dir> <responses.csv> [...]")
    analyze(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
    print("wrote analysis.md / analysis.json")


if __name__ == "__main__":
    main()
