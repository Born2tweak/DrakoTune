"""Fail-closed anonymization gate for private-corpus artifacts (D-029).

Nothing derived from the private corpus may enter git except anonymized metrics.
This checks every COMMITTED artifact that discusses the corpus for identifying
tokens taken from the LOCAL manifest (artist/title words, video ids), and exits
non-zero if any appears.

Skipped (not failed) when the manifest is absent — CI has no access to it, so
this is a local pre-commit gate, not a CI gate.

Usage: python scripts/check_corpus_anonymization.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "restricted" / "private_corpus_manifest.json"

# Words that are ordinary audio/English vocabulary and carry no identity even
# though they also appear inside filenames.
GENERIC = set("""a an the and or of to in on for with without from by at is are was were be been
acapella acapellas vocal vocals studio official audio version raw wet dry mix mixed master
mastered file files only high low same stay all clean track song music youtube mp3 wav
prime his kid go me part live remix intro outro
well""".split())

# Committed artifacts that discuss the corpus and must stay anonymized.
GUARDED = (
    "reports/evaluations/paired-corpus/FINDINGS.md",
    "reports/evaluations/paired-corpus/gap_report_anonymized.json",
    "reports/evaluations/paired-corpus/oracle_report_anonymized.json",
    "reports/evaluations/paired-corpus/oracle_report_anonymized.md",
    "reports/evaluations/paired-corpus/search_report_admissible_anonymized.json",
    "AURELIAN/00_CONTROL/NEGATIVE_RESULTS.md",
    "AURELIAN/02_RESEARCH/DT77_IMPROVEMENT_BRIEF.md",
)


def identifying_tokens(records: list[dict]) -> set[str]:
    tokens: set[str] = set()
    for rec in records:
        vid = rec.get("youtube_id")
        # The registrar mis-parses some ids (see the known-defect note); only
        # treat id-shaped values as identifiers so a bad parse cannot generate
        # a generic word and produce a false failure.
        if isinstance(vid, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            tokens.add(vid.lower())
        for key in ("artist_hint", "title_hint", "pair_key_hint", "filename"):
            value = rec.get(key)
            if not isinstance(value, str):
                continue
            stem = re.sub(r"\.(mp3|wav|flac)$", "", value.strip(), flags=re.I)
            for word in re.findall(r"[A-Za-z0-9]{3,}", stem):
                low = word.lower()
                if low not in GENERIC and not low.isdigit():
                    tokens.add(low)
    return tokens


def main() -> int:
    if not MANIFEST.exists():
        print("no local manifest; anonymization gate skipped (nothing to compare against)")
        return 0
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    tokens = identifying_tokens(records)
    failures = []
    for rel in GUARDED:
        path = REPO / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        hits = sorted(t for t in tokens if re.search(rf"\b{re.escape(t)}\b", text))
        if hits:
            failures.append((rel, hits))
    if failures:
        print("ANONYMIZATION FAILURE — identifying tokens in committed artifacts:")
        for rel, hits in failures:
            print(f"  {rel}: {hits}")
        return 1
    print(f"anonymization OK: {len(tokens)} identifying tokens, "
          f"{len(GUARDED)} guarded artifacts, 0 leaks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
