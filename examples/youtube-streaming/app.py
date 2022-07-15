from collections import deque
from typing import List, Deque, Tuple
from datetime import timedelta

import subprocess as sp
import depthai as dai

from robothub_sdk import (
    App,
    CameraResolution,
    StreamType,
    Config,
)

from robothub_sdk.device import Device


def make_command(key: str) -> List[str]:

    HLS_URL = f"https://a.upload.youtube.com/http_upload_hls?cid={key}&copy=0&file=stream.m3u8"
    YOUTUBE_URL = f"rtmp://a.rtmp.youtube.com/live2/{key}"

    # TODO: limit max bitrate -> streaming mode needs to be passed
    # NOTE: rtmp command is not currently used -> do we need it?

    hls_command = [ "ffmpeg",
                    '-hide_banner',
                    "-fflags", "+genpts",
                    '-loglevel', 'info',
                    '-use_wallclock_as_timestamps', 'true',
                    '-thread_queue_size', '512',
                    "-i", "-",
                    "-f", "lavfi",
                    '-thread_queue_size', '512',
                    "-i", "anullsrc",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-f", "hls",
                    "-hls_time", "2",
                    "-hls_list_size", "4",
                    "-http_persistent", "1",
                    "-method", "PUT",
                    HLS_URL ]
    
    rtmp_command = [ "ffmpeg",
                    '-use_wallclock_as_timestamps', 'true',
                    "-fflags", "+genpts",
                    '-f', 'h264',
                    '-thread_queue_size', '512',
                    '-i', '-',
                    '-f', 'lavfi',
                    '-thread_queue_size', '512',
                    '-i', 'anullsrc',
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-f", "flv",
                    YOUTUBE_URL ]

    # NOTE: hls as it can stream everything (even 4K)
    return hls_command

class StreamingMode():
    fps: int
    camera_socket: dai.CameraBoardSocket
    resolution: CameraResolution

    def __init__(self, fps: int, camera_socket: dai.CameraBoardSocket, resolution: CameraResolution):
        self.fps = fps
        self.camera_socket = camera_socket
        self.resolution = resolution

streaming_modes = {
    "RGB_1080_30fps" : StreamingMode(30, dai.CameraBoardSocket.RGB, CameraResolution.THE_1080_P),
    "RGB_1080_60fps" : StreamingMode(60, dai.CameraBoardSocket.RGB, CameraResolution.THE_1080_P),
    "RGB_4K_30fps" : StreamingMode(30, dai.CameraBoardSocket.RGB, CameraResolution.THE_4_K),
    "Left_720_30fps" : StreamingMode(30, dai.CameraBoardSocket.LEFT, CameraResolution.THE_720_P),
    "Right_720_30fps" : StreamingMode(30, dai.CameraBoardSocket.RIGHT, CameraResolution.THE_720_P),
}

class YoutubeStreaming(App):
    cameras: List[Tuple[Device, Deque]]
    max_video_retention: timedelta
    key: str
    streaming_mode: StreamingMode
    proc: sp.Popen

    def __init__(self):
        super().__init__()
        self.cameras = [] # NOTE: to save all devices, streaming will be done from the first that is set up
        self.max_video_retention = timedelta(seconds=90)
        self.key = ""
        self.streaming_mode = streaming_modes["RGB_1080_30fps"]
        self.proc = None

    def on_initialize(self, unused_devices: List[dai.DeviceInfo]):
        self.cameras.clear()

    def on_configuration(self, old_configuration: Config):
        print("Configuration update", self.config.values())
        if self.config.streaming_key and self.config.streaming_key != old_configuration.streaming_key:
            self.key = self.config.streaming_key
            self.restart()

        if self.config.streaming_mode != old_configuration.streaming_mode:
            self.streaming_mode = streaming_modes[self.config.streaming_mode]
            self.cameras.clear()
            self.restart()

    def on_setup(self, device):
        backlog_size = round(self.max_video_retention.total_seconds() * self.streaming_mode.fps)
        video_loop = deque(maxlen=backlog_size)
        self.cameras.append((device, video_loop))
        mode = self.streaming_mode

        if mode.camera_socket is dai.CameraBoardSocket.LEFT or mode.camera_socket is dai.CameraBoardSocket.RIGHT:
            if dai.CameraBoardSocket.LEFT not in device.cameras or dai.CameraBoardSocket.RIGHT not in device.cameras:
                print(f"{mode.camera_socket} not availible, setting streaming mode to RGB 1080p30.")
                self.streaming_mode = streaming_modes["RGB_1080_30fps"]
                mode = self.streaming_mode
            else:
                output_node = getattr(device.streams, f"mono_{'left' if mode.camera_socket is dai.CameraBoardSocket.LEFT else 'right'}_video").output_node
        else:
            # needs to be set here because `device.ensure_camera` is called and log about resolution setting for RGB is printed
            # so it cannot be set by default as the log would be confusing
            output_node = device.streams.color_video.output_node
        
        camera = device.configure_camera(mode.camera_socket, res=mode.resolution, fps=mode.fps)

        encoder = device.create_encoder(
            output_node,
            mode.fps,
            # NOTE: h265 does not work as expected yet
            profile=dai.VideoEncoderProperties.Profile.H264_MAIN,
        )

        encoder_stream = device.streams.create(encoder, encoder.bitstream, stream_type=StreamType.ENCODED, rate=mode.fps)
        encoder_stream.consume(lambda frame: video_loop.append(frame.getData()))

        command = make_command(self.key)
        if self.proc:
            self.proc.kill()
        self.proc = sp.Popen(command, stdin=sp.PIPE, stderr=None)

    def on_update(self):
        if self.key != "":
            device, video_loop = self.cameras[0] # ensures streaming from just one device
            if len(video_loop):
                self.proc.stdin.write(video_loop.pop())

app = YoutubeStreaming()
app.run()
