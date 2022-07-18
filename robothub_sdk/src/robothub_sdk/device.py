from __future__ import annotations

import collections
import json
import ipaddress
from threading import Lock
from bisect import bisect_right
from functools import partial, cached_property
from pathlib import Path
from typing import Tuple, List, Union, Optional, Literal, Iterable, Any, Protocol, Dict, Deque

import depthai as dai
from depthai.node import (
    NeuralNetwork,
    ColorCamera,
    MonoCamera,
    SystemLogger,
    VideoEncoder,
    Script,
    ImageManip,
    StereoDepth,
    IMU,
    MobileNetSpatialDetectionNetwork,
    MobileNetDetectionNetwork,
    YoloSpatialDetectionNetwork,
    YoloDetectionNetwork,
    SPIOut,
)  # pylint: disable=import-error

from .resolutions import CameraResolution
from .stream import StreamType, Stream, InputStream


SupportedNeuralNetworks = Union[NeuralNetwork, MobileNetSpatialDetectionNetwork, MobileNetDetectionNetwork, YoloSpatialDetectionNetwork, YoloDetectionNetwork]


class SyncCallback(Protocol):
    def __call__(self, *args: dai.ADatatype) -> Any:
        pass


class SynchronizedStream:
    streams: Tuple[Stream]
    callback: SyncCallback
    rate: int
    last_completed_sequence: int

    _queue: Deque[Dict[int, dai.ADatatype]]
    _seq: Deque[int]
    _streams_len: int
    _receive_lock: Lock

    def __init__(self, streams: Iterable[Stream], callback: SyncCallback):
        self.streams = tuple(streams)
        self._streams_len = len(self.streams)
        self._receive_lock = Lock()
        assert self._streams_len > 1

        self.callback = callback
        self.last_completed_sequence = 0
        self.rate = 30

        for index, stream in enumerate(self.streams):
            stream.consume(partial(self._receive, index))
            self.rate = min(stream.rate, self.rate)

        self._queue = collections.deque(maxlen=self.rate)
        self._seq = collections.deque(maxlen=self.rate)

    def _receive(self, index: int, data: dai.ADatatype):
        with self._receive_lock:
            if isinstance(data, (dai.ImgFrame, dai.ImgDetections, dai.NNData)):
                i = data.getSequenceNum()
                if i <= self.last_completed_sequence:
                    return

                frames: Optional[Dict[int, dai.ADatatype]] = None
                if len(self._seq) == 0 or self._seq[-1] < i:
                    self._seq.append(i)
                    frames = {index: data}
                    self._queue.append(frames)
                else:
                    seq_index = bisect_right(self._seq, i)
                    if seq_index and self._seq[seq_index - 1] == i:
                        frames = self._queue[seq_index - 1]
                        frames[index] = data

                if frames and len(frames) == self._streams_len:
                    self.last_completed_sequence = i
                    args: List[dai.ADatatype] = [frames[i] for i in range(0, self._streams_len)]
                    self.callback(*args)
            elif len(self._queue) > 0:
                frames = self._queue[-1]
                frames[index] = data
                if len(frames) == self._streams_len:
                    self.last_completed_sequence = self._seq[-1]
                    args: List[dai.ADatatype] = [frames[i] for i in range(0, self._streams_len)]
                    self.callback(*args)


class DeviceConfiguration:
    name: str

    def __init__(self, name: Optional[str] = None):
        self.name = name or "<unknown>"

    def __repr__(self):
        return f"<DeviceConfiguration name={self.name!r}>"


