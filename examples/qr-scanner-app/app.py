from functools import partial
from pathlib import Path
from typing import List
import time
import numpy as np
import depthai as dai

from robothub_sdk import App, IS_INTERACTIVE, CameraResolution, StreamType, Config
from string import Template

import cv2
if IS_INTERACTIVE:
    from robothub_sdk.draw import draw_detection


DETECT_THRESHOLD = 0.6
DEFAULT_VALID_IDS = [67]
QR_CODE_DETECTION_SIZE = 384
INITIAl_ROI = (0.21875, 0, 0.78125, 1.0)


def parse_valid_ids(ids):
    if ids is None:
        return DEFAULT_VALID_IDS
    return [int(x) for x in ids.split(",")]


class Wrapper(dict):
    def __init__(self, detection):
        dict.__init__(self, detection=detection)


class QRScanner(App):
    _counter = 0

    def on_initialize(self, unused_devices: List[dai.DeviceInfo]):
        self.config.add_defaults(send_still_picture=False, detect_threshold=DETECT_THRESHOLD)

        # Remebering the decoded texts alongside their timestamps of QR codes detected in the last `x` seconds
        self.detections_history = {}

        # QR detector
        self.detector = cv2.wechat_qrcode_WeChatQRCode("detect.prototxt", "detect.caffemodel", "sr.prototxt", "sr.caffemodel")

        # For storing detections (bboxes,and decoded texts)
        self.detections = []
        self.obj_detections = []
        self.fps = 7
        # For storing the stream of object detections
        self.manip_stream = None
        self.valid_ids = parse_valid_ids(self.config.classes)
        self.debug = False
        self.roi = INITIAl_ROI
    
    def on_configuration(self, old_configuration: Config):
        self.valid_ids = parse_valid_ids(self.config.classes)

        if old_configuration.classes and self.valid_ids != parse_valid_ids(old_configuration.classes):
            print(f'Different valid ids: {self.valid_ids}')
            # Restart the app
            self.restart()

    def on_setup(self, device):
        device.configure_camera(dai.CameraBoardSocket.RGB, res=CameraResolution.THE_4_K, fps=self.fps, preview_size=(640, 640))

        # Create a node with object detection model
        (_, nn_det_out, nn_det_passthrough) = device.create_nn(device.streams.color_preview, Path("./model.blob"), \
            config_path=Path("./model.json"), input_size=(640, 640))
        
        # Image manipulator that resize the cropped car to 384x384 for QR decoding
        (manip, manip_stream) = device.create_image_manipulator()
        manip.setMaxOutputFrameSize(QR_CODE_DETECTION_SIZE * QR_CODE_DETECTION_SIZE * 3)
        manip.initialConfig.setResize(QR_CODE_DETECTION_SIZE, QR_CODE_DETECTION_SIZE)
        manip.initialConfig.setFrameType(dai.ImgFrame.Type.NV12)
        manip.inputConfig.setWaitForMessage(True)

        self.manip_stream = manip_stream

        self.cropped_script = device.create_script(content=self._create_multi_stage_script(), name='cropping_script',
            inputs={
                'detections': nn_det_out,
                'passthrough': nn_det_passthrough,
                'frames': device.streams.color_video
            },
            outputs={
                'manip_cfg': manip.inputConfig,
                'manip_img': manip.inputImage,
            })
        
        # 2nd stage - QR code detector
        (_, qr_det_out, qr_pass) = device.create_nn(
            manip_stream, blob_path=Path('./qr_model.blob'), config_path=Path("./qr_model.json"), full_fov=False)

        if IS_INTERACTIVE:
            device.streams.color_preview.consume()
            stream_id = device.streams.color_preview.description = (
                f"{device.name} {device.streams.color_preview.description}"
            )
            self.manip_stream.consume()
            device.streams.synchronize((qr_det_out, qr_pass, nn_det_out, nn_det_passthrough, device.streams.color_preview), partial(self.on_detection, device.id))
        else:
            encoder = device.create_encoder(
                self.manip_stream.output_node,
                fps=self.fps,
                profile=dai.VideoEncoderProperties.Profile.MJPEG,
                quality=80,
            )
            encoder_stream = device.streams.create(
                encoder,
                encoder.bitstream,
                stream_type=StreamType.BINARY,
                rate=self.fps,
            )
                
            device.streams.color_video.publish()
            device.streams.synchronize((qr_det_out, qr_pass, nn_det_out, nn_det_passthrough, encoder_stream), partial(self.on_detection, device.id))
            # self.manip_stream.publish()

    def _create_multi_stage_script(self):
        with open('template_multi_stage_script.py', 'r') as file:
            return Template(file.read()).substitute(
                DEBUG = '' if self.debug else '#',
                CHECK_LABELS = f"if det.label not in {str(self.valid_ids)}: continue" if self.valid_ids else "",
                CORRECT_BB = f'correct_bb(det, roi={self.roi})',
                WIDTH = str(QR_CODE_DETECTION_SIZE),
                HEIGHT = str(QR_CODE_DETECTION_SIZE),
            )
            
    def _decode(self, frame, bbox):
        # Cropp the frame
        img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        # Detect and decode
        res, _ = self.detector.detectAndDecode(img)

        if len(res) > 0:
            return res[0]
        
        return ""

    # nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
    def _frameNorm(self, frame, bbox):
        normVals = np.full(len(bbox), frame.shape[0])
        normVals[::2] = frame.shape[1]
        return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

    def on_update(self):
        if IS_INTERACTIVE:
            for device in self.devices:
                for camera in device.cameras:
                    if camera == dai.CameraBoardSocket.RGB:
                        # Save the last frame
                        frame = device.streams.color_preview.last_value.getCvFrame() \
                            if device.streams.color_preview.last_value is not None \
                            else np.empty([1, 1])

                        # Object detections
                        for detection in self.obj_detections:
                            draw_detection(detection, frame)
                            
                        # Restore
                        self.obj_detections = []
                        
                        cv2.imshow(
                            f"{device.streams.color_preview.description}:Object detections",
                            frame
                        )

            # Showing the detection cropped frame
            manip_frame = self.manip_stream.last_value.getCvFrame() \
                            if self.manip_stream.last_value is not None \
                            else np.empty([1, 1])
            
            if manip_frame.shape[0] > 1:
                for detection in self.detections:
                    draw_detection(detection, manip_frame)
                    bbox = self._frameNorm(manip_frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
                    # Decode the QR code
                    text = self._decode(manip_frame, bbox)
                    if text != '':
                        print(f'Decoded text: {text}')
                        coords = (bbox[0] + 10, bbox[1] + 40)
                        cv2.putText(manip_frame, text, coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
                        cv2.putText(manip_frame, text, coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

                # Restore
                self.detections = []
            cv2.imshow('Cropped object detection - QR code detections', manip_frame)
        else:
            keys2remove = []
            # Look at the detected codes in the last `x` seconds and update it
            for decoded_text, timestamp in self.detections_history.items():
                # If the interval for state change has passed mark it to delete the decoded text 
                if time.monotonic() - timestamp > self.config.send_still_picture_state_changed_interval:
                    keys2remove.append(decoded_text)

            # Delete the decoded text
            for k in keys2remove: del self.detections_history[k]

        if IS_INTERACTIVE:
            key = cv2.waitKey(1)
            if key == ord("q"):
                self.stop()

    def on_detection(self, device_id: str, data: dai.ImgDetections, frame: dai.ImgFrame, obj_data: dai.ImgDetections, obj_frame: dai.ImgFrame, video_frame: dai.ImgFrame):
        def expandDetection(det, percent=2):
            percent /= 100
            det.xmin -= percent
            det.ymin -= percent
            det.xmax += percent
            det.ymax += percent
            if det.xmin < 0: det.xmin = 0
            if det.ymin < 0: det.ymin = 0
            if det.xmax > 1: det.xmax = 1
            if det.ymax > 1: det.ymax = 1

        if IS_INTERACTIVE:
            # Iterate through the object detections
            for detection in obj_data.detections:
                if detection.label in self.valid_ids:
                    # Remember the object detections
                    self.obj_detections.append(detection)

            for detection in data.detections:
                if detection.confidence >= self.config.detect_threshold:
                    expandDetection(detection)
                    # Remember the QR code detections
                    self.detections.append(detection)
        else:
            valid_detections = []
            
            # Handle qr detections
            for detection in data.detections:
                if detection.confidence >= self.config.detect_threshold:
                    expandDetection(detection)

                    cv_frame = frame.getCvFrame()

                    bbox = self._frameNorm(cv_frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
                    # Decode the QR code
                    text = self._decode(cv_frame, bbox)

                    # If the decoded text hasn't been seen in the last `x` seconds or if the decoding wasn't successful
                    if text not in self.detections_history and text != '':
                        # Add the detection
                        valid_detections.append({'label': detection.label,
                                                'confidence': detection.confidence,
                                                'xmax': bbox[2],
                                                'xmin': bbox[0],
                                                'ymax': bbox[3],
                                                'ymin': bbox[1],
                                                'text': text})
                        # Add decoded text
                        # Remember the timestamp
                        self.detections_history[text] = time.monotonic()
                    
                    if text in self.detections_history:
                        print(f'QR code already seen in the last {self.config.send_still_picture_state_changed_interval}s.')
                    if text == '':
                        print('Decoding not working...')

            # Now if you have some valid detections, it should send them
            if len(valid_detections) > 0:
                # Send each detection
                for valid_detection in valid_detections:
                    wrapper = Wrapper([valid_detection])
                    print('sending...')
                    print(f'Decoded text: {valid_detection["text"]}')
                    self.send_detection(f'Still frame from device {device_id}. Decoded text: \
                        {valid_detection["text"] if valid_detection["text"] != "" else "None"}. Confidence: {valid_detection["confidence"]}',
                        data=wrapper, tags=['detection', 'qr code'], frames=[(video_frame, 'jpeg')])


app = QRScanner()
app.run()
