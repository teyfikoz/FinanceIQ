#!/usr/bin/env python3
"""Retired Streamlit entrypoint stub."""

from pathlib import Path


LEGACY_PATH = Path(__file__).resolve().parent / "archive" / "retired_streamlit_runtime" / "main_streamlit_legacy.py"


def main() -> None:
    raise RuntimeError(
        "The Streamlit runtime has been retired. "
        f"Legacy code was archived at {LEGACY_PATH}. "
        "Start FundPilot with `uvicorn app.main:app --host 127.0.0.1 --port 8000`."
    )


if __name__ == "__main__":
    main()
