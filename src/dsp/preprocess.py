"""FFmpeg preprocessing for DrakoTune.

Normalizes raw vocal input to a consistent format before DSP processing:
- 44100 Hz sample rate
- 16-bit signed integer PCM
- Mono channel
"""

import os
import subprocess
import shutil
from pathlib import Path


TARGET_SAMPLE_RATE = 44100
TARGET_BIT_DEPTH = 16
TARGET_CHANNELS = 1

_FFMPEG_FALLBACK_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
    r"C:\Program Files\DownloadHelper CoApp\ffmpeg.exe",
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\tools\ffmpeg\bin\ffmpeg.exe",
]


def _find_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path is not None:
        return path

    for fallback in _FFMPEG_FALLBACK_PATHS:
        if os.path.isfile(fallback):
            return fallback

    raise RuntimeError(
        "FFmpeg not found on PATH. Install FFmpeg: https://ffmpeg.org/download.html"
    )


def probe_channels(input_path: str | Path) -> int | None:
    """Channel count of the ORIGINAL upload (M41 honesty advisory).

    Uses soundfile where the container is supported; falls back to None for
    exotic formats rather than shelling out — a missing probe only means the
    stereo-summed warning is skipped, never a failure.
    """
    try:
        import soundfile as sf

        return int(sf.info(str(input_path)).channels)
    except Exception:
        return None


def preprocess(
    input_path: str | Path,
    output_path: str | Path,
    channels: int = TARGET_CHANNELS,
) -> Path:
    """Normalize a vocal file to 44100Hz, 16-bit WAV using FFmpeg.

    Mono remains the default and the right choice for a *lead vocal input*: a
    single performance carries no stereo information worth preserving, and
    summing it first keeps every downstream measurement unambiguous.

    `channels=2` exists because that default was previously a hard rule, which
    made stereo output impossible no matter what the graph did (DT-94/F-10). The
    input stage and the output stage are now separate decisions: a mono vocal can
    be fed to a V3 graph that emits stereo effects, and the export path preserves
    whatever width the graph produced.

    Args:
        input_path: Path to the raw vocal file (WAV, MP3, etc.)
        output_path: Path where the normalized WAV will be written.
        channels: 1 (default, vocal-only) or 2.

    Returns:
        Path to the normalized output file.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If FFmpeg is not installed or processing fails.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if channels not in (1, 2):
        raise ValueError(f"channels must be 1 or 2, got {channels}")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = _find_ffmpeg()

    cmd = [
        ffmpeg,
        "-y",
        "-i", str(input_path),
        "-ar", str(TARGET_SAMPLE_RATE),
        "-ac", str(channels),
        "-sample_fmt", "s16",
        "-c:a", "pcm_s16le",
        str(output_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg preprocessing failed (exit {result.returncode}):\n{result.stderr}"
        )

    if not output_path.exists():
        raise RuntimeError(f"FFmpeg produced no output at: {output_path}")

    return output_path
