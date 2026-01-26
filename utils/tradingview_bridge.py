#!/usr/bin/env python3
"""Optional bridge to TradingView-API (Node) for OHLCV data."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pandas as pd


class TradingViewBridge:
    def __init__(self, script_path: Optional[str] = None, timeout_s: int = 20):
        root = Path(__file__).resolve().parents[1]
        default_script = root / "scripts" / "tradingview_fetch.js"
        self.script_path = Path(script_path) if script_path else default_script
        self.timeout_s = timeout_s

    def available(self) -> bool:
        if not (bool(shutil.which("node")) and self.script_path.exists()):
            return False
        # Check if package is installed locally
        root = self.script_path.resolve().parents[1]
        pkg_path = root / "node_modules" / "@mathieuc" / "tradingview"
        return pkg_path.exists()

    def fetch_ohlc(self, symbol: str, timeframe: str = "D", limit: int = 200) -> Optional[pd.DataFrame]:
        if not self.available():
            return None

        cmd = [
            "node",
            str(self.script_path),
            "--symbol",
            symbol,
            "--timeframe",
            str(timeframe),
            "--range",
            str(limit),
        ]

        env = os.environ.copy()
        # Optional TradingView session cookies
        if env.get("TV_SESSION") and not env.get("TRADINGVIEW_SESSION"):
            env["TRADINGVIEW_SESSION"] = env["TV_SESSION"]
        if env.get("TV_SIGNATURE") and not env.get("TRADINGVIEW_SIGNATURE"):
            env["TRADINGVIEW_SIGNATURE"] = env["TV_SIGNATURE"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_s,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "TradingView fetch failed")

        payload = json.loads(result.stdout)
        periods = payload.get("periods", [])
        if not periods:
            return pd.DataFrame()

        df = pd.DataFrame(periods)
        df["Datetime"] = pd.to_datetime(df["time"], unit="s")
        df = df.set_index("Datetime")
        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        })
        return df[["Open", "High", "Low", "Close", "Volume"]].sort_index()
