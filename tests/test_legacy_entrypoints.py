import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_retired_streamlit_entrypoints_fail_fast():
    entrypoints = [
        "main.py",
        "app.py",
        "financeiq_pro.py",
        "game_changer_dashboard.py",
        "test_tabs.py",
    ]

    for entrypoint in entrypoints:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / entrypoint)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
