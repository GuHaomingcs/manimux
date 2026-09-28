"""Ten reference images per task, shared by capture and evaluation viewers."""

from __future__ import annotations

import hashlib
import io
import re
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

DEFAULT_LAYOUT_ROOT = Path("data/evaluation_layouts")
REFERENCE_SLOTS = tuple(f"{index:02d}" for index in range(1, 11))


class ReferenceLayouts:
    def __init__(self, root: Path = DEFAULT_LAYOUT_ROOT) -> None:
        self.root = root

    def task_path(self, task: str) -> Path:
        if not re.fullmatch(r"[\w-]{1,100}", task, flags=re.UNICODE):
            raise ValueError("Task names must use 1–100 letters, digits, underscores or hyphens.")
        path = self.root / task
        if path.is_symlink():
            raise ValueError("Task directories cannot be symbolic links.")
        return path

    def tasks(self) -> tuple[str, ...]:
        if not self.root.exists():
            return ()
        return tuple(
            sorted(
                path.name
                for path in self.root.iterdir()
                if path.is_dir()
                and not path.is_symlink()
                and re.fullmatch(r"[\w-]{1,100}", path.name, flags=re.UNICODE)
            )
        )

    def create_task(self, task: str) -> None:
        self.task_path(task).mkdir(parents=True, exist_ok=True)

    def image_path(self, task: str, slot: str) -> Path:
        if slot not in REFERENCE_SLOTS:
            raise ValueError("Reference image IDs must be 01–10.")
        return self.task_path(task) / f"{slot}.png"

    def slots(self, task: str) -> tuple[str, ...]:
        return tuple(slot for slot in REFERENCE_SLOTS if self.image_path(task, slot).is_file())

    def load(self, task: str, slot: str) -> np.ndarray:
        return self.snapshot(task, slot)[0]

    def snapshot(self, task: str, slot: str) -> tuple[np.ndarray, dict[str, Any]]:
        """Decode and fingerprint the same file bytes, even during atomic replacement."""
        path = self.image_path(task, slot).resolve()
        content = path.read_bytes()
        with Image.open(io.BytesIO(content)) as image:
            pixels = np.array(image.convert("RGB"))
        return pixels, {
            "layout_id": slot,
            "reference_layout": {
                "task": task,
                "path": str(path),
                "sha256": hashlib.sha256(content).hexdigest(),
            },
        }

    def save(self, task: str, slot: str, image: np.ndarray) -> None:
        if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
            raise ValueError("Reference images must be uint8 RGB images.")
        destination = self.image_path(task, slot)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, suffix=".png", delete=False
        ) as file:
            temporary = Path(file.name)
        try:
            Image.fromarray(image).save(temporary, format="PNG")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
