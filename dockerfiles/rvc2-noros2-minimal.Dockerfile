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

# Install dependencies for building depthai
RUN apt-get update -qq  && \
    apt-get install -qq -y --no-install-recommends git ca-certificates wget bzip2 build-essential cmake python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

RUN wget https://github.com/libusb/libusb/releases/download/v1.0.26/libusb-1.0.26.tar.bz2 -O libusb.tar.bz2 && \
    git clone --depth=1 --recurse-submodules https://github.com/luxonis/depthai-python.git

# Patch and build libusb
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

# # Clear Python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

RUN pip3 install --no-deps --no-cache-dir robothub-oak && \
    pip3 install --no-deps --no-cache-dir depthai_sdk && \
    pip3 install --no-cache-dir --only-binary=:all: sentry-sdk distinctipy requests numpy xmltodict marshmallow opencv-contrib-python-headless

# Build OpenCV from source
# WORKDIR /opt/build

# RUN set -ex \
#     && apt-get -qq update \
#     && apt-get -qq install -y --no-install-recommends \
#         build-essential cmake \
#         wget unzip \
#         libhdf5-103-1 libhdf5-dev \
#         libopenblas0 libopenblas-dev \
#         libprotobuf23 libprotobuf-dev \
#         libjpeg8 libjpeg8-dev \
#         libpng16-16 libpng-dev \
#         libtiff5 libtiff-dev \
#         libwebp7 libwebp-dev \
#         libopenjp2-7 libopenjp2-7-dev \
#         libtbb2 libtbb2-dev \
#         libeigen3-dev \
#         tesseract-ocr tesseract-ocr-por libtesseract-dev \
#         python3 python3-pip python3-numpy python3-dev \
#     && wget -q --no-check-certificate https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip -O opencv.zip \
#     && wget -q --no-check-certificate https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip -O opencv_contrib.zip \
#     && unzip -qq opencv.zip -d /opt && rm -rf opencv.zip \
#     && unzip -qq opencv_contrib.zip -d /opt && rm -rf opencv_contrib.zip \
#     && cmake \
#         -D CMAKE_BUILD_TYPE=RELEASE \
#         -D CMAKE_INSTALL_PREFIX=/usr/local \
#         -D OPENCV_EXTRA_MODULES_PATH=/opt/opencv_contrib-${OPENCV_VERSION}/modules \
#         -D EIGEN_INCLUDE_PATH=/usr/include/eigen3 \
#         -D OPENCV_ENABLE_NONFREE=ON \
#         -D WITH_JPEG=ON \
#         -D WITH_PNG=ON \
#         -D WITH_TIFF=ON \
#         -D WITH_WEBP=ON \
#         -D WITH_JASPER=ON \
#         -D WITH_EIGEN=ON \
#         -D WITH_TBB=ON \
#         -D WITH_LAPACK=ON \
#         -D WITH_PROTOBUF=ON \
#         -D WITH_V4L=OFF \
#         -D WITH_GSTREAMER=OFF \
#         -D WITH_GTK=OFF \
#         -D WITH_QT=OFF \
#         -D WITH_CUDA=OFF \
#         -D WITH_VTK=OFF \
#         -D WITH_OPENEXR=OFF \
#         -D WITH_FFMPEG=OFF \
#         -D WITH_OPENCL=OFF \
#         -D WITH_OPENNI=OFF \
#         -D WITH_XINE=OFF \
#         -D WITH_GDAL=OFF \
#         -D WITH_IPP=OFF \
#         -D BUILD_OPENCV_PYTHON3=ON \
#         -D BUILD_OPENCV_PYTHON2=OFF \
#         -D BUILD_OPENCV_JAVA=OFF \
#         -D BUILD_TESTS=OFF \
#         -D BUILD_IPP_IW=OFF \
#         -D BUILD_PERF_TESTS=OFF \
#         -D BUILD_EXAMPLES=OFF \
#         -D BUILD_ANDROID_EXAMPLES=OFF \
#         -D BUILD_DOCS=OFF \
#         -D BUILD_ITT=OFF \
#         -D INSTALL_PYTHON_EXAMPLES=OFF \
#         -D INSTALL_C_EXAMPLES=OFF \
#         -D INSTALL_TESTS=OFF \
#         /opt/opencv-${OPENCV_VERSION} \
#     && make -j$(nproc)
# RUN make install \
#     && ln -s /usr/local/lib/python3.10/dist-packages/cv2/python-3.10/cv2.cpython-310-x86_64-linux-gnu.so /usr/local/lib/python3.10/dist-packages/cv2/python-3.10/cv2.so \
#     # && rm -rf /opt/build/* \
#     # && rm -rf /opt/opencv-${OPENCV_VERSION} \
#     # && rm -rf /opt/opencv_contrib-${OPENCV_VERSION} \
#     && apt-get -qq remove -y \
#         software-properties-common \
#         build-essential cmake \
#         git wget bzip2 \
#         libhdf5-dev \
#         libprotobuf-dev \
#         libjpeg8-dev \
#         libpng-dev \
#         libtiff-dev \
#         libwebp-dev \
#         libopenjp2-7-dev \
#         libtbb-dev \
#         libtesseract-dev \
#         python3-dev \
#     && apt-get -qq autoremove \
#     && apt-get -qq clean

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
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
