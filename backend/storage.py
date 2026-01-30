from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import UploadFile

from backend.settings import settings


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def new_assessment_dir() -> str:
    aid = str(uuid.uuid4())
    base = os.path.join(settings.STORAGE_DIR, aid)
    ensure_dir(base)
    return base


def save_upload(base_dir: str, key: str, f: Optional[UploadFile]) -> Optional[str]:
    if f is None:
        return None

    ext = ""
    if f.filename and "." in f.filename:
        ext = "." + f.filename.split(".")[-1].lower()

    out_path = os.path.join(base_dir, f"{key}{ext}")
    out_path = os.path.abspath(out_path)

    ensure_dir(base_dir)

    with open(out_path, "wb") as w:
        while True:
            chunk = f.file.read(1024 * 1024)
            if not chunk:
                break
            w.write(chunk)

    return out_path
