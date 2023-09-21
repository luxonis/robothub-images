FROM ubuntu:22.04 AS base

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

# Install dependencies
RUN apt-get update -qq  && \
    apt-get install -qq --no-install-recommends ca-certificates wget && \
    rm -rf /var/lib/apt/lists/*

# Download patched libusb
COPY download-patched-libusb.sh /tmp/
RUN /tmp/download-patched-libusb.sh

# Install depthai
COPY install-depthai-version /usr/local/bin
RUN install-depthai-version ${DEPTHAI_VERSION}

# Install python3 packages
RUN pip3 install --no-cache-dir --only-binary=:all: opencv-contrib-python-headless

FROM base

# Copy python3 packages
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
