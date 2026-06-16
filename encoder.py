#!/usr/bin/env python3
"""Backward-compatible entry point: ``python encoder.py``.

The implementation now lives in the :mod:`deadcrypt` package. This shim keeps
the original interactive workflow working.
"""

from deadcrypt.cli import _interactive_encode

if __name__ == "__main__":
    raise SystemExit(_interactive_encode())
