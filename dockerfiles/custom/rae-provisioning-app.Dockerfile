# syntax=docker/dockerfile:experimental
FROM ubuntu:22.04 as base

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ARG DEBIAN_FRONTEND=noninteractive
ARG OPENCV_VERSION=4.7.0

# Install Python 3
RUN apt-get update -qq && \
    apt-get install -qq --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

FROM base as build

ARG TARGETARCH

# Install dependencies
RUN apt-get update -qq  && \
    apt-get install -qq --no-install-recommends ca-certificates wget && \
    rm -rf /var/lib/apt/lists/*

# Install libusb
COPY install-libusb.sh /tmp/
RUN /tmp/install-libusb.sh

# Install luxonis packages and dependencies
RUN pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-snapshot-local/ depthai==2.22.0.0.dev0+8b9eceb316ce60d57d9157ecec48534b548e8904 && \
    pip3 install --no-cache-dir --only-binary=:all: opencv-contrib-python-headless

RUN apt-get purge -y --auto-remove \
    wget \
    && rm -rf /var/lib/apt/lists/*

FROM base

# Squash the image to save on space
COPY --from=build /lib/libusb-1.0.so /lib/libusb-1.0.so
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
