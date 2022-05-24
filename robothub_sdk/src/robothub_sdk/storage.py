import uuid
from pathlib import Path

from .constants import IS_INTERACTIVE, STORAGE_DIR


def store_data(data: bytes, suffix: str) -> str:
    filename = f"{str(uuid.uuid4())}.{suffix}"
    if IS_INTERACTIVE:
        return filename

    file_path = Path(STORAGE_DIR) / Path(filename)
    with file_path.open(mode="wb") as file:
        file.write(data)

    return filename
