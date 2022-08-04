import uuid
from pathlib import Path

from .constants import IS_INTERACTIVE, STORAGE_DIR


def store_data(data: bytes, suffix: str, customName: str = None) -> str:
    name = customName
    if name is None:
        name = str(uuid.uuid4())

    filename = f"{name}.{suffix}"
    if IS_INTERACTIVE:
        return filename

    file_path = Path(STORAGE_DIR) / Path(filename)
    with file_path.open(mode="wb") as file:
        file.write(data)

    return filename
