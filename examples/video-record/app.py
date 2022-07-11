import io
from collections import deque
from fractions import Fraction
from typing import List, Deque, Tuple
import time
from datetime import timedelta

import depthai as dai
import av

from robothub_sdk import (
    App,
    CameraResolution,
    StreamType,
    Config,
)
from robothub_sdk.device import Device

DETECTION_INTERVAL = timedelta(minutes=15).total_seconds()
video_retention = timedelta(minutes=2)


def save_video(video_loop, fps: int) -> bytes:
    snapshot = video_loop.copy()

    # TODO: for larger video this memory copy is not practical, we should implement our own File like stream reading mechanism
    input_file = io.BytesIO(b"".join([frame.data for frame in snapshot]))
    mp4_file = io.BytesIO()
    with av.open(mp4_file, "w", format="mp4") as output_container, av.open(input_file, "r", format="h264") as input_container:
        input_stream = input_container.streams[0]
        output_stream = output_container.add_stream(template=input_stream, rate=fps)
        output_stream.time_base = input_stream.time_base
        frame_time = (1 / fps) * input_stream.time_base.denominator
        for i, packet in enumerate(input_container.demux(input_stream)):
            packet.dts = i * frame_time
            packet.pts = i * frame_time
            packet.stream = output_stream
            output_container.mux_one(packet)
    mp4_file.flush()
    return mp4_file.getvalue()


class VideoRecord(App):
    video_fps: int
    cameras: List[Tuple[Device, Deque]]
    next_detection = 0

    def __init__(self):
        super().__init__()
        self.video_fps = 30
        self.cameras = []
        self.max_video_retention = timedelta(seconds=90)

    def on_initialize(self, unused_devices: List[dai.DeviceInfo]):
        self.cameras.clear()
        self.config.add_defaults(send_video=False, send_video_interval=DETECTION_INTERVAL)
        self.next_detection = 0

    def on_configuration(self, old_configuration: Config):
        print("Configuration update", self.config.values())
        if not self.config.send_video:
            self.next_detection = 0

        if self.config.send_video and self.config.send_video_interval != old_configuration.send_video_interval:
            self.next_detection = time.monotonic() + self.config.send_video_interval

    def on_setup(self, device):
        fps = self.video_fps
        backlog_size = round(self.max_video_retention.total_seconds() * fps)
        video_loop = deque(maxlen=backlog_size)
        self.cameras.append((device, video_loop))

        camera = device.configure_camera(dai.CameraBoardSocket.RGB, res=CameraResolution.MAX_RESOLUTION, fps=fps)
        scale_to_720p = Fraction(720, camera.getIspHeight())
        if scale_to_720p < 1:
            camera.setIspScale(scale_to_720p.numerator, scale_to_720p.denominator)

        encoder = device.create_encoder(
            device.streams.color_video.output_node,
            fps,
            profile=dai.VideoEncoderProperties.Profile.H264_BASELINE,
        )
        encoder.setBitrate(1500 * 1000)
        encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)

        encoder_stream = device.streams.create(encoder, encoder.bitstream, stream_type=StreamType.ENCODED, rate=fps)
        encoder_stream.consume(lambda frame: video_loop.append(frame.getData()))
        encoder_stream.publish(description=f"Main camera on {device.name} 720p@{fps}")

    def on_update(self):
        if self.config.send_video and self.next_detection < time.monotonic():
            for device, video_loop in self.cameras:
                if len(video_loop) == 0:
                    continue
                self.send_detection(f"Video from device {device.name}", video=save_video(video_loop, self.video_fps))

            self.next_detection = time.monotonic() + self.config.send_video_interval


app = VideoRecord()
app.run()
