from functools import partial
from pathlib import Path
from typing import List
import time
import numpy as np
import depthai as dai

from robothub_sdk import App, IS_INTERACTIVE, CameraResolution, StreamType, Config

import cv2
if IS_INTERACTIVE:
    from robothub_sdk.draw import draw_detection


DETECT_THRESHOLD = 0.5
DEFAULT_VALID_IDS = [63, 67]
QR_CODE_DETECTION_SIZE = 384
INITIAl_ROI = (0.21875, 0, 0.78125, 1.0)
DISPLAY_SIZE = (1280, 720)
EXPAND_PIXELS = 10


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
        self.obj_detections = []
        self.fps = 6
        # For storing the stream of object detections
        self.valid_ids = parse_valid_ids(self.config.classes)
        self.roi = INITIAl_ROI
    
    def on_configuration(self, old_configuration: Config):
        self.valid_ids = parse_valid_ids(self.config.classes)
        print(f'Valid ids: {self.valid_ids}')
        print(f"The consent for using detections for ML purposes has{'' if self.config.data_usage_consent else ' not'} been given.")

    def on_setup(self, device):
        camera = device.configure_camera(dai.CameraBoardSocket.RGB, res=CameraResolution.THE_4_K, fps=self.fps, preview_size=(640, 640))
        
        camera.initialControl.setSceneMode(dai.CameraControl.SceneMode.BARCODE)

        self.scale_x = camera.getVideoWidth()//DISPLAY_SIZE[0]
        self.scale_y = camera.getVideoHeight()//DISPLAY_SIZE[1]

        # Create a node with object detection model
        (_, nn_det_out, nn_det_passthrough) = device.create_nn(device.streams.color_preview, Path("./model.blob"), \
            config_path=Path("./model.json"), input_size=(640, 640))

        (manip, manip_stream) = device.create_image_manipulator()
        manip.setMaxOutputFrameSize(DISPLAY_SIZE[0] * DISPLAY_SIZE[1] * 3)
        manip.initialConfig.setResize(DISPLAY_SIZE)
        manip.initialConfig.setFrameType(dai.ImgFrame.Type.NV12)
        manip.inputConfig.setWaitForMessage(True)

        self.cropped_script = device.create_script(script_path=Path("./script.py"),
            inputs={
                'frames': device.streams.color_video
            },
            outputs={
                'manip_cfg': manip.inputConfig,
                'manip_img': manip.inputImage,
            })

        if IS_INTERACTIVE:
            device.streams.color_video.consume()
            stream_id = device.streams.color_video.description = (
                f"{device.name} {device.streams.color_video.description}"
            )
            device.streams.synchronize((nn_det_out, nn_det_passthrough, device.streams.color_video, manip_stream), partial(self.on_detection, device.id))
        else:
            encoder = device.create_encoder(
                manip_stream.output_node,
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
            device.streams.synchronize((nn_det_out, nn_det_passthrough, device.streams.color_video, encoder_stream), partial(self.on_detection, device.id))
            
    def _decode(self, frame, bbox):
        # Cropp the frame
        img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]

        # Detect and decode
        text, qr_bbox = self.detector.detectAndDecode(img)
        
        n = len(qr_bbox)
        m = len(text)

        print(f'# of qr detections in a obj detection: {n} {text}')
        if m > 0 and n > 0 and m == n:
           return list(text), [qr_bbox[i].astype(int) for i in range(n)]
        
        return [], []

    # nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
    def _frameNorm(self, frame, bbox):
        normVals = np.full(len(bbox), frame.shape[0])
        normVals[::2] = frame.shape[1]
        return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

    def _correct_bb(self, bb, roi=None):
        # To make the bbox a square
        # Check difference in aspect ratio and apply correction to BBs
        if bb.xmax-bb.xmin >= bb.ymax-bb.ymin:
            diff = (bb.xmax-bb.xmin) - (bb.ymax-bb.ymin)
            bb.ymin -= diff/2
            bb.ymax += diff/2
        else:
            diff = (bb.ymax-bb.ymin) - (bb.xmax-bb.xmin)
            bb.xmin -= diff/2
            bb.xmax += diff/2
        # Count the correct bounding box
        if roi is not None:
            xdelta = roi[2]-roi[0]
            ydelta = roi[3]-roi[1]
            bb.xmin = roi[0] + xdelta*bb.xmin
            bb.xmax = roi[0] + xdelta*bb.xmax
            bb.ymin = roi[1] + ydelta*bb.ymin
            bb.ymax = roi[1] + ydelta*bb.ymax
        # Check for overflow
        if bb.xmin < 0: bb.xmin = 0.001
        if bb.ymin < 0: bb.ymin = 0.001
        if bb.xmax > 1: bb.xmax = 0.999
        if bb.ymax > 1: bb.ymax = 0.999
        return bb

    def _corners2detection_bbox(self, corners):
        corners = np.array(corners)
        xmax = np.amax(corners[:, 0]).astype(int) + EXPAND_PIXELS
        xmin = np.amin(corners[:, 0]).astype(int) - EXPAND_PIXELS
        ymax = np.amax(corners[:, 1]).astype(int) + EXPAND_PIXELS
        ymin = np.amin(corners[:, 1]).astype(int) - EXPAND_PIXELS
        return xmin, ymin, xmax, ymax

    def on_update(self):
        if IS_INTERACTIVE:
            for device in self.devices:
                for camera in device.cameras:
                    if camera == dai.CameraBoardSocket.RGB:
                        # Save the last frame
                        frame = cv2.resize(device.streams.color_video.last_value.getCvFrame(), DISPLAY_SIZE) \
                            if device.streams.color_video.last_value is not None \
                            else np.empty([1, 1])

                        # Object detections
                        # cropped_frames = []
                        for detection, texts, qr_bboxs in self.obj_detections:
                            draw_detection(detection, frame)
                            bbox = self._frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))

                            cropped_frame = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                            # cropped_frames.append(frame[bbox[1]:bbox[3], bbox[0]:bbox[2]])
                            
                            if len(qr_bboxs) > 0:
                                for text, qr_bbox in zip(texts, qr_bboxs):
                                    # Recompute the QR code's bounding box with regard to the original scaled frame
                                    xmin, ymin, xmax, ymax = self._corners2detection_bbox(qr_bbox)
                                    top_left_corner = (bbox[0]+xmin//self.scale_x, bbox[1]+ymin//self.scale_y)
                                    bottom_right_corner = (bbox[0]+xmax//self.scale_x, bbox[1]+ymax//self.scale_y)
                                    # Draw the QR code bbox
                                    cv2.rectangle(frame, top_left_corner, bottom_right_corner, (0, 255, 0), 5)

                                    cv2.rectangle(cropped_frame, (xmin//self.scale_x, ymin//self.scale_y), (xmax//self.scale_x, ymax//self.scale_y), (0, 255, 0), 5)
                                    # cv2.rectangle(cropped_frames[-1], (xmin//self.scale_x, ymin//self.scale_y), (xmax//self.scale_x, ymax//self.scale_y), (0, 255, 0), 5)
                                    # Decode the QR code
                                    if text != '':
                                        print(f'Decoded text: {text}')
                                        coords = (bbox[0]+xmin//self.scale_x+10, bbox[1]+ymin//self.scale_y+20)
                                        cv2.putText(frame, text, coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
                                        cv2.putText(frame, text, coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

                                        cropped_coords = (xmin//self.scale_x+10, ymin//self.scale_y+20)
                                        cv2.putText(cropped_frame, text, cropped_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
                                        cv2.putText(cropped_frame, text, cropped_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
                                        # cv2.putText(cropped_frames[-1], text, cropped_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
                                        # cv2.putText(cropped_frames[-1], text, cropped_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
                                    cv2.imshow(f"Object detection detail", cropped_frame)
                        # for i, cropped_frame in enumerate(cropped_frames):
                        #     cv2.imshow(f"Object detection {i+1} detail", cropped_frame)
                        # Restore
                        self.obj_detections = []
                        
                        cv2.imshow(f"{device.streams.color_video.description}:Object detections", frame)
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

    def on_detection(self, device_id: str, obj_data: dai.ImgDetections, obj_frame: dai.ImgFrame, frame: dai.ImgFrame, video_frame: dai.ImgFrame):
        cv_frame = frame.getCvFrame()
        valid_detections = []
        # print(cv_frame.shape)
        # print(f'# of obj detections: {len(obj_data.detections)}')
        # Iterate through the object detections
        for detection in obj_data.detections:
            if detection.label in self.valid_ids and detection.confidence >= self.config.detect_threshold:
                # Remember the object detections
                self._correct_bb(detection, roi=self.roi)
                bbox = self._frameNorm(cv_frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
                # Decode the QR code
                texts, qr_bboxs = self._decode(cv_frame, bbox)
                
                if IS_INTERACTIVE:
                    self.obj_detections.append((detection, texts, qr_bboxs))
                else:
                    for text, qr_bbox in zip(texts, qr_bboxs):
                        # If the decoded text hasn't been seen in the last `x` seconds or if the decoding wasn't successful
                        if text not in self.detections_history and text != '':
                            xmin, ymin, xmax, ymax = self._corners2detection_bbox(qr_bbox)
                            # Add the detection
                            valid_detections.append({'label': detection.label,
                                                    'confidence': detection.confidence,
                                                    'xmax': (bbox[0]+xmax)//self.scale_x,
                                                    'xmin': (bbox[0]+xmin)//self.scale_x,
                                                    'ymax': (bbox[1]+ymax)//self.scale_y,
                                                    'ymin': (bbox[1]+ymin)//self.scale_y,
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
                    data=wrapper, tags=['detection', 'qr code', 'ml_usage_consent' if self.config.data_usage_consent else 'no_ml_usage_consent'],
                    frames=[(video_frame, 'jpeg')])


app = QRScanner()
app.run()
