from __future__ import annotations
import enum
import time
import uuid
from collections import deque
from functools import cached_property
from typing import TYPE_CHECKING, List, Callable, Any, ClassVar, Optional, Final, Tuple, Deque

import depthai as dai
from depthai.node import XLinkOut, XLinkIn  # pylint: disable=import-error

if TYPE_CHECKING:
    from .device import Device


class StreamType(enum.Enum):
    ENCODED = "encoded"
    FRAME = "frame"
    STATISTICS = "statistics"
    DETECTION = "detection"
    BINARY = "binary"
    IMU = "imu"


PUBLISHABLE_TYPES: Final = [StreamType.FRAME, StreamType.ENCODED, StreamType.STATISTICS]


class RateCounter:
    _samples: Deque[float]

    def __init__(self, sample_size=100):
        self._samples = deque(maxlen=sample_size)

    def record(self, now: float, n=1) -> None:
        if n == 1:
            self._samples.append(now)
        else:
            for i in range(0, n):
                self._samples.append(now)

    def value(self) -> float:
        if len(self._samples) > 1:
            first = self._samples[0]
            last = self._samples[-1]
            return len(self._samples) / (last - first)
        return 0


class Stream:
    device: Device
    type: StreamType
    node: dai.Node
    output_node: dai.Node.Output
    rate: Optional[int]
    description: Optional[str]
    is_published: bool
    current_rate: float
    last_value: Optional[dai.ADatatype]
    last_timestamp: float
    published: Optional[PublishedStream]
    resolution: Tuple[int, int]
    _output_queue_name: Optional[str]
    _xlink_output: Optional[XLinkOut]
    _callbacks: List[Callable[[dai.ADatatype], Any]]
    _rate_counter: RateCounter

    _queue_counter: ClassVar[int] = 0

    @classmethod
    def _gen_output_queue_name(cls) -> str:
        cls._queue_counter += 1
        return f"_out_{cls._queue_counter}"

    @cached_property
    def output_queue_name(self) -> str:
        if self._output_queue_name is None:
            self._output_queue_name = Stream._gen_output_queue_name()
        return self._output_queue_name

    @property
    def has_data(self) -> bool:
        return self.last_value is not None

    @property
    def is_consumed(self) -> bool:
        return self._xlink_output is not None

    @property
    def is_published(self) -> bool:
        return self.published is not None

    @property
    def current_rate(self) -> float:
        return self._rate_counter.value()

    def __init__(
        self,
        device: Device,
        node: dai.Node,
        output_node: dai.Node.Output,
        stream_type: StreamType,
        rate: int = None,
        description: str = None,
        output_queue_name: str = None,
        resolution: Tuple[int, int] = None,
    ):
        self.device = device
        self.node = node
        self.output_node = output_node
        self.type = stream_type
        self.rate = rate
        self.description = description
        self._output_queue_name = output_queue_name or Stream._gen_output_queue_name()
        self._xlink_output = None
        self.last_value = None
        self.last_timestamp = 0
        self.published = None
        self.resolution = resolution if resolution else (0, 0)
        self._callbacks = []
        self._rate_counter = RateCounter()

    def consume(self, callback: Optional[Callable[[dai.ADatatype], Any]] = None) -> None:
        self.create_output()
        if callback:
            self._callbacks.append(callback)

    def create_output(self) -> XLinkOut:
        if self._xlink_output is None:
            self._xlink_output = self.device.pipeline.createXLinkOut()
            self._xlink_output.setStreamName(self.output_queue_name)
            self.output_node.link(self._xlink_output.input)
        return self._xlink_output

    def publish(self, description: str = None) -> PublishedStream:
        if self.type not in PUBLISHABLE_TYPES:
            raise RuntimeError(f"Publishing stream type {self.type.name} is not supported")
        if self.published:
            return self.published

        if description is None:
            description = self.description

        self.published = PublishedStream(self.device, self.type, source=self, rate=self.rate, description=description)
        return self.published

    def queue_callback(self, data: dai.ADatatype) -> None:
        now = time.monotonic()
        self.last_value = data
        self.last_timestamp = now
        if isinstance(data, dai.IMUData):
            self._rate_counter.record(now, len(data.packets))
        else:
            self._rate_counter.record(now)
        for callback in self._callbacks:
            callback(data)


class InputStream:
    device: Device
    type: StreamType
    node: dai.Node
    input_node: dai.Node.Input
    _input_queue_name: str
    _xlink_input: XLinkIn
    _queue: Optional[dai.DataInputQueue]
    description: str

    _queue_counter: ClassVar[int] = 0

    @classmethod
    def _gen_input_queue_name(cls) -> str:
        cls._queue_counter += 1
        return f"_in_{cls._queue_counter}"

    @cached_property
    def input_queue_name(self) -> str:
        if self._input_queue_name is None:
            self._input_queue_name = InputStream._gen_input_queue_name()
        return self._input_queue_name

    def __init__(
        self,
        device: Device,
        node: dai.Node,
        input_node: dai.Node.Input,
        stream_type: StreamType,
        description: str = None,
    ):
        self.device = device
        self.node = node
        self.input_node = input_node
        self.type = stream_type
        self.description = description
        self._input_queue_name = InputStream._gen_input_queue_name()
        self._xlink_input = device.pipeline.createXLinkIn()
        self._xlink_input.setStreamName(self._input_queue_name)
        self._xlink_input.out.link(self.input_node)
        self._queue = None

    def send(self, data: dai.ADatatype):
        assert self._queue
        self._queue.send(data)

    def register_queue(self, queue: dai.DataInputQueue):
        assert self._xlink_input
        self._queue = queue


class PublishedStream:
    id: str
    device: Device
    type: StreamType
    rate: int
    description: str
    enabled: bool
    output_queue_name: str
    _xlink_output: XLinkOut
    source: Stream

    def __init__(
        self,
        device: Device,
        stream_type: StreamType,
        source: Stream,
        rate=1,
        description: str = None,
    ):
        self.id = str(uuid.uuid4())
        self.device = device
        self.type = stream_type
        self.rate = rate
        self.description = description
        self.enabled = False
        self.source = source
        if self.type == StreamType.FRAME:
            self.type = StreamType.ENCODED
            self.output_queue_name = f"{source.output_queue_name}-published"
            self._xlink_output = self.device.pipeline.createXLinkOut()
            self._xlink_output.input.setBlocking(False)
            self._xlink_output.input.setQueueSize(2)
            self._xlink_output.setStreamName(self.output_queue_name)
            encoder = self.device.create_encoder(source.output_node, self.rate)
            encoder.bitstream.link(self._xlink_output.input)
        else:
            self._xlink_output = source.create_output()
            self.output_queue_name = self._xlink_output.getStreamName()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False
