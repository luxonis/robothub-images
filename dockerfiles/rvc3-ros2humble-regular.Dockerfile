FROM ros:humble-ros-base as origin

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

FROM origin as base

# Install pip
RUN apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends python3-pip && \
    rm -rf /var/lib/apt/lists/*

FROM base as build

ARG TARGETARCH

# Install dependencies
RUN apt-get update -qq  && \
    apt-get install -qq -y --no-install-recommends ca-certificates wget git && \
    rm -rf /var/lib/apt/lists/*

# Install libusb
COPY install-libusb.sh /tmp/
RUN /tmp/install-libusb.sh

RUN pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-snapshot-local/ depthai==2.22.0.0.dev0+8b9eceb316ce60d57d9157ecec48534b548e8904 && \
    pip3 install --no-deps --no-cache-dir git+https://github.com/luxonis/depthai.git@rvc3_develop#subdirectory=depthai_sdk && \
    pip3 install --no-deps --no-cache-dir robothub-oak && \
    pip3 install --no-cache-dir --only-binary=:all: sentry-sdk requests numpy xmltodict marshmallow opencv-contrib-python-headless av blobconverter

RUN apt-get purge -y --auto-remove \
    wget git \
    && rm -rf /var/lib/apt/lists/*

FROM base

# Squash the image to save on space
COPY --from=build /lib/libusb-1.0.so /lib/libusb-1.0.so
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
