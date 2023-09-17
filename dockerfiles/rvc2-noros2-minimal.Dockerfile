# syntax=docker/dockerfile:experimental
FROM ubuntu:22.04 as origin

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ARG DEBIAN_FRONTEND=noninteractive
ARG OPENCV_VERSION=4.7.0

FROM origin as base

# Install Python 3
RUN apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

FROM base as build

ARG TARGETARCH

# Install dependencies
RUN apt-get update -qq  && \
    apt-get install -qq -y --no-install-recommends git ca-certificates wget bzip2 build-essential cmake python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Install libusb
COPY install-libusb.sh /tmp/
RUN /tmp/install-libusb.sh

# Install depthai-python
RUN git clone --depth=1 --recurse-submodules https://github.com/luxonis/depthai-python.git

RUN cd depthai-python \
    && cmake -H. -B build -D CMAKE_BUILD_TYPE=Release -D DEPTHAI_ENABLE_BACKWARD=OFF \
    && cmake --build build --parallel $(nproc)

# Package dependencies
RUN mkdir -p /opt/depthai \
    && for dep in $(ldd /depthai-python/build/depthai*.so 2>/dev/null | awk 'BEGIN{ORS=" "}$1 ~/^\//{print $1}$3~/^\//{print $3}' | sed 's/,$/\n/'); do cp "$dep" /opt/depthai; done \
    && mv /depthai-python/build/depthai*.so /opt/depthai

# Clear python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

RUN pip3 install --no-deps --no-cache-dir robothub-oak && \
    pip3 install --no-deps --no-cache-dir depthai_sdk && \
    pip3 install --no-cache-dir --only-binary=:all: sentry-sdk distinctipy requests numpy xmltodict marshmallow opencv-contrib-python-headless

RUN apt-get purge -y --auto-remove \
    build-essential \
    cmake \
    git \
    wget \
    bzip2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
    
FROM base

# Squash the image to save on space
COPY --from=build /opt/depthai /lib
COPY --from=build /lib/libusb-1.0.so /lib/libusb-1.0.so
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
