from __future__ import annotations
import json
from typing import Dict, Union, Any, Optional, Mapping


class Request:
    id: str
    path: str
    method: str
    headers: Dict[str, str]
    params: Mapping[str, Any]
    query: Mapping[str, str]
    payload: Any

    def __init__(self, request_id: str, path: str, method: str, params: Mapping[str, Any], headers: Dict[str, str], query: Dict[str, str], payload: Any = None):
        self.id = request_id
        self.path = path
        self.method = method
        self.params = params
        self.headers = headers
        self.query = query
        self.payload = payload


class Response:
    headers: Dict[str, str]
    payload: Optional[Union[str, bytes]]
    request: Request
    status: int

    def __init__(self, request: Request, status: int = None, payload: Any = None, headers: Dict[str, str] = None):
        self.request = request
        self.status = status
        self.payload = None
        self.headers = headers if headers else {}
        self.set_payload(payload)

    def add_header(self, name: str, value: str) -> None:
        self.headers[name.title()] = value

    def set_payload(self, payload: Any) -> None:
        if payload is None:
            self.payload = None
        elif isinstance(payload, (str, bytes, memoryview)):
            self.payload = payload
        elif isinstance(payload, (list, dict)):
            self.headers["content-type"] = "application/json"
            self.payload = json.dumps(payload)
        else:
            raise TypeError("Payload must be serializable to JSON")
