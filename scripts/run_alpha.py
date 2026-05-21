"""DrakoTune Alpha 2.2 — CLI entry point.

Usage:
    python scripts/run_alpha.py path/to/raw_vocal.wav [--output-dir output/] [--generic]

Runs the full Alpha 2.2 pipeline:
1. FFmpeg preprocessing (normalize to 44100Hz, 16-bit, mono)
2. Vocal diagnosis (7 categories via Librosa)
3. Adaptive Pedalboard DSP chain (or --generic for Alpha 1 behavior)
4. Export before/after WAV files
"""

import argparse
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dsp.diagnose import diagnose, print_profile, scan_artifacts, print_artifacts
from src.dsp.export import export_before_after
from src.dsp.pipeline import process_audio
from src.dsp.preprocess import preprocess


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DrakoTune Alpha 2.2: light Alpha 2 refinement with targeted DSP."
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to raw vocal file (WAV, MP3, etc.)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory for before/after output files (default: output/)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="vocal",
        help="Base name for output files (default: vocal)",
    )
    parser.add_argument(
        "--generic",
        action="store_true",
        help="Use generic Alpha 1 chain instead of adaptive diagnosis-driven chain",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    print("DrakoTune Alpha 2.2 Pipeline")
    print("============================")
    print(f"Input: {input_path}")
    print()

    start_time = time.time()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: FFmpeg preprocessing
        print("[1/5] Preprocessing with FFmpeg...")
        normalized_path = Path(tmpdir) / "normalized.wav"
        preprocess(input_path, normalized_path)
        print("      Normalized to 44100Hz, 16-bit, mono")

        # Step 2: Diagnosis
        profile = None
        if not args.generic:
            print("[2/5] Diagnosing vocal problems...")
            diag_start = time.time()
            profile = diagnose(str(normalized_path))
            diag_elapsed = time.time() - diag_start
            print_profile(profile)
            print(f"      Diagnosis completed in {diag_elapsed:.1f}s")
        else:
            print("[2/5] Skipping diagnosis (--generic mode)")

        # Step 3: Artifact scan (before processing)
        print("[3/5] Scanning for localized artifacts...")
        artifacts_before = scan_artifacts(str(normalized_path))
        if artifacts_before:
            print(f"      Found {len(artifacts_before)} artifact(s) in raw audio:")
            print_artifacts(artifacts_before)
        else:
            print("      No localized artifacts detected in raw audio.")

        # Step 4: DSP processing
        print("[4/5] Applying DSP chain...")
        processed_path = Path(tmpdir) / "processed.wav"
        result = process_audio(
            str(normalized_path),
            str(processed_path),
            profile=profile,
        )
        duration = result["duration_seconds"]
        chain_desc = result.get("chain_description", "generic cleanup chain")
        print(f"      Processed {duration:.1f}s of audio")
        print(f"      Chain: {chain_desc}")

        # Artifact scan on processed output
        artifacts_after = scan_artifacts(str(processed_path))
        if artifacts_after:
            print(f"      WARNING: {len(artifacts_after)} artifact(s) remain after processing:")
            print_artifacts(artifacts_after)
        else:
            print("      No artifacts in processed output.")

        # Step 5: Export before/after
        print("[5/5] Exporting before/after files...")
        export_result = export_before_after(
            original_path=normalized_path,
            processed_path=processed_path,
            output_dir=args.output_dir,
            project_name=args.name,
        )

    elapsed = time.time() - start_time

    print()
    print("=" * 40)
    print("Alpha 2.2 Report")
    print("=" * 40)
    print(f"Duration: {duration:.1f}s | Processed in {elapsed:.1f}s")
    print(f"Chain: {chain_desc}")
    print(f"Artifacts before: {len(artifacts_before)} | After: {len(artifacts_after)}")
    if profile:
        active = [d for d in profile.diagnoses if d.severity.value > 0]
        print(f"Issues detected: {len(active)}/7")
        for d in active:
            freq = f" @ {d.detected_frequency_hz:.0f}Hz" if d.detected_frequency_hz else ""
            print(f"  {d.category}: {d.severity.name}{freq}")
    print()
    print(f"Before: {export_result['before']}")
    print(f"After:  {export_result['after']}")


if __name__ == "__main__":
    main()
