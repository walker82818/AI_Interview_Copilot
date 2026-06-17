import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from src.core.config import settings


def ensure_upload_dir(subdir: str = "") -> Path:
    base = Path(settings.upload_dir) / subdir
    base.mkdir(parents=True, exist_ok=True)
    return base


async def save_upload_file(file: UploadFile, subdir: str = "") -> tuple[str, Path]:
    upload_dir = ensure_upload_dir(subdir)
    suffix = Path(file.filename or "upload").suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = upload_dir / stored_name

    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file.filename or stored_name, dest


def delete_file(path: str | Path) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
