"""Export utilities for DrakoTune.

Handles copying before/after files to an output directory
for easy comparison and final export.
"""

import shutil
from pathlib import Path


def export_before_after(
    original_path: str | Path,
    processed_path: str | Path,
    output_dir: str | Path,
    project_name: str = "vocal",
) -> dict:
    """Copy original and processed files to output directory as a before/after pair.

    Args:
        original_path: Path to the preprocessed (normalized) original WAV.
        processed_path: Path to the DSP-processed WAV.
        output_dir: Directory where before/after files will be placed.
        project_name: Base name for output files.

    Returns:
        Dict with paths to the before and after files.
    """
    original_path = Path(original_path)
    processed_path = Path(processed_path)
    output_dir = Path(output_dir)

    if not original_path.exists():
        raise FileNotFoundError(f"Original file not found: {original_path}")
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed file not found: {processed_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    before_path = output_dir / f"{project_name}_before.wav"
    after_path = output_dir / f"{project_name}_after.wav"

    shutil.copy2(str(original_path), str(before_path))
    shutil.copy2(str(processed_path), str(after_path))

    return {
        "before": str(before_path),
        "after": str(after_path),
        "output_dir": str(output_dir),
    }
