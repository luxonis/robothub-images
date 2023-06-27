# syntax=docker/dockerfile:experimental
FROM ros:humble-ros-core as origin

# Python will buffer output in case of non interactive terminals and we don't want that, because it delays logs
ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update  && \
    apt-get install -q -y --no-install-recommends git ca-certificates wget python3-pip bzip2 build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN wget https://github.com/libusb/libusb/releases/download/v1.0.26/libusb-1.0.26.tar.bz2 -O libusb.tar.bz2 && \
    git clone --depth=1 --recurse-submodules https://github.com/luxonis/depthai-python.git

RUN wget -O /tmp/linux_netlink.c https://raw.githubusercontent.com/luxonis/robothub-images/main/docker_images/linux_netlink.c
RUN tar xf libusb.tar.bz2 \
    && cd libusb-* \
    && rm ./libusb/os/linux_netlink.c \
    && cp /tmp/linux_netlink.c ./libusb/os/linux_netlink.c \
    && ./configure --disable-udev \
    && make -j$(nproc) \
    && cp ./libusb/.libs/libusb-1.0.so.0.3.0 /tmp/libusb-1.0.so

RUN cd depthai-python \
    && cmake -H. -B build -D CMAKE_BUILD_TYPE=Release -D DEPTHAI_ENABLE_BACKWARD=OFF \
    && cmake --build build --parallel $(nproc)

# Package dependencies
RUN mkdir -p /opt/depthai \
    && for dep in $(ldd /depthai-python/build/depthai*.so 2>/dev/null | awk 'BEGIN{ORS=" "}$1 ~/^\//{print $1}$3~/^\//{print $3}' | sed 's/,$/\n/'); do cp "$dep" /opt/depthai; done \
    && mv /depthai-python/build/depthai*.so /opt/depthai

# Clear Python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

RUN pip3 install --no-deps --no-cache-dir robothub-oak && \
    pip3 install --no-deps --no-cache-dir depthai_sdk && \
    pip3 install --no-cache-dir --only-binary=:all: sentry-sdk requests numpy \
        xmltodict marshmallow opencv-contrib-python-headless

RUN apt-get purge -y --auto-remove \
    build-essential \
    cmake \
    git \
    wget \
    bzip2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

FROM ros:humble-ros-core

# Squash the image to save on space
COPY --from=origin /opt/depthai /lib
COPY --from=origin /tmp/libusb-1.0.so /lib/libusb-1.0.so
COPY --from=origin /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
