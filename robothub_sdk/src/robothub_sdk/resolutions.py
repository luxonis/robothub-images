import enum
import depthai as dai
        
_COLOR_RESOLUTION = [
    dai.ColorCameraProperties.SensorResolution.THE_1080_P,
    dai.ColorCameraProperties.SensorResolution.THE_12_MP,
    dai.ColorCameraProperties.SensorResolution.THE_13_MP,
    dai.ColorCameraProperties.SensorResolution.THE_4_K,
]

_MONO_RESOLUTION = [
    dai.MonoCameraProperties.SensorResolution.THE_400_P,
    dai.MonoCameraProperties.SensorResolution.THE_480_P,
    dai.MonoCameraProperties.SensorResolution.THE_720_P,
    dai.MonoCameraProperties.SensorResolution.THE_800_P,
]

class CameraResolution(enum.Enum):
    MAX_RESOLUTION = "MAX_RESOLUTION"
    MIN_RESOLUTION = "MIN_RESOLUTION"
    THE_400_P = dai.MonoCameraProperties.SensorResolution.THE_400_P
    THE_480_P = dai.MonoCameraProperties.SensorResolution.THE_480_P
    THE_720_P = dai.MonoCameraProperties.SensorResolution.THE_720_P
    THE_800_P = dai.MonoCameraProperties.SensorResolution.THE_800_P
    THE_1080_P = dai.ColorCameraProperties.SensorResolution.THE_1080_P
    THE_1200_P = "1200p"
    THE_12_MP = dai.ColorCameraProperties.SensorResolution.THE_12_MP
    THE_13_MP = dai.ColorCameraProperties.SensorResolution.THE_13_MP
    THE_4_K = dai.ColorCameraProperties.SensorResolution.THE_4_K

    def __str__(self):
        if self == CameraResolution.MAX_RESOLUTION:
            return "max"
        if self == CameraResolution.MIN_RESOLUTION:
            return "min"
        if self == CameraResolution.THE_400_P:
            return "400p"
        if self == CameraResolution.THE_480_P:
            return "480p"
        if self == CameraResolution.THE_720_P:
            return "720p"
        if self == CameraResolution.THE_800_P:
            return "800p"
        if self == CameraResolution.THE_1080_P:
            return "1080p"
        if self == CameraResolution.THE_12_MP:
            return "12MP"
        if self == CameraResolution.THE_13_MP:
            return "13MP"
        if self == CameraResolution.THE_4_K:
            return "4k"

        return self.name

    def for_socket(self, camera: dai.CameraBoardSocket):
        if camera == dai.CameraBoardSocket.RGB:
            if self == CameraResolution.MAX_RESOLUTION:
                return dai.ColorCameraProperties.SensorResolution.THE_4_K
            if self == CameraResolution.MIN_RESOLUTION:
                return dai.ColorCameraProperties.SensorResolution.THE_1080_P
            if self.value == "1200p":
                return dai.ColorCameraProperties.SensorResolution.THE_1200_P
            if self.value not in _COLOR_RESOLUTION:
                print(f'{self.value} is not supported for RGB camera! fallback to THE_1080_P');
                return dai.ColorCameraProperties.SensorResolution.THE_1080_P
            return self.value

        if self == CameraResolution.MAX_RESOLUTION:
            return dai.MonoCameraProperties.SensorResolution.THE_800_P
        if self == CameraResolution.MIN_RESOLUTION or self.value not in _MONO_RESOLUTION:
            return dai.MonoCameraProperties.SensorResolution.THE_400_P
        return self.value