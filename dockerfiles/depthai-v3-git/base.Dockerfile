ARG BASE_IMAGE

FROM ${BASE_IMAGE} AS base

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install python3
RUN apt-get update -qq && \
    apt-get install -qq --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

FROM base AS build

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH
ARG DEPTHAI_VERSION
ARG ROBOTICS_VISION_CORE
ARG DEPTHAI_VERSION
ARG DEPTHAI_SDK_VERSION
ARG ROBOTHUB_VERSION
ARG VARIANT

COPY install-depthai-from-git /tmp/
RUN /tmp/install-depthai-from-git ${DEPTHAI_VERSION}

# Download patched libusb
COPY download-patched-libusb /tmp/
RUN /tmp/download-patched-libusb ${TARGETARCH}

# Install luxonis packages: depthai-sdk, robothub
COPY install-luxonis-packages /tmp/
RUN /tmp/install-luxonis-packages ${ROBOTICS_VISION_CORE} ${ROBOTHUB_VERSION} ${DEPTHAI_SDK_VERSION}

# Install python3 packages
COPY requirements-${VARIANT}.txt /tmp/
RUN pip3 install --no-cache-dir --only-binary=:all: -r /tmp/requirements-${VARIANT}.txt

FROM base

ARG DEPTHAI_VERSION

# Copy python3 packages
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

# Install depthai
COPY --from=build /lib/libusb-1.0.so /lib/libusb-1.0.so
