FROM ghcr.io/luxonis/robothub-base-app:ubuntu-depthai-main

RUN pip3 install -U av

ARG FILE=app.py
ADD $FILE run.py
