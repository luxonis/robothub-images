FROM ghcr.io/luxonis/robothub-base-app:ubuntu-depthai-main


RUN pip3 install -U numpy opencv-contrib-python-headless

ARG FILE=app.py
ADD qr_model.blob .
ADD qr_model.json .

ADD detect.prototxt .
ADD detect.caffemodel .
ADD sr.prototxt .
ADD sr.caffemodel .

# ADD script.py .
ADD template_multi_stage_script.py .

ADD model.blob .
ADD model.json .

ADD $FILE run.py
