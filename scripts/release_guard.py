#!/usr/bin/env python3
"""Repository-level release guard for FundPilot."""

from __future__ import annotations

import argparse
import py_compile
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CACHE_MARKER = "INTENTIONAL CACHE DIVERGENCE"
LEGACY_BRANDS = ("FinanceIQ",)
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".service",
    ".env",
    ".sh",
    ".js",
    ".ts",
    ".css",
    ".html",
    ".xml",
}
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "archive",
    "build",
    "dist",
    "htmlcov",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "data",
}
SECRET_KEYS = (
    "SECRET_KEY",
    "FRED_API_KEY",
    "FINNHUB_API_KEY",
    "ALPHA_VANTAGE_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "FMP_API_KEY",
    "POLYGON_API_KEY",
    "TRADINGECONOMICS_KEY",
    "EVDS_API_KEY",
    "TCMB_EVDS_API_KEY",
    "TWELVEDATA_API_KEY",
    "TWELVEDATA_KEY",
    "NEWSAPI_KEY",
    "COINGECKO_API_KEY",
    "POSTGRES_PASSWORD",
    "SMTP_PASSWORD",
)
ALLOWED_SECRET_MARKERS = (
    "your_",
    "YOUR_",
    "replace_",
    "REPLACE_",
    "change_",
    "CHANGE_",
    "use_strong",
    "USE_STRONG",
    "placeholder",
    "PLACEHOLDER",
    "example",
    "EXAMPLE",
    "...",
    "${{",
    "$(",
    "<",
    ">",
    "optional",
    "Optional",
    "None",
    "null",
)
SECRET_PATTERN = re.compile(
    rf"(?:export\s+)?({'|'.join(map(re.escape, SECRET_KEYS))})\s*[:=]\s*[\"']?([A-Za-z0-9:_\-/\.]+)"
)


@dataclass
class CheckFailure:
    check: str
    detail: str


def iter_repo_files(*, suffixes: set[str] | None = None) -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if suffixes is not None and path.suffix not in suffixes:
            continue
        yield path


def compile_python_sources() -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    for path in iter_repo_files(suffixes={".py"}):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(CheckFailure("compile", f"{path.relative_to(ROOT)}: {exc.msg}"))
    return failures


def check_main_import_is_silent() -> list[CheckFailure]:
    command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            f"sys.path.insert(0, {ROOT.as_posix()!r}); "
            "import main"
        ),
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    failures: list[CheckFailure] = []
    if result.returncode != 0:
        failures.append(
            CheckFailure(
                "import-main",
                f"returncode={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
        )
        return failures
    if result.stdout.strip() or result.stderr.strip():
        failures.append(
            CheckFailure(
                "import-main",
                f"unexpected output\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
        )
    return failures


def check_legacy_branding() -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    for path in iter_repo_files(suffixes=TEXT_EXTENSIONS):
        if path == Path(__file__):
            continue
        text = path.read_text(errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for brand in LEGACY_BRANDS:
                if brand in line:
                    failures.append(
                        CheckFailure("branding", f"{path.relative_to(ROOT)}:{line_no}: contains {brand!r}")
                    )
    return failures


def check_cache_annotations() -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    for path in iter_repo_files(suffixes={".py"}):
        if path == Path(__file__):
            continue
        lines = path.read_text(errors="ignore").splitlines()
        for index, line in enumerate(lines):
            if "@st.cache_data" not in line:
                continue
            previous = "\n".join(lines[max(0, index - 3):index])
            if CACHE_MARKER not in previous:
                failures.append(
                    CheckFailure(
                        "cache-annotation",
                        f"{path.relative_to(ROOT)}:{index + 1}: missing '{CACHE_MARKER}' comment",
                    )
                )
    return failures


def check_hardcoded_secrets() -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    for path in iter_repo_files(suffixes=TEXT_EXTENSIONS):
        text = path.read_text(errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if path.suffix == ".py" and ("os.environ.get(" in line or "os.getenv(" in line or "get_secret(" in line):
                continue
            for match in SECRET_PATTERN.finditer(line):
                key, value = match.groups()
                if value.lower() == "demo":
                    continue
                if any(marker in value for marker in ALLOWED_SECRET_MARKERS):
                    continue
                failures.append(
                    CheckFailure(
                        "hardcoded-secret",
                        f"{path.relative_to(ROOT)}:{line_no}: {key} appears to contain a concrete value",
                    )
                )
    return failures


def run_pytest() -> list[CheckFailure]:
    result = subprocess.run(["pytest", "-q", "tests/"], cwd=ROOT)
    if result.returncode == 0:
        return []
    return [CheckFailure("pytest", f"pytest exited with code {result.returncode}")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run FundPilot release guard checks.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip pytest execution.")
    args = parser.parse_args()

    failures: list[CheckFailure] = []
    failures.extend(compile_python_sources())
    failures.extend(check_main_import_is_silent())
    failures.extend(check_legacy_branding())
    failures.extend(check_cache_annotations())
    failures.extend(check_hardcoded_secrets())
    if not args.skip_pytest:
        failures.extend(run_pytest())

    if failures:
        print("FundPilot release guard failed:\n")
        for failure in failures:
            print(f"[{failure.check}] {failure.detail}")
        return 1

    print("FundPilot release guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
