"""The recorded identity of one attempt in the ten-layout evaluation protocol."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def rollout_identity(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate metadata before creating runtime resources; never read image files.

    The reference task names a gallery, not the canonical evaluation task or the
    policy prompt. Ordinary rollouts carry no formal layout/repeat identity.
    """
    mode = run.get("experiment_mode", False)
    if not isinstance(mode, bool):
        raise ValueError("run.experiment_mode must be a boolean")
    if not mode:
        return {
            "experiment_mode": False,
            "layout_id": "",
            "repeat_id": None,
            "reference_layout": None,
        }
    layout_id = run.get("layout_id")
    if not isinstance(layout_id, str) or not re.fullmatch(r"0[1-9]|10", layout_id):
        raise ValueError("experiment rollout requires run.layout_id '01' through '10'")
    repeat_id = run.get("repeat_id")
    if type(repeat_id) is not int or not 1 <= repeat_id <= 3:
        raise ValueError("experiment rollout requires integer run.repeat_id 1 through 3")
    reference = run.get("reference_layout")
    if not isinstance(reference, Mapping):
        raise ValueError("experiment rollout requires run.reference_layout (task, path, sha256)")
    task, path, digest = (reference.get(key) for key in ("task", "path", "sha256"))
    if not isinstance(task, str) or not re.fullmatch(r"[\w-]{1,100}", task):
        raise ValueError("reference_layout.task must be a reference gallery name")
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ValueError("reference_layout.path must be an absolute image path")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("reference_layout.sha256 must identify the selected image bytes")
    return {
        "experiment_mode": True,
        "layout_id": layout_id,
        "repeat_id": repeat_id,
        "reference_layout": {"task": task, "path": path, "sha256": digest},
    }
