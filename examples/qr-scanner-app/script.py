import time

while True:
    time.sleep(0.001) # Avoid lazy looping
    frame = node.io['frames'].tryGet()
    if frame is not None:
        cfg = ImageManipConfig()
        cfg.setResize(1280, 720)
        cfg.setKeepAspectRatio(True)
        node.io['manip_cfg'].send(cfg)
        node.io['manip_img'].send(frame)