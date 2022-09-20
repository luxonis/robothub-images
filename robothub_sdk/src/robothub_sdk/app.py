import atexit
import os
import signal
import uuid
import time
import warnings
import traceback
from contextlib import ExitStack
from datetime import timedelta
from functools import partial
from pathlib import Path
from threading import Thread
from typing import List, Tuple, Generator, Optional, Any, Literal, Dict, Union
import depthai as dai
import asyncio

from .client import AgentClient
from .config import Config
from .constants import IS_INTERACTIVE, CONFIG_FILE
from .detection import Detection
from .device import Device, DeviceConfiguration
from .error import RobotHubFatalException
from .storage import store_data
from .stream import StreamType
from . import json

STREAM_STUCK_TIMEOUT = timedelta(seconds=60).total_seconds()


class App:
    running: bool
    fail_counter: int
    #: str: unique identifier of the application
    app_id: str
    #: str: Contains device identifier on which the application can be executed
    device_ids: List[str]
    #: Config: Contains config supplied by Agent
    config: Config
    devices: List[Device]
    loop: asyncio.AbstractEventLoop

    _loop_thread: Thread
    _run_without_devices: bool
    _comm: AgentClient
    _device_configuration: Dict[str, DeviceConfiguration]
    _min_update_rate: int
    _config_path: Path
    _running: Optional[Generator[bool, None, None]]

    def on_initialize(self, devices: List[dai.DeviceInfo]):
        pass

    def on_exit(self):
        pass

    def on_configuration(self, old_configuration: Config):
        pass

    def on_setup(self, device: Device):
        pass

    def on_update(self):
        pass

    @property
    def device_configuration(self):
        return self._device_configuration

    @device_configuration.setter
    def device_configuration(self, value: Dict[str, DeviceConfiguration]):
        self._device_configuration = value
        print("Device configuration updated", value)
        for device in self.devices:
            configuration = value.get(device.id, None)
            if configuration is not None:
                device.configuration = configuration

    def __init__(self, config_path: Path = Path(CONFIG_FILE), run_without_devices: bool = False, app_id: str = None):
        self.running = False
        self.fail_counter = 0
        #: str: unique identifier of the application
        self.app_id = app_id or os.environ.get("APP_ID", str(uuid.uuid4()))
        #: str: Contains device identifier on which the application can be executed
        self.device_ids = [device_id for device_id in os.environ.get("APP_DEVICES", "").split(",") if device_id]
        #: Config: Contains config supplied by Agent
        self.config = Config()
        self.devices: List[Device] = []
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self._loop_thread = Thread(target=self._background_loop, daemon=True)
        self._loop_thread.start()

        self._running = None
        self._comm = AgentClient(self)
        self._device_configuration = {}
        self._min_update_rate = 1
        self._config_path = config_path.resolve().absolute()
        self._run_without_devices = run_without_devices

        atexit.register(self._process_exit)
        for sig_no in (signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
            signal.signal(sig_no, self._signal_handler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def send_poweroff(self):
        self._comm.send_poweroff()

    def send_detection(
        self, title: str, tags: List[str] = None, data: Any = None, frames: List[Tuple[dai.ImgFrame, Literal["jpeg", "raw"]]] = None, video: Union[bytes, memoryview] = None, files: List[Tuple[Union[bytes, memoryview], str, str]] = None
    ) -> Detection:
        saved_frames = []
        if frames is not None and len(frames) > 0:
            for (img_frame, suffix) in frames:
                filename = store_data(img_frame.getData().tobytes(), suffix)
                saved_frames.append(filename)

        saved_video = None
        if video is not None:
            saved_video = store_data(video, "mp4")

        saved_files = []
        if files is not None and len(files) > 0:
            for (raw_bytes, name, suffix) in files:
                filename = store_data(raw_bytes, suffix, name)
                saved_files.append(filename)

        detection = Detection(title, tags, data=data, frames=saved_frames, video=saved_video, files=saved_files)
        self._comm.send_detection(detection)
        return detection

    def restart(self):
        if self._running:
            self._running = None

        devices = self.devices.copy()
        self.devices.clear()
        if self._comm is not None:
            self._comm.reset()

        for device in devices:
            device.internal.close()

    def stop(self):
        atexit.unregister(self._process_exit)
        signal.signal(signal.SIGINT, signal.default_int_handler)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGQUIT, signal.SIG_DFL)

        self.running = False
        self.loop.stop()
        self._loop_thread.join(timeout=3)
        self.restart()

    def _start(self) -> Generator[bool, None, None]:
        self.running = True
        self.fail_counter = 0
        while self.running:
            try:
                if self._run_without_devices:
                    yield from self._run_empty_loop()
                else:
                    devices = self._find_devices()
                    if devices:
                        yield from self._run_pipelines(devices)
                    time.sleep(1)
            except RobotHubFatalException as e:
                self._comm.send_error(f"Application cannot start: {e}")
                self.stop()
                print(e, "Application cannot start")
            except (GeneratorExit, SystemExit):
                raise
            except BaseException as e:
                traceback.print_exc()
                self.fail_counter += 1
                self._comm.send_error(f"Application failed to start: {e}")
                if self.fail_counter < 10:
                    print(e, type(e), "Restarting...")
                    self.restart()
                    time.sleep(1)
                else:
                    print(e, "Application failed too many times, terminating...")
                    self.stop()

    def update(self) -> bool:
        if self._running is None:
            self._running = self._start()

        try:
            return next(self._running)
        except StopIteration:
            return False

    def run(self) -> None:
        if not self._run_without_devices:
            if IS_INTERACTIVE and not self.device_ids:
                print("Running in interactive mode and getting all devices")
                devices = dai.Device.getAllAvailableDevices()
                for device in devices:
                    mx_id = device.getMxId()
                    if mx_id == "<error>":
                        continue
                    self.device_ids.append(mx_id)

            if not self.device_ids:
                raise RobotHubFatalException("Devices not specified")

        if self._config_path.exists():
            with self._config_path.open(encoding="utf-8") as file:
                old_configuration = self.config.clone()
                self.config.set_data(json.load(file))
                self.on_configuration(old_configuration)
        else:
            error = "Unable to resolve initial config file location - configuration not loaded. This issue can be solved by providing `config_path` param"
            if not IS_INTERACTIVE:
                warnings.warn(error)

        self.running = True
        self._running = self._start()

        while self.running:
            update_start = time.monotonic()
            self.update()
            update_duration = time.monotonic() - update_start
            sleep_time = self._min_update_rate - update_duration
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _background_loop(self):
        self.loop.run_forever()

    def _signal_handler(self, unused_signum, unused_frame):
        atexit.unregister(self._process_exit)
        self._process_exit()

    def _process_exit(self):
        self.stop()
        self.on_exit()

    def _find_devices(self) -> List[dai.DeviceInfo]:
        devices: Dict[str, dai.DeviceInfo] = {}
        missing_devices = True

        # TODO: add configurable timeout
        while missing_devices:
            missing_devices = False
            available_devices: List[dai.DeviceInfo] = dai.Device.getAllAvailableDevices()
            for device in available_devices:
                mx_id = device.getMxId()
                if mx_id in self.device_ids:
                    devices[mx_id] = device

            for device_id in self.device_ids:
                if devices.get(device_id, None) is None:
                    missing_devices = True
                    msg = f"Device {device_id} not found"
                    print(msg)
                    self._comm.send_error(msg)
            if missing_devices:
                time.sleep(0.5)

        return list(devices.values())

    def _run_empty_loop(self) -> Generator[bool, None, None]:
        self.on_initialize([])
        self._comm.report_online()
        while self.running:
            self.on_update()
            yield True

    def _run_pipelines(self, devices: List[dai.DeviceInfo]) -> Generator[bool, None, None]:
        for device in self.devices:
            device.internal.close()
        self.devices.clear()

        openvino_version = dai.OpenVINO.Version.VERSION_2021_4
        usb2_mode = False
        self.on_initialize(devices)

        with ExitStack() as stack:
            for device_info in devices:
                dai_device: dai.Device = stack.enter_context(dai.Device(openvino_version, device_info, usb2_mode))
                device_id = dai_device.getMxId()
                configuration = self._device_configuration.get(device_id, None)
                device = Device(device_id, device_info, dai_device, configuration)

                print(f"=== Connected to: {device_id}")
                print(str(device))
                self.on_setup(device)

                dai_device.startPipeline(device.pipeline)

                dai_device.setLogLevel(dai.LogLevel.WARN)
                dai_device.setLogOutputLevel(dai.LogLevel.WARN)

                self._comm.report_device(device)
                for stream in device.streams.inputs():
                    queue = dai_device.getInputQueue(stream.input_queue_name, maxSize=1, blocking=False)
                    stream.register_queue(queue)

                for stream in device.streams.outputs():
                    consumed_queue = dai_device.getOutputQueue(stream.output_queue_name, maxSize=2, blocking=False) if stream.is_consumed else None
                    published_queue = None
                    if stream.is_published:
                        published_queue = consumed_queue
                        if stream.published.output_queue_name != stream.output_queue_name:
                            published_queue = dai_device.getOutputQueue(stream.published.output_queue_name, maxSize=2, blocking=False)

                    if published_queue:
                        if stream.published.type == StreamType.ENCODED:
                            self._comm.add_video_stream(stream.published)
                            published_queue.addCallback(partial(self._comm.send_stream, stream.published))
                        elif stream.published.type == StreamType.STATISTICS:
                            published_queue.addCallback(partial(self._comm.send_statistics, device_id))
                        else:
                            raise RobotHubFatalException("Published stream is not supported")

                    if consumed_queue:
                        if stream.rate > 0:
                            self._min_update_rate = min(self._min_update_rate, 1 / stream.rate)
                        consumed_queue.addCallback(stream.queue_callback)

                self.devices.append(device)

            self._comm.report_online()
            last_run = 0
            while self.running:
                had_items = False
                now = time.monotonic()
                print(f'Adding last value to queue at time {now}')

                for device in self.devices:
                    last_item = 0
                    for stream in device.streams.outputs():
                        last_item = max(last_item, stream.last_timestamp)
                        if stream.last_timestamp > last_run:
                            had_items = True
                    if last_item > 0 and now - last_item > STREAM_STUCK_TIMEOUT:
                        # NOTE(michal) temporary measure before we figure out how to fix this
                        raise RuntimeError(f"Device {device.id} / {device.name} stuck. Last message received {now - last_item}s ago.")

                if had_items:
                    self.on_update()
                last_run = now
                yield had_items
