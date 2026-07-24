"""DT-55A: register a private candidate corpus WITHOUT ingesting it.

Byte-level provenance bookkeeping only — sha256, size, filename-parsed metadata,
candidate pair grouping, and a fail-closed rights classification. NO audio is
decoded, processed, copied into the repo, or committed: the manifest is written to
data/restricted/ (gitignored). Processing stays blocked until the H1-D ruling
(control/CONSOLIDATED_HUMAN_DECISION_H1_STUDY.md); leaked or AI-isolated-wet
material is rejected permanently regardless of H1-D.

Usage: python scripts/register_private_corpus.py <folder> [--out data/restricted/private_corpus_manifest.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "data" / "restricted" / "private_corpus_manifest.json"

MANIFEST_VERSION = "1.0.0"

# Permanent rejections independent of any future H1-D approval.
LEAKED_PAT = re.compile(r"leak", re.IGNORECASE)
AI_ISOLATED_PAT = re.compile(r"ai\s*isolated|isolated\s*vocals", re.IGNORECASE)

RAW_PAT = re.compile(r"\braw\b|\bno\s*autotune\b", re.IGNORECASE)
WET_PAT = re.compile(r"studio|official|acapella\)|\bacapella\b|vocals\s*only|diy", re.IGNORECASE)
YT_ID_PAT = re.compile(r"\[([A-Za-z0-9_-]{6,})\]")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_name(name: str) -> dict:
    """Best-effort artist/title/role from the filename. Filenames are HINTS only:
    pairing must be re-verified by DT-55B signal evidence, never trusted."""
    stem = re.sub(r"^\d+\s*-\s*", "", Path(name).stem)
    yt = YT_ID_PAT.search(stem)
    stem_clean = YT_ID_PAT.sub("", stem).strip()
    artist, title = (stem_clean.split(" - ", 1) + [""])[:2] if " - " in stem_clean else ("", stem_clean)
    role = "raw" if RAW_PAT.search(name) else ("wet_candidate" if WET_PAT.search(name) else "unknown")
    # Normalize a pair key: title lowercased minus parentheticals + role tokens.
    base = re.sub(r"\(.*?\)", "", title).strip().lower()
    base = re.sub(r"\b(ft|feat)\.?\s.*$", "", base).strip()
    base = re.sub(r"\b(no\s*autotune|raw|studio|official|acapella|vocals\s*only|diy|perfect|leaked)\b", "", base)
    base = re.sub(r"\s+", " ", base).strip(" -–")
    return {
        "artist_hint": artist.strip(), "title_hint": title.strip(),
        "pair_key_hint": base, "role_hint": role,
        "youtube_id": yt.group(1) if yt else None,
    }


def classify(name: str) -> str:
    if LEAKED_PAT.search(name):
        return "rejected_leaked"
    if AI_ISOLATED_PAT.search(name):
        return "rejected_ai_isolated_wet"
    return "blocked_pending_H1D"


def build_manifest(folder: Path, approve_ref: str | None = None) -> dict:
    """approve_ref: a decision-log id (e.g. "D-029") recording the H1-D ruling.
    When given, non-rejected files become `approved_local_internal_eval` with that
    consent_ref. Rejected classes (leaked / AI-isolated) NEVER flip, regardless."""
    files = sorted(p for p in folder.iterdir() if p.is_file())
    records, seen_hash = [], {}
    for p in files:
        digest = sha256_of(p)
        rights = classify(p.name)
        if digest in seen_hash:
            rights = "duplicate"
        else:
            seen_hash[digest] = p.name
        consent = None
        if approve_ref and rights == "blocked_pending_H1D":
            rights = "approved_local_internal_eval"
            consent = approve_ref
        records.append({
            "filename": p.name, "bytes": p.stat().st_size, "sha256": digest,
            **parse_name(p.name),
            "rights_class": rights,
            "duplicate_of": seen_hash.get(digest) if rights == "duplicate" else None,
            # Fail-closed ingestion mirror: consent_ref stays null unless approved.
            "consent_ref": consent,
        })
    # Candidate pair grouping by pair_key_hint (verification is DT-55B's job).
    by_key: dict[str, list[str]] = {}
    for r in records:
        if r["rights_class"].startswith("rejected") or r["rights_class"] == "duplicate":
            continue
        by_key.setdefault(r["pair_key_hint"], []).append(r["filename"])
    pairs = {k: v for k, v in by_key.items() if len(v) >= 2}
    return {
        "manifest_version": MANIFEST_VERSION,
        "source_folder": str(folder),
        "rule": "Filenames are hints; pairing requires DT-55B signal verification. "
                "No processing before H1-D; rejected classes never process.",
        "n_files": len(records),
        "n_candidate_pair_groups": len(pairs),
        "candidate_pair_groups": pairs,
        "files": records,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--approve", default=None, metavar="DECISION_ID",
                    help="record the H1-D ruling (e.g. D-029): non-rejected files "
                         "become approved_local_internal_eval with this consent_ref")
    args = ap.parse_args()
    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"not a directory: {folder}")
        return 1
    out = Path(args.out)
    if REPO in out.resolve().parents and "restricted" not in out.parts and "local" not in out.parts:
        print("refusing: manifest must live under a gitignored path (data/restricted/)")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(folder, approve_ref=args.approve)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    counts: dict[str, int] = {}
    for r in manifest["files"]:
        counts[r["rights_class"]] = counts.get(r["rights_class"], 0) + 1
    print(json.dumps({"out": str(out), "n_files": manifest["n_files"],
                      "pair_groups": manifest["n_candidate_pair_groups"],
                      "rights_classes": counts}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
