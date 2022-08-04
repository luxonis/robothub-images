import uuid
from datetime import datetime
from typing import Optional, List, Any

from . import json


class Detection:
    id: uuid.UUID
    title: str
    frames: Optional[List[str]]
    video: Optional[str]
    files: Optional[List[str]]
    tags: Optional[List[str]]
    data: Any
    created_at: datetime

    def __init__(self, title: str, tags: List[str] = None, data=None, frames: List[str] = None, video: str = None, files: List[str] = None, detection_id: uuid.UUID = None):
        self.id = detection_id or uuid.uuid4()
        self.title = title
        self.tags = tags
        self.data = data
        self.frames = frames
        self.video = video
        self.files = files
        self.created_at = datetime.now()

    def get_payload(self) -> str:
        payload = {"id": self.id, "title": self.title, "createdAt": self.created_at}
        if self.tags:
            payload["tags"] = self.tags
        if self.data:
            payload["data"] = self.data
        if self.frames:
            payload["frames"] = self.frames
        if self.video:
            payload["video"] = self.video
        if self.files:
            payload["files"] = self.files

        return json.dumps(payload)

    def __str__(self):
        return f"Detection<{self.title} {str(self.id)} - {self.created_at.strftime('%H:%M:%S.%f')} (frames: {len(self.frames) if self.frames is not None else '<none>'})>"

    def __repr__(self):
        return self.__str__()
