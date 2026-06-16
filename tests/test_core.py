"""Unit tests for the header and framing primitives (no ffmpeg required)."""

from __future__ import annotations

import numpy as np
import pytest

from deadcrypt import core


def test_header_round_trips():
    header = core.build_header("secret.zip", 12345)
    parsed, offset = core.parse_header(header + b"payload")
    assert parsed.filename == "secret.zip"
    assert parsed.size == 12345
    assert offset == len(header)


def test_parse_header_rejects_foreign_stream():
    with pytest.raises(ValueError):
        core.parse_header(b"not a deadcrypt stream at all")


def test_unicode_filename_round_trips():
    header = core.build_header("naïve—file.txt", 7)
    parsed, _ = core.parse_header(header)
    assert parsed.filename == "naïve—file.txt"


def test_frame_count_uses_ceiling():
    assert core.frame_count(0, 100) == 1
    assert core.frame_count(1, 100) == 1
    assert core.frame_count(100, 100) == 1
    assert core.frame_count(101, 100) == 2


def test_iter_frames_pads_final_frame():
    res = core.Resolution("tiny", 2, 2)  # capacity = 2*2*3 = 12 bytes
    stream = bytes(range(13))  # 13 bytes -> 2 frames, second is padded
    frames = list(core.iter_frames(stream, res))
    assert len(frames) == 2
    assert frames[0].shape == (2, 2, 3)
    # First 12 bytes preserved, remainder zero-padded.
    assert frames[0].flatten().tolist() == list(range(12))
    assert frames[1].flatten().tolist() == [12] + [0] * 11


def test_resolve_resolution_by_key_and_label():
    assert core.resolve_resolution("5") is core.RESOLUTIONS["5"]
    assert core.resolve_resolution("1080p").label == "1080p"
    assert core.resolve_resolution("1080P").label == "1080p"
    with pytest.raises(KeyError):
        core.resolve_resolution("not-a-resolution")


def test_capacity_matches_resolution_property():
    res = core.RESOLUTIONS["4"]
    assert core.capacity_bytes(res.width, res.height) == res.capacity


def test_stream_to_frames_to_stream_is_lossless():
    """Frame packing/unpacking via numpy must be byte-exact (no ffmpeg)."""
    res = core.Resolution("tiny", 4, 4)
    payload = bytes(range(256)) * 3
    stream = core.build_header("data.bin", len(payload)) + payload

    rebuilt = bytearray()
    for array in core.iter_frames(stream, res):
        rebuilt.extend(np.asarray(array, dtype=np.uint8).tobytes())

    header, offset = core.parse_header(bytes(rebuilt))
    assert header.filename == "data.bin"
    assert bytes(rebuilt)[offset : offset + header.size] == payload
