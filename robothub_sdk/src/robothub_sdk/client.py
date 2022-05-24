from __future__ import annotations
import json
import sys
import urllib.request
import base64
import asyncio
from pathlib import Path
from typing import Dict, TYPE_CHECKING, TypedDict, List
from urllib.error import URLError, HTTPError

import depthai as dai
import paho_socket as mqtt_client
from paho.mqtt.client import MQTTMessage

from .constants import IS_INTERACTIVE, BROKER_SOCKET, STORAGE_DIR
from .detection import Detection
from .device import Device
from .error import RobotHubFatalException, RobotHubConnectionException, RobotHubPublishException
from .router import router
from .rest import Request, Response
from .stream import PublishedStream

if TYPE_CHECKING:
    from .app import App


class ReportedDevice(TypedDict):
    serialNumber: str
    state: str
    protocol: str
    platform: str
    boardName: str
    boardRev: str


class AgentClient:
    app_id: str
    app: App
    #: paho_socket.Client: Contains device identifiers on which the application can be executed
    client = None
    _requests: asyncio.Queue
    _video_streams: Dict[str, PublishedStream]
    _reported_devices: List[ReportedDevice]

    def __init__(self, app: App, broker_path=None):
        """
        This class is responsible for managing connection between Agent and App.

        Args:
            app (App): app instance
            broker_path (pathlib.Path, Optional): Path to Agent MQTT UNIX socket
        """

        if not app:
            raise RuntimeError("app argument is required")

        if broker_path is not None:
            parsed = Path(broker_path).resolve().absolute()
            if parsed.exists():
                broker_path = parsed

        if broker_path is None:
            primary_path = Path(BROKER_SOCKET).resolve().absolute()
            if primary_path.exists():
                broker_path = primary_path
            elif not IS_INTERACTIVE:
                error = "Unable to resolve broker path. Please provide `broker_path` parameter with socket path"
                raise RobotHubFatalException(error)

        self.app = app
        self.app_id = app.app_id
        self._requests = asyncio.Queue()
        self._video_streams = {}
        self._reported_devices = []
        if broker_path:
            self._connect(broker_path)

        asyncio.run_coroutine_threadsafe(self._process_requests(), app.loop)

    def __del__(self):
        self._disconnect()

    def reset(self):
        self._video_streams = {}
        self._reported_devices = []
        self.report_online()

    def add_video_stream(self, stream: PublishedStream):
        self._video_streams[stream.id] = stream

    # START MQTT

    def _on_connect(self, unused_client, unused_userdata, unused_flags, result):
        if result == 0:
            print("Connected to MQTT Broker!")
            self.client.on_message = self._on_message
        else:
            raise RobotHubConnectionException(
                f"Failed to connect - non-zero return code: {result}",
            )

        # We have to re-report all messages in case the broker has restarted and lost all the retained messages
        for reported_device in self._reported_devices:
            self._send_message(f"device/{self.app_id}", json.dumps(reported_device), retain=True)

        self.report_online()

        self.client.subscribe(f"{self.app_id}/#", 0)

    def _on_disconnect(self, unused_client, unused_userdata, result):
        print(f"Disconnected from MQTT Broker with result code {result}")

    def _on_message(self, unused_client, unused_userdata, msg: MQTTMessage):
        if msg.topic == f"{self.app_id}/configuration":
            try:
                configuration = json.loads(msg.payload.decode("utf-8"))
                old_configuration = self.app.config.clone()
                self.app.config.set_data(configuration)
                self.app.on_configuration(old_configuration)
            except Exception as e:
                print("Failed to parse configuration", e, file=sys.stderr)
        elif msg.topic == f"{self.app_id}/stream-enable":
            args = json.loads(msg.payload.decode())
            for stream in args:
                if stream in self._video_streams:
                    self._video_streams[stream].enable()
        elif msg.topic == f"{self.app_id}/stream-disable":
            args = json.loads(msg.payload.decode("utf-8"))
            for stream in args:
                if stream in self._video_streams:
                    self._video_streams[stream].disable()
        elif msg.topic == f"{self.app_id}/request":
            self.app.loop.call_soon_threadsafe(self._requests.put_nowait, msg)
        else:
            data = msg.payload.decode("utf-8")
            print(f"Received unhandled topic `{msg.topic}` with `{data}`")

    def _send_message(self, topic, msg, *args, **kwargs):
        if self.client is not None:
            self.client.publish(topic, msg, *args, **kwargs)
        elif not IS_INTERACTIVE:
            raise RobotHubPublishException(f"Failed to send message to topic {topic} - client not initialized")

    def _send_request(self, url, payload):
        req = urllib.request.Request(url)
        req.method = "POST"
        req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req, payload.encode("utf-8")):
                pass
        except HTTPError as e:
            # do something
            RobotHubPublishException(f"Failed to send message to URL {url} - non-zero return code: {e.code}")
            print("Error code: ", e.code)
        except URLError as e:
            # do something
            RobotHubPublishException(f"Failed to send message to URL {url} - reason: {e.reason}")
            print("Reason: ", e.reason)
        print(f"Send message to {url} with payload {payload}")

    def _connect(self, broker_path: Path):
        """
        Starts a connection to the Agent
        """

        if self.client:
            return

        self.client = mqtt_client.Client(client_id=self.app_id)
        self.client.will_set(f"offline/{self.app_id}", json.dumps({"appId": self.app_id}))
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.sock_connect_async(str(broker_path))
        self.client.reconnect_delay_set(min_delay=1, max_delay=16)
        self.client.loop_start()

    def _disconnect(self):
        """
        Terminates a connection to the Agent (if was started)
        """
        if self.client is not None:
            self.client.loop_stop()

    # END MQTT

    def report_device(self, device: Device):
        """
        Sends the device configuration to the Agent

        Args:
            device (dai.Device): Device object to report
        """
        info = device.device_info
        eeprom = device.eeprom
        # Announce device to the agent
        payload: ReportedDevice = {
            "serialNumber": info.getMxId(),
            "state": info.state.value,
            "protocol": info.desc.protocol.value,
            "platform": info.desc.platform.value,
            "boardName": eeprom.boardName,
            "boardRev": eeprom.boardRev,
        }
        self._reported_devices.append(payload)
        self._send_message(f"device/{self.app_id}", json.dumps(payload), retain=True)

    def report_online(self):
        """
        Sends app configuration to the Agent
        """
        self._send_message(
            f"online/{self.app_id}",
            json.dumps(
                {
                    "appId": self.app_id,
                    "interactive": {
                        "storage": STORAGE_DIR,
                    }
                    if IS_INTERACTIVE
                    else None,
                    "streams": [
                        {
                            "name": streamName,
                            "type": "video",
                            "fps": stream.rate,
                            "description": stream.description,
                            "enabled": stream.enabled,
                        }
                        for streamName, stream in self._video_streams.items()
                    ],
                }
            ),
            retain=True,
        )

    def send_detection(self, detection: Detection):
        """
        Sends the :class:`robothub_sdk.Detection` object to the Agent
        """
        payload = detection.get_payload()
        print("Detection payload", payload)
        self._send_message(f"detection/{self.app_id}", payload)

    def send_error(self, msg):
        """
        Sends the specified error message to the Agent
        """
        self._send_message(f"error/{self.app_id}", msg)

    def send_statistics(self, device_id: str, statistics: dai.SystemInformation):
        """
        Sends the usage metrics to the Agent
        """
        msg = json.dumps(
            {
                "serialNumber": device_id,
                "cssUsage": int(statistics.leonCssCpuUsage.average * 100),
                "mssUsage": int(statistics.leonMssCpuUsage.average * 100),
                "ddrMemFree": statistics.ddrMemoryUsage.remaining,
                "ddrMemTotal": statistics.ddrMemoryUsage.total,
                "cmxMemFree": statistics.cmxMemoryUsage.remaining,
                "cmxMemTotal": statistics.cmxMemoryUsage.total,
                "cssTemperature": int(statistics.chipTemperature.css),
                "mssTemperature": int(statistics.chipTemperature.mss),
                "upaTemperature": int(statistics.chipTemperature.upa),
                "dssTemperature": int(statistics.chipTemperature.dss),
                "temperature": int(statistics.chipTemperature.average),
            }
        )
        self._send_message(f"system/{self.app_id}", msg)

    def send_stream(self, stream: PublishedStream, frame: dai.ImgFrame):
        """
        Sends a preview frame to the Agent

        Args:
            stream (OutputStream): Name of the preview
            frame (dai.ImgFrame): Frame object to be sent as a preview (for encoded streams)
        """
        if stream.enabled:
            self._send_message(f"stream/{self.app_id}/{stream.id}", frame.getData().tobytes())

    def send_response(self, response: Response):
        request = response.request
        payload = response.payload
        msg = {
            "status": response.status,
            "headers": response.headers,
            "payload": payload,
        }

        if isinstance(payload, (bytes, memoryview)):
            payload = base64.b64encode(payload)
            msg["payload"] = payload.decode('ascii')
            msg["encoding"] = "base64"

        try:
            msg = json.dumps(msg)
            self._send_message(f"response/{self.app_id}/{request.id}", msg)
        except Exception as e:
            print("Failed to encode response to JSON", e)

    async def _process_requests(self):
        while True:
            msg = await self._requests.get()
            self._requests.task_done()
            data = json.loads(msg.payload.decode("utf-8"))
            request_id = data.get("id")
            payload = data.get("payload", None)
            if payload is str and data.get("encoding", None) == "base64":
                payload = base64.b64decode(payload)
            path = data.get("path")
            method = data.get("method", "GET")
            headers = data.get("headers", {})
            query = data.get("query", {})

            match = router.match(path, method=method)
            if match and match.target is not None:
                request = Request(request_id, path, method, match.params, headers, query, payload)
                try:
                    result = match.target(request)
                    if asyncio.iscoroutine(result):
                        result = await result
                    payload = result
                    status = 200
                    headers = {}
                    if isinstance(result, tuple):
                        if len(result) == 2:
                            payload, status = result
                        if len(result) == 3:
                            payload, status, headers = result
                    if not isinstance(result, Response):
                        result = Response(request, status, payload, headers)
                    self.send_response(result)
                except Exception as e:
                    result = Response(request, 500, str(e), headers)
                    self.send_response(result)
            else:
                request = Request(request_id, path, method, {}, headers, query, payload)
                result = Response(request, 404, None, headers)
                self.send_response(result)
