"""Command-line interface for DeadCrypt.

Supports both a scriptable subcommand interface::

    deadcrypt encode secret.zip --resolution 1080p
    deadcrypt decode encoded/secret.zip.mkv

and a friendly interactive mode when run with no arguments::

    deadcrypt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .core import (
    DEFAULT_FPS,
    DEFAULT_RESOLUTION_KEY,
    RESOLUTIONS,
    Resolution,
    resolve_resolution,
)
from .decoder import decode_video_to_file
from .encoder import encode_file_to_video


def _human_size(num_bytes: float) -> str:
    """Format a byte count as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024 or unit == "TB":
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"


# --------------------------------------------------------------------------- #
# Subcommand handlers
# --------------------------------------------------------------------------- #


def _cmd_encode(args: argparse.Namespace) -> int:
    try:
        resolution = resolve_resolution(args.resolution)
    except KeyError:
        labels = ", ".join(r.label for r in RESOLUTIONS.values())
        print(f"Unknown resolution '{args.resolution}'. Choose one of: {labels}")
        return 2

    try:
        output = encode_file_to_video(
            args.file,
            resolution,
            fps=args.fps,
            output_dir=args.output_dir,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Encoded -> {output}  ({_human_size(output.stat().st_size)})")
    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    try:
        recovered = decode_video_to_file(args.video, output_dir=args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Recovered -> {recovered}  ({_human_size(recovered.stat().st_size)})")
    return 0


# --------------------------------------------------------------------------- #
# Interactive mode
# --------------------------------------------------------------------------- #


def _prompt_resolution() -> Resolution:
    print("Select video resolution:")
    for key, res in RESOLUTIONS.items():
        print(
            f"  {key}. {res.label:<6} ({res.width}x{res.height}) "
            f"- {_human_size(res.capacity)} per frame"
        )
    choice = input("Enter option number: ").strip()
    if choice not in RESOLUTIONS:
        print(f"Invalid choice, defaulting to {RESOLUTIONS[DEFAULT_RESOLUTION_KEY].label}.")
        choice = DEFAULT_RESOLUTION_KEY
    return RESOLUTIONS[choice]


def _interactive_encode() -> int:
    file_path = input("Enter path to the file to encode: ").strip().strip('"')
    if not Path(file_path).is_file():
        print("Error: File does not exist!")
        return 1
    resolution = _prompt_resolution()
    output = encode_file_to_video(file_path, resolution)
    print(f"\nEncoded -> {output}  ({_human_size(output.stat().st_size)})")
    return 0


def _interactive_decode() -> int:
    encoded_dir = Path("encoded")
    videos = sorted(encoded_dir.glob("*.mkv")) if encoded_dir.is_dir() else []
    if not videos:
        print("No videos found in the 'encoded' folder!")
        return 1
    print("Available videos:")
    for index, video in enumerate(videos, start=1):
        print(f"  {index}. {video.name}")
    try:
        choice = int(input("Select a video to decode (number): ")) - 1
        selected = videos[choice]
    except (ValueError, IndexError):
        print("Invalid selection!")
        return 1
    recovered = decode_video_to_file(selected)
    print(f"\nRecovered -> {recovered}  ({_human_size(recovered.stat().st_size)})")
    return 0


def _interactive() -> int:
    print("=== DeadCrypt ===")
    print("1. Encode a file into a video")
    print("2. Decode a video back into a file")
    choice = input("Choose an option: ").strip()
    if choice == "1":
        return _interactive_encode()
    if choice == "2":
        return _interactive_decode()
    print("Invalid option.")
    return 2


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deadcrypt",
        description="Turn any file into lossless 'TV static' video and back.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    encode = subparsers.add_parser("encode", help="Encode a file into a video.")
    encode.add_argument("file", help="Path to the file to encode.")
    encode.add_argument(
        "-r",
        "--resolution",
        default=RESOLUTIONS[DEFAULT_RESOLUTION_KEY].label,
        help="Frame resolution, e.g. 720p or 1080p (default: %(default)s).",
    )
    encode.add_argument(
        "--fps", type=int, default=DEFAULT_FPS, help="Output frame rate (default: %(default)s)."
    )
    encode.add_argument(
        "-o", "--output-dir", default="encoded", help="Output directory (default: %(default)s)."
    )
    encode.set_defaults(func=_cmd_encode)

    decode = subparsers.add_parser("decode", help="Decode a video back into a file.")
    decode.add_argument("video", help="Path to the DeadCrypt .mkv video.")
    decode.add_argument(
        "-o", "--output-dir", default="decoded", help="Output directory (default: %(default)s)."
    )
    decode.set_defaults(func=_cmd_decode)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) is None:
        return _interactive()
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
