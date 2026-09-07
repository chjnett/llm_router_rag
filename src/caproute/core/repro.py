from __future__ import annotations

import os
import platform
import random
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch = sys.modules.get("torch")
    if torch is not None:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def git_metadata(root: str | Path) -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            return subprocess.run(
                ["git", "-C", str(root), *args], capture_output=True, text=True,
                timeout=10, check=True,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
    commit = run("rev-parse", "HEAD")
    status = run("status", "--porcelain")
    return {"commit": commit, "dirty": bool(status) if status is not None else None}


def environment_metadata() -> dict[str, Any]:
    result: dict[str, Any] = {
        "os": platform.platform(),
        "python": sys.version,
        "cpu": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
    }
    try:
        import pymupdf
        result["pymupdf"] = getattr(pymupdf, "version", None)
    except ImportError:
        result["pymupdf"] = None
    try:
        result["torch"] = version("torch")
    except PackageNotFoundError:
        result["torch"] = None
    try:
        fields = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip().splitlines()[0].split(",")
        result["gpu"] = fields[0].strip()
        result["vram_mib"] = float(fields[1].strip())
        result["nvidia_driver"] = fields[2].strip()
    except (OSError, subprocess.SubprocessError, IndexError, ValueError):
        result["gpu"] = None
    return result
