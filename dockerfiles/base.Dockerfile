ARG BASE_IMAGE

FROM ${BASE_IMAGE} AS base

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install python3
RUN apt-get update -qq && \
    apt-get install -qq --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip install --upgrade pip setuptools wheel

FROM base AS build

ARG DEBIAN_FRONTEND=noninteractive
ARG ROBOTICS_VISION_CORE
ARG DEPTHAI_SDK_VERSION
ARG ROBOTHUB_OAK_VERSION
ARG VARIANT

# Install dependencies
RUN apt-get update -qq  && \
    apt-get install -qq --no-install-recommends ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

# Install luxonis packages
COPY install-luxonis-packages-${ROBOTICS_VISION_CORE}.sh /tmp/
RUN /tmp/install-luxonis-packages-${ROBOTICS_VISION_CORE}.sh

# Install python3 packages
COPY requirements-${VARIANT}.txt /tmp/
RUN pip3 install --no-cache-dir --only-binary=:all: -r /tmp/requirements-${VARIANT}.txt

FROM base

ARG TARGETARCH
ARG DEPTHAI_VERSION

# Copy python3 packages
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

# Install depthai
COPY libusb-1.0-${TARGETARCH}.so /lib/libusb-1.0.so
COPY install-depthai-version /usr/local/bin
RUN install-depthai-version ${DEPTHAI_VERSION}
