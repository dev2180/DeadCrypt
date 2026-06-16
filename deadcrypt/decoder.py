"""Decode a DeadCrypt video back into its original file."""

from __future__ import annotations

import tempfile
from pathlib import Path

import ffmpeg

from .core import FileHeader, parse_header, read_frames


def _legacy_header_from_filename(video_path: Path) -> FileHeader | None:
    """Recover metadata from the old ``name__WxH__size.mkv`` naming scheme.

    Early DeadCrypt videos stored metadata in the filename instead of an
    in-stream header. This keeps those videos decodable.
    """
    stem = video_path.stem
    parts = stem.split("__")
    if len(parts) != 3:
        return None
    try:
        return FileHeader(filename=parts[0], size=int(parts[2]))
    except ValueError:
        return None


def decode_video_to_file(
    video_path: str | Path,
    *,
    output_dir: str | Path = "decoded",
) -> Path:
    """Decode ``video_path`` and restore the original file.

    The function prefers the self-describing in-stream header and transparently
    falls back to the legacy filename-based metadata for older videos.

    Args:
        video_path: Path to a DeadCrypt ``.mkv`` video.
        output_dir: Directory the recovered file is written to.

    Returns:
        Path to the recovered file.

    Raises:
        FileNotFoundError: if ``video_path`` does not exist.
        ValueError: if the video contains neither a valid header nor legacy
            filename metadata.
    """
    video_path = Path(video_path)
    if not video_path.is_file():
        raise FileNotFoundError(f"Video does not exist: {video_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="deadcrypt_dec_") as tmp:
        tmp_dir = Path(tmp)
        (
            ffmpeg.input(str(video_path))
            .output(str(tmp_dir / "frame_%06d.png"))
            .overwrite_output()
            .run(quiet=True)
        )
        frame_paths = sorted(tmp_dir.glob("frame_*.png"))
        if not frame_paths:
            raise ValueError("No frames could be extracted from the video.")
        stream = read_frames(frame_paths)

    try:
        header, offset = parse_header(stream)
        payload = stream[offset : offset + header.size]
    except ValueError:
        legacy = _legacy_header_from_filename(video_path)
        if legacy is None:
            raise ValueError(
                "Video is not a recognised DeadCrypt stream and has no legacy "
                "metadata in its filename."
            )
        header = legacy
        payload = stream[: header.size]

    recovered_path = output_dir / header.filename
    recovered_path.write_bytes(payload)
    return recovered_path
