"""Core primitives shared by the DeadCrypt encoder and decoder.

This module owns three concerns:

1. **Resolutions** — the catalogue of supported (YouTube-friendly) frame sizes
   and how much payload each frame can carry.
2. **The container header** — a small, self-describing prefix that travels
   *inside* the pixel stream so a video can be decoded without trusting its
   filename.
3. **Frame (de)serialisation** — converting a byte stream to PNG frames and
   back.

Keeping these helpers in one place means the encoder and decoder cannot drift
out of sync with each other.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List

import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- #
# Resolutions
# --------------------------------------------------------------------------- #

# Each pixel stores 3 bytes (one per RGB channel), so a frame's raw capacity is
# simply ``width * height * 3`` bytes.
BYTES_PER_PIXEL = 3


@dataclass(frozen=True)
class Resolution:
    """A named frame size and its derived byte capacity."""

    label: str
    width: int
    height: int

    @property
    def capacity(self) -> int:
        """Number of payload bytes a single frame of this size can hold."""
        return self.width * self.height * BYTES_PER_PIXEL


# Ordered from smallest to largest. Keys double as the numeric menu options in
# the interactive CLI, while ``label`` (e.g. "1080p") is accepted on the
# command line.
RESOLUTIONS: Dict[str, Resolution] = {
    "1": Resolution("240p", 426, 240),
    "2": Resolution("360p", 640, 360),
    "3": Resolution("480p", 854, 480),
    "4": Resolution("720p", 1280, 720),
    "5": Resolution("1080p", 1920, 1080),
    "6": Resolution("1440p", 2560, 1440),
    "7": Resolution("2160p", 3840, 2160),
}

#: Default resolution used when an interactive choice is invalid.
DEFAULT_RESOLUTION_KEY = "4"  # 720p

#: Default frame rate. 24 fps is a safe, broadly supported value.
DEFAULT_FPS = 24


def resolve_resolution(value: str) -> Resolution:
    """Resolve a resolution from a menu key (``"5"``) or label (``"1080p"``).

    Raises:
        KeyError: if ``value`` matches neither a menu key nor a known label.
    """
    if value in RESOLUTIONS:
        return RESOLUTIONS[value]
    needle = value.lower().strip()
    for resolution in RESOLUTIONS.values():
        if resolution.label.lower() == needle:
            return resolution
    raise KeyError(value)


def capacity_bytes(width: int, height: int) -> int:
    """Return the payload capacity (in bytes) of a ``width`` x ``height`` frame."""
    return width * height * BYTES_PER_PIXEL


# --------------------------------------------------------------------------- #
# Container header
# --------------------------------------------------------------------------- #
#
# Layout (big-endian), prepended to the file's bytes before framing:
#
#     magic     : 4 bytes  -> b"DCRT"
#     version   : 1 byte   -> HEADER_VERSION
#     name_len  : 2 bytes  -> length of the UTF-8 filename
#     name      : N bytes  -> original filename (basename only)
#     data_len  : 8 bytes  -> original file size in bytes
#     ... file bytes follow ...
#
# Embedding the metadata in the stream (rather than the .mkv filename) means the
# video is self-describing: rename it to anything and it still decodes.

MAGIC = b"DCRT"
HEADER_VERSION = 1
_FIXED_HEADER = struct.Struct(">4sBH")  # magic, version, name_len
_DATA_LEN = struct.Struct(">Q")  # uint64 original size


@dataclass(frozen=True)
class FileHeader:
    """Parsed metadata describing the payload carried by a DeadCrypt video."""

    filename: str
    size: int


def build_header(filename: str, size: int) -> bytes:
    """Serialise a :class:`FileHeader` to bytes."""
    name_bytes = filename.encode("utf-8")
    if len(name_bytes) > 0xFFFF:
        raise ValueError("Filename is too long to store in the header.")
    return (
        _FIXED_HEADER.pack(MAGIC, HEADER_VERSION, len(name_bytes))
        + name_bytes
        + _DATA_LEN.pack(size)
    )


def parse_header(stream: bytes) -> tuple[FileHeader, int]:
    """Parse a header from the front of ``stream``.

    Returns:
        A tuple of ``(FileHeader, payload_offset)`` where ``payload_offset`` is
        the index at which the file's actual bytes begin.

    Raises:
        ValueError: if the magic number or version is not recognised.
    """
    if len(stream) < _FIXED_HEADER.size:
        raise ValueError("Stream is too short to contain a DeadCrypt header.")

    magic, version, name_len = _FIXED_HEADER.unpack_from(stream, 0)
    if magic != MAGIC:
        raise ValueError("Not a DeadCrypt stream (bad magic number).")
    if version != HEADER_VERSION:
        raise ValueError(f"Unsupported DeadCrypt header version: {version}.")

    offset = _FIXED_HEADER.size
    filename = stream[offset : offset + name_len].decode("utf-8")
    offset += name_len
    (size,) = _DATA_LEN.unpack_from(stream, offset)
    offset += _DATA_LEN.size
    return FileHeader(filename=filename, size=size), offset


# --------------------------------------------------------------------------- #
# Frame (de)serialisation
# --------------------------------------------------------------------------- #


def frame_count(stream_size: int, capacity: int) -> int:
    """Number of frames needed to store ``stream_size`` bytes at ``capacity``."""
    return max(1, -(-stream_size // capacity))  # ceil division


def iter_frames(stream: bytes, resolution: Resolution) -> Iterator[np.ndarray]:
    """Yield zero-padded ``(height, width, 3)`` uint8 arrays for ``stream``.

    The final frame is padded with zero bytes so it fills the full resolution;
    the padding is stripped on decode using the size recorded in the header.
    """
    capacity = resolution.capacity
    shape = (resolution.height, resolution.width, BYTES_PER_PIXEL)
    for start in range(0, max(len(stream), 1), capacity):
        chunk = stream[start : start + capacity]
        if len(chunk) < capacity:
            chunk = chunk + bytes(capacity - len(chunk))
        yield np.frombuffer(chunk, dtype=np.uint8).reshape(shape)


def write_frames(stream: bytes, resolution: Resolution, frames_dir: Path) -> List[Path]:
    """Write ``stream`` to sequential PNG frames inside ``frames_dir``.

    Frames are named ``frame_000001.png`` (6-digit, 1-based) which matches the
    ffmpeg glob pattern ``frame_%06d.png`` and keeps lexical and numeric order
    identical for up to 999,999 frames.
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for index, array in enumerate(iter_frames(stream, resolution), start=1):
        path = frames_dir / f"frame_{index:06d}.png"
        Image.fromarray(array).save(path)
        paths.append(path)
    return paths


def read_frames(frame_paths: List[Path]) -> bytes:
    """Concatenate the raw pixel bytes of ``frame_paths`` back into a stream."""
    buffer = bytearray()
    for path in frame_paths:
        with Image.open(path) as image:
            buffer.extend(image.convert("RGB").tobytes())
    return bytes(buffer)


#: ffmpeg-compatible frame filename pattern.
FRAME_PATTERN = "frame_%06d.png"
