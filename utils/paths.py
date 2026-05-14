"""Single source of truth for the project root path."""
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
