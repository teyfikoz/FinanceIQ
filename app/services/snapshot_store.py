from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


class SnapshotStore:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        if base_dir is None:
            root = Path(__file__).resolve().parents[2]
            base_dir = root / settings.PUBLIC_SNAPSHOT_DIR
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.base_dir / f"{safe}.json"

    def read_json(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def write_json(self, key: str, payload: Dict[str, Any]) -> None:
        path = self._path_for(key)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        tmp_path.replace(path)
