"""Encode an arbitrary file into a lossless DeadCrypt video."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import ffmpeg
from tqdm import tqdm

from .core import (
    DEFAULT_FPS,
    FRAME_PATTERN,
    Resolution,
    build_header,
    frame_count,
    iter_frames,
)

from PIL import Image


def encode_file_to_video(
    file_path: str | Path,
    resolution: Resolution,
    *,
    fps: int = DEFAULT_FPS,
    output_dir: str | Path = "encoded",
    output_name: Optional[str] = None,
    show_progress: bool = True,
) -> Path:
    """Encode ``file_path`` into an FFV1 ``.mkv`` video.

    Args:
        file_path: File to encode.
        resolution: Target frame size (see :data:`deadcrypt.core.RESOLUTIONS`).
        fps: Frame rate of the output video.
        output_dir: Directory the encoded video is written to (created if
            missing).
        output_name: Optional output filename (``.mkv`` appended if absent).
            Defaults to ``<original-name>.mkv``.
        show_progress: Whether to render a tqdm progress bar.

    Returns:
        Path to the encoded video.

    Raises:
        FileNotFoundError: if ``file_path`` does not exist.
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = file_path.read_bytes()
    stream = build_header(file_path.name, len(payload)) + payload

    total_frames = frame_count(len(stream), resolution.capacity)

    name = output_name or f"{file_path.name}.mkv"
    if not name.endswith(".mkv"):
        name += ".mkv"
    output_video = output_dir / name

    # Frames are written to a throwaway temp directory so we never pollute the
    # working directory and cleanup is guaranteed even on failure.
    with tempfile.TemporaryDirectory(prefix="deadcrypt_enc_") as tmp:
        tmp_dir = Path(tmp)
        frames = iter_frames(stream, resolution)
        if show_progress:
            frames = tqdm(frames, total=total_frames, desc="Packing frames", unit="frame")

        for index, array in enumerate(frames, start=1):
            Image.fromarray(array).save(tmp_dir / f"frame_{index:06d}.png")

        (
            ffmpeg.input(str(tmp_dir / FRAME_PATTERN), framerate=fps)
            .output(str(output_video), vcodec="ffv1")
            .overwrite_output()
            .run(quiet=True)
        )

    return output_video
