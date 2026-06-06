import os
import subprocess
import sys
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_runtime_imports_without_streamlit():
    script = textwrap.dedent(
        """
        import builtins
        import importlib

        original_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "streamlit" or name.startswith("streamlit."):
                raise RuntimeError("streamlit import attempted")
            return original_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import
        module = importlib.import_module("app.main")
        assert module.app is not None
        print("ok")
        """
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
