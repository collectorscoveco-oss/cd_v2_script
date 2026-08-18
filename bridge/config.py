import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.example.json"
USER_CONFIG = ROOT / "config.json"


def ensure_config(path: Path | None = None) -> Path:
    target = path or USER_CONFIG
    if not target.exists():
        shutil.copyfile(DEFAULT_CONFIG, target)
    return target


def load_config(path: str | Path | None = None) -> dict:
    target = ensure_config(Path(path) if path else None)
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)
