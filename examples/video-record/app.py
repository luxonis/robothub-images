import io
from collections import deque
from fractions import Fraction
from typing import List, Deque, Tuple, Literal
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


def save_video(video_loop, fps: int, video_format: Literal["mjpeg", "h264", "h265"]) -> bytes:
    snapshot = video_loop.copy()

    mp4_file = io.BytesIO()

    if video_format == "mjpeg":
        with av.open(mp4_file, "w", format="mp4") as output_container:
            output_stream = output_container.add_stream("mjpeg", rate=fps)
            output_stream.time_base = Fraction(1, 1000 * 1000)
            output_stream.pix_fmt = "yuvj420p"
            frame_time = (1 / fps) * output_stream.time_base.denominator
            for i, frame in enumerate(snapshot):
                packet = av.Packet(frame)
                packet.dts = i * frame_time
                packet.pts = i * frame_time
                packet.stream = output_stream
                output_container.mux_one(packet)
    else:
        # TODO: for larger video this memory copy is not practical, we should implement our own File like stream reading mechanism
        input_file = io.BytesIO(b"".join([frame.data for frame in snapshot]))

        # NOTE(michal): we parse the bitstream because the first frame might not be a key frame, which results in a corrupted video file
        with av.open(mp4_file, "w", format="mp4") as output_container, av.open(input_file, "r", format=video_format) as input_container:
            input_stream = input_container.streams[0]
            output_stream = output_container.add_stream(template=input_stream, rate=fps)
            output_stream.time_base = input_stream.time_base
            frame_time = (1 / fps) * input_stream.time_base.denominator
            for i, packet in enumerate(input_container.demux(input_stream)):
                packet.dts = i * frame_time
                packet.pts = i * frame_time
                packet.stream = output_stream
                output_container.mux_one(packet)
    return mp4_file.getvalue()


class VideoRecord(App):
    cameras: List[Tuple[Device, Deque]]
    next_detection = 0

    def __init__(self):
        super().__init__()
        self.cameras = []

    def on_initialize(self, unused_devices: List[dai.DeviceInfo]):
        self.cameras.clear()
        self.config.add_defaults(
            send_video=False,
            send_video_interval=DETECTION_INTERVAL,
            video_fps=30,
            video_format="h264",
            video_retention_seconds=90,
        )
        self.next_detection = 0

    def on_configuration(self, old_configuration: Config):
        print("Configuration update", self.config.values())
        if not self.config.send_video:
            self.next_detection = 0

        if self.config.send_video and self.config.send_video_interval != old_configuration.send_video_interval:
            self.next_detection = time.monotonic() + self.config.send_video_interval

        if (
            self.config.video_fps != old_configuration.video_fps
            or self.config.video_format != old_configuration.video_format
            or self.config.video_retention_seconds != old_configuration.video_retention_seconds
        ):
            self.restart()

    def on_setup(self, device):
        fps = self.config.video_fps
        video_format = self.config.video_format
        backlog_size = round(self.config.video_retention_seconds * fps)
        video_loop = deque(maxlen=backlog_size)
        self.cameras.append((device, video_loop))

        camera = device.configure_camera(dai.CameraBoardSocket.RGB, res=CameraResolution.MAX_RESOLUTION, fps=fps)
        scale_to_720p = Fraction(720, camera.getIspHeight())
        if scale_to_720p < 1:
            camera.setIspScale(scale_to_720p.numerator, scale_to_720p.denominator)

        encoder = None
        if video_format == "mjpeg":
            encoder = device.create_encoder(
                device.streams.color_video.output_node,
                fps,
                profile=dai.VideoEncoderProperties.Profile.MJPEG,
            )
        elif video_format == "h264":
            encoder = device.create_encoder(
                device.streams.color_video.output_node,
                fps,
                profile=dai.VideoEncoderProperties.Profile.H264_BASELINE,
            )
            encoder.setBitrate(1500 * 1000)
            encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)
        elif video_format == "h265":
            encoder = device.create_encoder(
                device.streams.color_video.output_node,
                fps,
                profile=dai.VideoEncoderProperties.Profile.H265_MAIN,
            )

        encoder_stream = device.streams.create(encoder, encoder.bitstream, stream_type=StreamType.ENCODED, rate=fps)
        encoder_stream.consume(lambda frame: video_loop.append(frame.getData()))

        # NOTE(michal): Only h264 is currently supported
        if video_format == "h264":
            encoder_stream.publish(description=f"Main camera on {device.name} 720p@{fps}")

    def on_update(self):
        if self.config.send_video and self.next_detection < time.monotonic():
            for device, video_loop in self.cameras:
                if len(video_loop) == 0:
                    continue
                self.send_detection(f"Video from device {device.name}", video=save_video(video_loop, self.config.video_fps, self.config.video_format))

            self.next_detection = time.monotonic() + self.config.send_video_interval


app = VideoRecord()
app.run()
