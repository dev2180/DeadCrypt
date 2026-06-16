#!/usr/bin/env python3
"""Generate the README demo GIF.

Runs a real file through the DeadCrypt encoder and renders an animated GIF that
shows, side by side:

    * a terminal typing the `deadcrypt encode ...` command + its output, and
    * the resulting lossless "TV static" video frames playing.

The static frames shown are the *actual* bytes the encoder writes (produced via
``deadcrypt.core.iter_frames`` on the same header+payload stream), so the demo
is a faithful representation of the encoded video, not a mock-up.

Usage:
    python tools/make_demo.py
Output:
    docs/demo.gif
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deadcrypt.core import RESOLUTIONS, build_header, iter_frames
from deadcrypt.encoder import encode_file_to_video

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo.gif"

RES = RESOLUTIONS["1"]            # 240p keeps frames small and the GIF light
SAMPLE_NAME = "secret_archive.7z"  # pretend it's a compressed archive
N_SOURCE_FRAMES = 14               # how many real video frames to render
PAYLOAD = RES.capacity * N_SOURCE_FRAMES - 64  # fill ~N frames (minus header)

W, H = 860, 470                    # canvas
BG = (13, 17, 23)                  # GitHub dark
PANEL = (22, 27, 34)
BORDER = (48, 54, 61)
FG = (201, 209, 217)
DIM = (110, 118, 129)
GREEN = (63, 185, 80)
CYAN = (57, 197, 187)
YELLOW = (210, 168, 90)
WHITE = (240, 246, 252)
RED_DOT, YEL_DOT, GRN_DOT = (255, 95, 86), (255, 189, 46), (39, 201, 63)

FONT_DIR = Path(r"C:\Windows\Fonts")


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


MONO = _font("consola.ttf", 17)
MONO_S = _font("consola.ttf", 14)
BOLD = _font("consolab.ttf", 19)
BOLD_S = _font("consolab.ttf", 15)


# --------------------------------------------------------------------------- #
# Build the real video frames
# --------------------------------------------------------------------------- #
def build_source_frames() -> tuple[list[Image.Image], Path, int]:
    """Encode a sample file and return the real video frames + output info."""
    sample = ROOT / SAMPLE_NAME
    rng = np.random.default_rng(20260616)  # deterministic "compressed" bytes
    sample.write_bytes(rng.integers(0, 256, size=PAYLOAD, dtype=np.uint8).tobytes())

    # The exact frames the encoder serialises (lossless => identical to the mkv).
    stream = build_header(sample.name, PAYLOAD) + sample.read_bytes()
    frames = [
        Image.fromarray(arr).resize((288, 162), Image.NEAREST)
        for arr in iter_frames(stream, RES)
    ]

    # Produce the real .mkv too, so the caption shows a genuine output size.
    video = encode_file_to_video(
        sample, RES, output_dir=ROOT / "encoded", show_progress=False
    )
    size = video.stat().st_size

    sample.unlink(missing_ok=True)
    return frames, video, size


# --------------------------------------------------------------------------- #
# Drawing helpers
# --------------------------------------------------------------------------- #
def rounded(draw: ImageDraw.ImageDraw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def progress_bar(pct: float, width_chars: int = 22) -> str:
    filled = int(round(pct * width_chars))
    return "#" * filled + "-" * (width_chars - filled)


# --------------------------------------------------------------------------- #
# Compose the animation
# --------------------------------------------------------------------------- #
def main() -> None:
    src_frames, video, size = build_source_frames()
    n_frames = len(src_frames)
    mb = size / (1024 * 1024)

    command = f"deadcrypt encode {SAMPLE_NAME} -r 240p"
    rel_video = f"encoded/{video.name}"

    # Terminal panel geometry
    tx, ty, tw, th = 28, 92, 470, 348
    # Monitor panel geometry
    mx, my, mw, mh = 524, 120, 308, 300
    screen = (mx + 10, my + 14, mx + mw - 10, my + 14 + 162)

    # Animation timeline (in GIF frames)
    type_end = len(command)            # one char per frame while typing
    pause = 6
    bar_frames = 18
    tail = 26
    total = type_end + pause + bar_frames + tail

    gif_frames: list[Image.Image] = []

    for f in range(total):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)

        # --- Header ---------------------------------------------------------
        d.text((28, 26), "DeadCrypt", font=BOLD, fill=WHITE)
        d.text((150, 30), "·  any file  →  lossless video  →  any file",
                font=MONO_S, fill=DIM)

        # --- Terminal panel -------------------------------------------------
        rounded(d, (tx, ty, tx + tw, ty + th), 10, fill=PANEL, outline=BORDER, width=1)
        d.rectangle((tx, ty, tx + tw, ty + 30), fill=(30, 36, 44))
        rounded(d, (tx, ty, tx + tw, ty + 30), 10, outline=BORDER, width=1)
        for i, c in enumerate((RED_DOT, YEL_DOT, GRN_DOT)):
            d.ellipse((tx + 16 + i * 20, ty + 11, tx + 24 + i * 20, ty + 19), fill=c)
        d.text((tx + tw / 2 - 40, ty + 8), "bash — deadcrypt", font=MONO_S, fill=DIM)

        line_x = tx + 16
        y = ty + 46

        # typed command (revealed char by char)
        shown = command[: min(f, type_end)] if f < type_end else command
        d.text((line_x, y), "$ ", font=MONO, fill=GREEN)
        d.text((line_x + 18, y), shown, font=MONO, fill=FG)
        # blinking cursor while typing / idle
        if f < type_end or (f // 3) % 2 == 0:
            cw = d.textlength("$ " + shown, font=MONO)
            if f <= type_end:
                d.rectangle((line_x + cw, y + 2, line_x + cw + 9, y + 20), fill=FG)

        # output appears after typing + pause
        out_y = y + 36
        after = f - type_end - pause
        if after >= 0:
            d.text((line_x, out_y), "Reading secret_archive.7z ...",
                   font=MONO_S, fill=DIM)
            pct = 1.0 if after >= bar_frames else after / bar_frames
            shown_frames = int(round(pct * n_frames))
            bar = progress_bar(pct)
            d.text((line_x, out_y + 26), f"Packing frames |{bar}|",
                   font=MONO_S, fill=CYAN)
            d.text((line_x, out_y + 48),
                   f"{shown_frames:>2}/{n_frames} frames   "
                   f"{int(pct*100):>3}%   24 fps   FFV1",
                   font=MONO_S, fill=DIM)

            if pct >= 1.0:
                d.text((line_x, out_y + 84), "OK  encoded ->", font=BOLD_S, fill=GREEN)
                d.text((line_x, out_y + 106), rel_video, font=MONO_S, fill=WHITE)
                d.text((line_x, out_y + 128), f"   {mb:.2f} MB · lossless · self-describing",
                       font=MONO_S, fill=DIM)
                d.text((line_x, out_y + 162), "$ ", font=MONO, fill=GREEN)
                if (f // 3) % 2 == 0:
                    d.rectangle((line_x + 18, out_y + 164, line_x + 27, out_y + 182),
                                fill=FG)

        # --- Monitor panel (the "video file") -------------------------------
        rounded(d, (mx, my, mx + mw, my + mh), 14, fill=(8, 10, 14),
                outline=BORDER, width=2)
        # current static frame (cycles continuously)
        frame = src_frames[f % n_frames]
        img.paste(frame, (screen[0], screen[1]))
        d.rectangle((screen[0], screen[1], screen[2], screen[3]),
                    outline=(40, 46, 54), width=1)
        # scanline shimmer
        sl = (f * 9) % 162
        d.line((screen[0], screen[1] + sl, screen[2], screen[1] + sl),
               fill=(255, 255, 255), width=1)

        # red "REC" + label
        d.ellipse((mx + 16, my + 192, mx + 26, my + 202), fill=RED_DOT)
        d.text((mx + 34, my + 190), "REC  ·  TV-static video", font=MONO_S, fill=FG)
        d.text((mx + 16, my + 220), video.name, font=BOLD_S, fill=CYAN)
        d.text((mx + 16, my + 242),
               f"{RES.label} · {RES.width}x{RES.height} · {n_frames} frames",
               font=MONO_S, fill=DIM)
        d.text((mx + 16, my + 264),
               "decode -> byte-for-byte identical", font=MONO_S, fill=GREEN)

        # arrow between panels
        ay = ty + th / 2
        d.text((tx + tw + 8, ay - 14), "==>", font=BOLD, fill=YELLOW)

        gif_frames.append(img)

    durations = [70] * type_end + [260] * pause
    durations += [90] * bar_frames + [120] * tail
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gif_frames[0].save(
        OUT,
        save_all=True,
        append_images=gif_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )

    # also drop a poster frame for quick visual QA
    gif_frames[-1].save(ROOT / "docs" / "demo_poster.png")
    print(f"Wrote {OUT}  ({OUT.stat().st_size/1024:.0f} KB, {len(gif_frames)} frames)")


if __name__ == "__main__":
    main()
