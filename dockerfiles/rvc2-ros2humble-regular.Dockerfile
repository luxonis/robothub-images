FROM ros:humble-ros-base as base

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install pip
RUN apt-get update -qq && \
    apt-get install -qq --no-install-recommends python3-pip && \
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
RUN pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-release-local/ depthai==2.22.0.0 && \
    pip3 install --no-deps --no-cache-dir depthai_sdk && \
    pip3 install --no-deps --no-cache-dir robothub-oak && \
    pip3 install --no-cache-dir --only-binary=:all: sentry-sdk requests numpy xmltodict marshmallow opencv-contrib-python-headless av blobconverter

FROM base

# Squash the image to save on space
COPY --from=build /lib/libusb-1.0.so /lib/libusb-1.0.so
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
