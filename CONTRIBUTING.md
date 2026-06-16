# Contributing to DeadCrypt

Thanks for your interest in improving DeadCrypt! Contributions of all sizes are
welcome.

## Getting set up

```bash
git clone https://github.com/dev2180/DeadCrypt.git
cd DeadCrypt
pip install -e ".[dev]"
```

You'll also need [FFmpeg](https://ffmpeg.org/download.html) on your `PATH` to run
the end-to-end tests.

## Running the tests

```bash
pytest -v
```

- `tests/test_core.py` runs anywhere (no ffmpeg needed).
- `tests/test_roundtrip.py` is skipped automatically when ffmpeg is missing.

Please make sure the full suite passes before opening a pull request.

## Guidelines

- Keep the encoder and decoder in sync by putting shared serialisation logic in
  [`deadcrypt/core.py`](deadcrypt/core.py).
- Maintain the lossless guarantee — any change to the encode/decode path **must**
  keep the round-trip test green.
- Add or update tests for behaviour you change.
- Match the existing style: type hints, docstrings, and small focused functions.
- If you change the container header format, bump `HEADER_VERSION` and keep
  older versions decodable.

## Reporting bugs / ideas

Open an issue describing the problem (with reproduction steps) or the feature
you'd like to see. See the roadmap in the [README](README.md) for directions
already on the table.
