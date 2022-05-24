from functools import partial
from typing import List
import time
import datetime

import depthai as dai
from robothub_sdk import App, IS_INTERACTIVE, CameraResolution, InputStream, StreamType, Config

if IS_INTERACTIVE:
    import cv2

DETECTION_INTERVAL = datetime.timedelta(seconds=5).seconds


class HelloWorld(App):
    next_window_position = (0, 0)
    next_detection = 0
    camera_controls: List[InputStream]

    def on_initialize(self, unused_devices: List[dai.DeviceInfo]):
        self.next_window_position = (0, 30)
        self.camera_controls = []
        self.config.add_defaults(send_still_picture=False, send_still_picture_interval=DETECTION_INTERVAL)
        self.next_detection = 0

    def on_configuration(self, old_configuration: Config):
        print('Configuration update', self.config.values())
        if not self.config.send_still_picture:
            self.next_detection = 0

        if self.config.send_still_picture and self.config.send_still_picture_interval != old_configuration.send_still_picture_interval:
            self.next_detection = time.monotonic() + self.config.send_still_picture_interval

    def on_setup(self, device):
        fps = 25
        res = CameraResolution.MIN_RESOLUTION

        for camera in device.cameras:
            stream_id = f"{device.id}-{camera.name}"

            if camera == dai.CameraBoardSocket.RGB:
                device.configure_camera(camera, res=res, fps=fps, preview_size=(640, 480))
                self.camera_controls.append(device.streams.color_control)

                if IS_INTERACTIVE:
                    device.streams.color_still.consume(partial(self.on_still_frame, device.id))
                    device.streams.color_preview.consume(partial(self.on_frame, stream_id))
                else:
                    encoder = device.create_encoder(device.streams.color_still.output_node, fps=8, profile=dai.VideoEncoderProperties.Profile.MJPEG, quality=80)
                    device.streams.create(encoder, encoder.bitstream, stream_type=StreamType.BINARY, rate=8).consume(partial(self.on_still_frame, device.id))
                    device.streams.color_video.publish()
            elif camera == dai.CameraBoardSocket.LEFT:
                device.configure_camera(camera, res=res, fps=fps)
                if IS_INTERACTIVE:
                    device.streams.mono_left_video.consume(partial(self.on_frame, stream_id))
                else:
                    device.streams.mono_left_video.publish()
            elif camera == dai.CameraBoardSocket.RIGHT:
                device.configure_camera(camera, res=res, fps=fps)
                if IS_INTERACTIVE:
                    device.streams.mono_right_video.consume(partial(self.on_frame, stream_id))
                else:
                    device.streams.mono_right_video.publish()

            if IS_INTERACTIVE:
                cv2.namedWindow(stream_id)
                cv2.moveWindow(stream_id, *self.next_window_position)
                self.next_window_position = (self.next_window_position[0] + 650, self.next_window_position[1])

        self.next_window_position = (0, self.next_window_position[1] + 500)

    def on_still_frame(self, device_id: str, frame: dai.ImgFrame):
        if IS_INTERACTIVE:
            cv2.imshow(f'{device_id} Still Picture', frame.getCvFrame())
        else:
            print('Sending detection...')
            self.send_detection(f"Still frame from device {device_id}", tags=['periodic', 'still'], frames=[(frame, 'jpeg')])

    def on_frame(self, stream_id: str, frame: dai.ImgFrame):
        cv2.imshow(stream_id, frame.getCvFrame())

    def on_update(self):
        if self.config.send_still_picture and self.next_detection < time.monotonic():
            for camera_control in self.camera_controls:
                ctl = dai.CameraControl()
                ctl.setCaptureStill(True)
                camera_control.send(ctl)
            self.next_detection = time.monotonic() + self.config.send_still_picture_interval

        if IS_INTERACTIVE:
            if cv2.waitKey(1) == ord('q'):
                self.stop()


app = HelloWorld()
app.run()
