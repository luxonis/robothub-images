FROM ghcr.io/luxonis/robothub-base-app:alpine-depthai-main

RUN apk update
RUN apk add ffmpeg

ARG FILE=app.py
ADD $FILE run.py
