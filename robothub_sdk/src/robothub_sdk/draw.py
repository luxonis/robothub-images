from typing import List, Final
import depthai as dai
import numpy as np
import cv2

_BBOX_COLORS: Final = np.random.random(size=(256, 3)) * 256  # Random Colors for bounding boxes
_TEXT_BG_COLOR: Final = (0, 0, 0)
_TEXT_COLOR: Final = (255, 255, 255)
_LINE_TYPE: Final = cv2.LINE_AA
_TEXT_TYPE: Final = cv2.FONT_HERSHEY_SIMPLEX


# def _crop_offset_x(frame: np.ndarray) -> int:
#     croppedW = (frame.shape[0] / self.inputSize[1]) * self.inputSize[0]
#     return int((frame.shape[1] - croppedW) // 2)


def frame_norm(frame: np.ndarray, bbox: List[float]) -> np.ndarray:
    """
    Maps bounding box coordinates (0..1) to pixel values on frame

    Args:
        frame (numpy.ndarray): Frame to which adjust the bounding box
        bbox (list): list of bounding box points in a form of :code:`[x1, y1, x2, y2, ...]`

    Returns:
        list: Bounding box points mapped to pixel values on frame
    """
    norm_vals = np.full(len(bbox), frame.shape[0])
    norm_vals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * norm_vals).astype(int)


def draw_detection(detection: dai.ImgDetection, frame: np.ndarray):
    bbox = frame_norm(frame, [detection.xmin, detection.ymin, detection.xmax, detection.ymax])
    # bbox[::2] += self._crop_offset_x(frame)
    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), _BBOX_COLORS[detection.label], 2)
    cv2.rectangle(frame, (bbox[0], (bbox[1] - 28)), ((bbox[0] + 110), bbox[1]), _BBOX_COLORS[detection.label], cv2.FILLED)
    cv2.putText(frame, str(detection.label), (bbox[0] + 5, bbox[1] - 10), _TEXT_TYPE, 0.5, (0, 0, 0), 1, _LINE_TYPE)
    cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 62, bbox[1] - 10), _TEXT_TYPE, 0.5, (0, 0, 0), 1, _LINE_TYPE)

    # if hasattr(detection, 'spatialCoordinates'):  # Display spatial coordinates as well
    #     xMeters = detection.spatialCoordinates.x / 1000
    #     yMeters = detection.spatialCoordinates.y / 1000
    #     zMeters = detection.spatialCoordinates.z / 1000
    #     cv2.putText(frame, "X: {:.2f} m".format(xMeters), (bbox[0] + 10, bbox[1] + 60),
    #                 _TEXT_TYPE, 0.5, self._textBgColor, 4, _LINE_TYPE)
    #     cv2.putText(frame, "X: {:.2f} m".format(xMeters), (bbox[0] + 10, bbox[1] + 60),
    #                 _TEXT_TYPE, 0.5, self._textColor, 1, _LINE_TYPE)
    #     cv2.putText(frame, "Y: {:.2f} m".format(yMeters), (bbox[0] + 10, bbox[1] + 75),
    #                 _TEXT_TYPE, 0.5, self._textBgColor, 4, _LINE_TYPE)
    #     cv2.putText(frame, "Y: {:.2f} m".format(yMeters), (bbox[0] + 10, bbox[1] + 75),
    #                 _TEXT_TYPE, 0.5, self._textColor, 1, _LINE_TYPE)
    #     cv2.putText(frame, "Z: {:.2f} m".format(zMeters), (bbox[0] + 10, bbox[1] + 90),
    #                 _TEXT_TYPE, 0.5, self._textBgColor, 4, _LINE_TYPE)
    #     cv2.putText(frame, "Z: {:.2f} m".format(zMeters), (bbox[0] + 10, bbox[1] + 90),
    #                 _TEXT_TYPE, 0.5, self._textColor, 1, _LINE_TYPE)