class Device:
    class Streams:
        device: Device

        @cached_property
        def statistics(self) -> Stream:
            logger = self.device.create_system_logger()
            return self.create(logger, logger.out, stream_type=StreamType.STATISTICS, rate=int(logger.getRate()), description="System statistics")

        @cached_property
        def color_preview(self) -> Stream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.RGB)
            fps = int(camera.getFps())
            return self.create(
                camera,
                camera.preview,
                stream_type=StreamType.FRAME,
                rate=fps,
                description=f"Color camera preview {camera.getPreviewWidth()}x{camera.getPreviewHeight()}@{fps}",
                resolution=(camera.getPreviewWidth(), camera.getPreviewHeight()),
            )

        @cached_property
        def color_video(self) -> Stream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.RGB)
            fps = int(camera.getFps())
            return self.create(
                camera,
                camera.video,
                stream_type=StreamType.FRAME,
                rate=fps,
                description=f"Color camera video {camera.getVideoWidth()}x{camera.getVideoHeight()}@{fps}",
                resolution=(camera.getVideoWidth(), camera.getVideoHeight()),
            )

        @cached_property
        def color_still(self) -> Stream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.RGB)
            fps = int(camera.getFps())
            return self.create(
                camera,
                camera.still,
                stream_type=StreamType.FRAME,
                rate=fps,
                description=f"Color camera still pictures {camera.getStillWidth()}x{camera.getStillHeight()}",
                resolution=(camera.getStillWidth(), camera.getStillHeight()),
            )

        @cached_property
        def color_control(self) -> InputStream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.RGB)
            return self.create_input(camera, camera.inputControl, stream_type=StreamType.BINARY, description="Color camera control")

        @cached_property
        def color_configuration(self) -> InputStream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.RGB)
            return self.create_input(camera, camera.inputConfig, stream_type=StreamType.BINARY, description="Color camera control")

        @cached_property
        def mono_left_video(self) -> Stream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.LEFT)
            fps = int(camera.getFps())
            return self.create(
                camera,
                camera.out,
                stream_type=StreamType.FRAME,
                rate=fps,
                description=f"Left camera video {camera.getResolutionWidth()}x{camera.getResolutionHeight()}@{fps}",
                resolution=(camera.getResolutionWidth(), camera.getResolutionHeight()),
            )

        @cached_property
        def mono_right_video(self) -> Stream:
            camera = self.device.ensure_camera(dai.CameraBoardSocket.RIGHT)
            fps = int(camera.getFps())
            return self.create(
                camera,
                camera.out,
                stream_type=StreamType.FRAME,
                rate=fps,
                description=f"Right camera video {camera.getResolutionWidth()}x{camera.getResolutionHeight()}@{fps}",
                resolution=(camera.getResolutionWidth(), camera.getResolutionHeight()),
            )

        statistics: Stream
        color_preview: Stream
        color_video: Stream
        color_still: Stream

        mono_left_video: Stream
        mono_right_video: Stream

        _outputs: List[Stream]
        _inputs: List[InputStream]

        def __init__(self, device: Device):
            self.device = device
            self._outputs = []
            self._inputs = []

        def __setitem__(self, item, value):
            setattr(self, item, value)

        def __getitem__(self, item):
            return getattr(self, item)

        def synchronize(self, streams: Iterable[Stream], callback: SyncCallback) -> SynchronizedStream:
            return SynchronizedStream(streams, callback)

        def create(self, node: dai.Node, output_node: dai.Node.Output, stream_type: StreamType, rate: int = None, description: str = None, resolution: Tuple[int, int] = None):
            stream = Stream(self.device, node, output_node, stream_type, rate=rate, description=description, resolution=resolution)
            self._outputs.append(stream)
            return stream

        def create_input(self, node: dai.Node, input_node: dai.Node.Input, stream_type: StreamType, description: str = None):
            stream = InputStream(self.device, node, input_node, stream_type=stream_type, description=description)
            self._inputs.append(stream)
            return stream

        def inputs(self) -> List[InputStream]:
            return self._inputs

        def outputs(self) -> List[Stream]:
            return self._outputs

    # TODO rename to cameras
    class Nodes:
        color_camera: ColorCamera = None
        left_camera: MonoCamera = None
        right_camera: MonoCamera = None

    id: str
    name: str
    device_info: dai.DeviceInfo
    calibration: dai.CalibrationHandler
    eeprom: dai.EepromData
    cameras: List[dai.CameraBoardSocket]
    usb_speed = dai.UsbSpeed
    internal = dai.Device

    #: depthai.Pipeline: Ready to use requested pipeline. Can be passed to :obj:`depthai.Device` to start execution
    pipeline: dai.Pipeline

    nodes: Nodes
    streams: Streams

    configuration: DeviceConfiguration

    @property
    def name(self):
        return self.configuration.name

    def __init__(self, device_id: str, device_info: dai.DeviceInfo, device: dai.Device, configuration: Optional[DeviceConfiguration] = None):
        self.id = device_id
        self.device_info = device_info
        self.calibration = device.readCalibration()
        self.eeprom = self.calibration.getEepromData()
        self.cameras = device.getConnectedCameras()
        self.usb_speed = device.getUsbSpeed()
        self.internal = device

        #: depthai.Pipeline: Ready to use requested pipeline. Can be passed to :obj:`depthai.Device` to start execution
        self.pipeline = dai.Pipeline()

        if device_info.protocol in (dai.XLinkProtocol.X_LINK_USB_VSC, dai.XLinkProtocol.X_LINK_USB_CDC):
            self.pipeline.setXLinkChunkSize(0)

        self.nodes = Device.Nodes()
        self.streams = Device.Streams(self)
        self.streams.statistics.publish()
        self.configuration = configuration if configuration is not None else DeviceConfiguration(name=device_id)

    def create_nn(
        self,
        source: Stream,
        blob_path: Path,
        nn_family: Literal["YOLO", "mobilenet"] = None,
        config_path: Path = None,
        config: dict = None,
        input_size: Tuple[int, int] = None,
        depth: StereoDepth = None,
        full_fov=True,
        confidence: float = None,
        metadata: dict = None,
        roi: Tuple[float, float, float, float] = None,
        color_order: Literal["RGB", "BGR"] = "BGR",
    ) -> Tuple[SupportedNeuralNetworks, Stream, Stream]:
        assert source.output_node is not None
        assert source.type == StreamType.FRAME

        if config is None:
            config = {}
        if config_path is not None:
            if not config_path.exists():
                raise ValueError(f"Config path {config_path} does not exist!")
            with config_path.open() as file:
                raw_config = json.load(file)
                config.update(raw_config.get("nn_config", {}))

        if metadata is None:
            metadata = config.get("NN_specific_metadata", {})

        if nn_family is None:
            nn_family = config.get("NN_family", None)

        if input_size is None and "input_size" in config:
            input_size = tuple(map(int, config.get("input_size").split("x")))

        if confidence is None:
            confidence = metadata.get("confidence_threshold", config.get("confidence_threshold", 0.5))

        if nn_family == "mobilenet":
            nn = self.pipeline.createMobileNetSpatialDetectionNetwork() if depth is not None else self.pipeline.createMobileNetDetectionNetwork()
            nn.setConfidenceThreshold(confidence)
        elif nn_family == "YOLO":
            nn = self.pipeline.createYoloSpatialDetectionNetwork() if depth is not None else self.pipeline.createYoloDetectionNetwork()
            nn.setConfidenceThreshold(confidence)
            nn.setNumClasses(metadata["classes"])
            nn.setCoordinateSize(metadata["coordinates"])
            nn.setAnchors(metadata["anchors"])
            nn.setAnchorMasks(metadata["anchor_masks"])
            nn.setIouThreshold(metadata["iou_threshold"])
        else:
            # TODO use createSpatialLocationCalculator
            nn = self.pipeline.createNeuralNetwork()

        nn.setBlobPath(str(blob_path.resolve().absolute()))
        nn.setNumInferenceThreads(2)
        nn.input.setBlocking(False)
        nn.input.setQueueSize(1)

        # TODO we should also adjust resolution if needed
        if depth is not None:
            depth.depth.link(nn.inputDepth)

        if source.resolution != input_size or roi is not None:
            manip_nn = self.pipeline.createImageManip()
            manip_nn.inputImage.setQueueSize(1)
            manip_nn.inputImage.setBlocking(False)
            # The NN model expects BGR input. By default, ImageManip output type would be same as input (gray in this case)
            if input_size is not None:
                manip_nn.initialConfig.setResize(*input_size)
                frame_type = dai.RawImgFrame.Type.BGR888p if color_order == "BGR" else dai.RawImgFrame.Type.RGB888p
                manip_nn.initialConfig.setFrameType(frame_type)
                manip_nn.setMaxOutputFrameSize(input_size[0] * input_size[1] * 3)  # assume 3 channels UINT8 images

            # Set crop if set
            if roi is not None:
                # If full_fov = True we do not want to keep aspect ratio
                manip_nn.setKeepAspectRatio(not full_fov)
                manip_nn.setKeepAspectRatio(True)
                manip_nn.initialConfig.setCropRect(roi)
            # NN inputs
            manip_nn.out.link(nn.input)
            source.output_node.link(manip_nn.inputImage)
        else:
            source.output_node.link(nn.input)

        stream_out = self.streams.create(nn, nn.out, rate=source.rate, stream_type=StreamType.DETECTION, description="Neural network detections")
        stream_passthrough = self.streams.create(nn, nn.passthrough, rate=source.rate, stream_type=source.type, description=source.description)
        return nn, stream_out, stream_passthrough

    def create_script(
        self,
        content: str = None,
        inputs: Dict[str, Stream] = None,
        outputs: Dict[str, dai.Node.Input] = None,
        script_path: Path = None,
        name: str = None,
        processor: dai.ProcessorType = None,
    ) -> Script:
        # noinspection PyTypeChecker
        script: Script = self.pipeline.create(Script)
        if content:
            script.setScript(content, name=name)
        elif script_path:
            if not script_path.exists():
                raise RuntimeError(f"Script '{str(script_path)}' does not exists")
            script.setScriptPath(str(script_path))
        if processor:
            script.setProcessor(processor)

        if inputs is not None:
            for input_name, input_stream in inputs.items():
                script_input = script.inputs[input_name]
                input_stream.output_node.link(script_input)

        if outputs is not None:
            for output_name, output_stream in outputs.items():
                script.outputs[output_name].link(output_stream)

        return script

    def create_image_manipulator(self) -> Tuple[ImageManip, Stream]:
        manip = self.pipeline.createImageManip()
        return manip, self.streams.create(manip, manip.out, stream_type=StreamType.FRAME, rate=30)

    def ensure_camera(self, camera: dai.CameraBoardSocket = dai.CameraBoardSocket.RGB) -> Union[ColorCamera, MonoCamera]:
        if camera == dai.CameraBoardSocket.RGB and self.nodes.color_camera:
            return self.nodes.color_camera
        if camera == dai.CameraBoardSocket.LEFT and self.nodes.left_camera:
            return self.nodes.left_camera
        if camera == dai.CameraBoardSocket.RIGHT and self.nodes.right_camera:
            return self.nodes.right_camera

        return self.configure_camera(camera)

    def configure_camera(
        self,
        camera: dai.CameraBoardSocket = dai.CameraBoardSocket.RGB,
        fps=25,
        orientation: dai.CameraImageOrientation = None,
        res: CameraResolution = CameraResolution.MIN_RESOLUTION,
        color_order=dai.ColorCameraProperties.ColorOrder.BGR,
        preview_size: Tuple[int, int] = None,
        video_size: Tuple[int, int] = None,
        still_size: Tuple[int, int] = None,
        isp_scale: Tuple[int, int] = None,
    ) -> Union[ColorCamera, MonoCamera]:
        if camera == dai.CameraBoardSocket.RGB:
            cam_rgb = self.nodes.color_camera or self.pipeline.createColorCamera()
            self.nodes.color_camera = cam_rgb

            depthai_res = res.for_socket(camera)
            print(f"setting {camera} resolution to {depthai_res}")
            cam_rgb.setResolution(depthai_res)
            if isp_scale is not None:
                cam_rgb.setIspScale(*isp_scale)
            if preview_size is not None:
                cam_rgb.setPreviewSize(*preview_size)
            if video_size is not None:
                cam_rgb.setVideoSize(*video_size)
            if still_size is not None:
                cam_rgb.setStillSize(*still_size)
            cam_rgb.setInterleaved(False)
            cam_rgb.setColorOrder(color_order)
            cam_rgb.setFps(fps)
            if orientation is not None:
                cam_rgb.setImageOrientation(orientation)
            return cam_rgb
        if camera == dai.CameraBoardSocket.LEFT:
            mono_left = self.nodes.left_camera or self.pipeline.createMonoCamera()
            self.nodes.left_camera = mono_left
            mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
            if orientation is not None:
                mono_left.setImageOrientation(orientation)
            mono_left.setResolution(res.for_socket(camera))
            mono_left.setFps(fps)
            return mono_left
        if camera == dai.CameraBoardSocket.RIGHT:
            mono_right = self.nodes.right_camera or self.pipeline.createMonoCamera()
            self.nodes.right_camera = mono_right
            mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
            if orientation is not None:
                mono_right.setImageOrientation(orientation)
            mono_right.setResolution(res.for_socket(camera))
            mono_right.setFps(fps)
            return mono_right

        raise ValueError(f"Unsupported camera value {camera.name}")

    def __str__(self):
        ip_address = "-"
        try:
            ip_address = ipaddress.ip_address(self.internal.getDeviceInfo().getMxId())
        except ValueError:
            pass

        return f"""
    >>> ID: {self.id}
    >>> Cameras: {",".join([c.name for c in self.cameras])}
    >>> USB speed: {self.usb_speed.name}
    >>> IP Address: {ip_address}
    >>> BoardName: {self.eeprom.boardName}
    >>> BoardRev: {self.eeprom.boardRev}
    >>> Configuration: {self.configuration}
        """.strip(
            "\r\n"
        )

    def create_encoder(
        self, output: dai.Node.Output, fps=30, quality=100, profile: dai.VideoEncoderProperties.Profile = dai.VideoEncoderProperties.Profile.H264_MAIN
    ) -> VideoEncoder:
        """
        Creates H.264 / H.265 video encoder (:obj:`depthai.node.VideoEncoder` instance)
        """
        enc = self.pipeline.createVideoEncoder()
        enc.setDefaultProfilePreset(fps, profile)
        enc.setQuality(quality)
        enc.setKeyframeFrequency(fps)
        enc.input.setBlocking(False)
        enc.input.setQueueSize(1)
        output.link(enc.input)
        return enc

    def create_imu(self, sensors: List[dai.IMUSensor], rate=50) -> IMU:
        imu = self.pipeline.createIMU()
        imu.enableIMUSensor(sensors, rate)
        imu.setBatchReportThreshold(1)
        imu.setMaxBatchReports(10)
        return imu

    def create_stereo_depth(self, output_size: Tuple[int, int] = None, confidence_threshold: int = None) -> StereoDepth:
        stereo = self.pipeline.createStereoDepth()
        stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
        stereo.setLeftRightCheck(True)
        self.streams.mono_left_video.output_node.link(stereo.left)
        self.streams.mono_right_video.output_node.link(stereo.right)
        if output_size is not None:
            stereo.setOutputSize(*output_size)
        if confidence_threshold is not None:
            stereo.initialConfig.setConfidenceThreshold(confidence_threshold)
        return stereo

    def create_spi_out(self, bus_id: int = None, stream_name: str = None) -> SPIOut:
        spi_out = self.pipeline.createSPIOut()
        spi_out.input.setBlocking(False)
        spi_out.input.setQueueSize(1)
        if bus_id is not None:
            spi_out.setBusId(bus_id)

        if stream_name:
            spi_out.setStreamName(stream_name)

        return spi_out

    def create_system_logger(self) -> SystemLogger:
        system_logger = self.pipeline.createSystemLogger()
        system_logger.setRate(1)
        return system_logger
