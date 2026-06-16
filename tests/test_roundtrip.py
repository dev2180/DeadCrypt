"""End-to-end encode -> decode round-trip test.

This test exercises the real ffmpeg pipeline, so it is skipped automatically
when the ``ffmpeg`` binary is not available on PATH.
"""

from __future__ import annotations

import os
import shutil

import pytest

from deadcrypt import core
from deadcrypt.decoder import decode_video_to_file
from deadcrypt.encoder import encode_file_to_video

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="ffmpeg binary not available on PATH",
)


@pytest.mark.parametrize("size", [0, 1, 5000, 200_000])
def test_encode_decode_round_trip(tmp_path, size):
    original = tmp_path / "payload.bin"
    original.write_bytes(os.urandom(size))

    video = encode_file_to_video(
        original,
        core.RESOLUTIONS["1"],  # 240p keeps the test fast
        output_dir=tmp_path / "encoded",
        show_progress=False,
    )
    assert video.is_file()

    recovered = decode_video_to_file(video, output_dir=tmp_path / "decoded")
    assert recovered.name == original.name
    assert recovered.read_bytes() == original.read_bytes()
