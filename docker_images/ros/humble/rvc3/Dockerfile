FROM ros:humble-ros-base as origin

# Set python environment variables
ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

FROM origin as base

# Install python 3.10
RUN apt-get update && \
    apt-get install -q -y --no-install-recommends python3-dev python3-pip && \
    rm -rf /var/lib/apt/lists/* && apt-get clean
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

FROM base as build

# Install build dependencies
RUN apt-get update  && \
    apt-get install -q -y --no-install-recommends git ca-certificates wget bzip2 build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Download libusb and depthai-python
RUN wget https://github.com/libusb/libusb/releases/download/v1.0.25/libusb-1.0.25.tar.bz2 -O libusb.tar.bz2 && \
    git clone --depth=1 --branch "rvc3_develop" --recurse-submodules https://github.com/luxonis/depthai-python.git

# Patch and build libusb
COPY docker_images/linux_netlink.c /tmp/linux_netlink.c
RUN tar xf libusb.tar.bz2 \
    && cd libusb-* \
    && rm ./libusb/os/linux_netlink.c \
    && cp /tmp/linux_netlink.c ./libusb/os/linux_netlink.c \
    && ./configure --disable-udev \
    && make -j$(nproc) \
    && cp ./libusb/.libs/libusb-1.0.so.0.3.0 /tmp/libusb-1.0.so

# Build depthai-python
RUN python3.10 -m pip install --no-cache-dir --only-binary=:all: numpy
RUN cd depthai-python \
    && cmake -H. -B build -D CMAKE_BUILD_TYPE=Release -D DEPTHAI_ENABLE_BACKWARD=OFF \
    && cmake --build build --parallel $(nproc)

# Copy dependencies to /opt/depthai
RUN mkdir -p /opt/depthai \
    && for dep in $(ldd /depthai-python/build/depthai*.so 2>/dev/null | awk 'BEGIN{ORS=" "}$1 ~/^\//{print $1}$3~/^\//{print $3}' | sed 's/,$/\n/'); do cp "$dep" /opt/depthai; done \
    && mv /depthai-python/build/depthai*.so /opt/depthai

# Clear python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

# Clear build dependencies
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
COPY --from=build /tmp/libusb-1.0.so /lib/libusb-1.0.so

# Install opencv
RUN apt-get update && \
    apt-get install -q -y --no-install-recommends python3-opencv

# Install depthai-sdk
RUN git clone --depth=1 --branch "rvc3_develop" https://github.com/luxonis/depthai.git /tmp/depthai && \
    python3.10 -m pip install --no-deps --no-cache-dir /tmp/depthai/depthai_sdk && \
    rm -rf /tmp/depthai

# Install python packages
RUN python3.10 -m pip install --no-deps --no-cache-dir opencv-contrib-python && \
    python3.10 -m pip install --no-deps --no-cache-dir robothub-oak && \
    python3.10 -m pip install --no-cache-dir --only-binary=:all: distinctipy requests numpy xmltodict marshmallow
