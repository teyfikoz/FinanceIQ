#!/usr/bin/env python3
"""Retired Streamlit helper stub."""

from pathlib import Path


LEGACY_PATH = (
    Path(__file__).resolve().parent
    / "archive"
    / "retired_streamlit_runtime"
    / "test_tabs_streamlit_legacy.py"
)


def main() -> None:
    raise RuntimeError(
        "The Streamlit tab test helper has been retired. "
        f"Legacy code was archived at {LEGACY_PATH}. "
        "Use the FastAPI runtime and pytest suite instead."
    )


if __name__ == "__main__":
    main()
