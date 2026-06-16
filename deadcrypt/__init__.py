"""DeadCrypt — turn any file into lossless "TV static" video and back.

DeadCrypt serialises a file's raw bytes directly into the RGB channels of
video frames, encodes those frames with the lossless FFV1 codec, and can
reconstruct the original file byte-for-byte from the resulting video.

Public API
----------
- :func:`deadcrypt.encoder.encode_file_to_video`
- :func:`deadcrypt.decoder.decode_video_to_file`
- :data:`deadcrypt.core.RESOLUTIONS`
"""

from __future__ import annotations

from .core import RESOLUTIONS, Resolution, capacity_bytes
from .decoder import decode_video_to_file
from .encoder import encode_file_to_video

__all__ = [
    "RESOLUTIONS",
    "Resolution",
    "capacity_bytes",
    "encode_file_to_video",
    "decode_video_to_file",
    "__version__",
]

__version__ = "1.0.0"
