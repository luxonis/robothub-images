ARG GO_LANG_VERSION
FROM golang:${GO_LANG_VERSION}

RUN apt update && apt-get install -y\
  gettext-base\
  btrfs-progs \
  git \
  iptables \
  libassuan-dev \
  libbtrfs-dev \
  libc6-dev \
  libdevmapper-dev \
  libglib2.0-dev \
  libgpgme-dev \
  libgpg-error-dev \
  libprotobuf-dev \
  libprotobuf-c-dev \
  libseccomp-dev \
  libselinux1-dev \
  libsystemd-dev \
  pkg-config \
  runc \
  uidmap \
  libapparmor-dev \
  dpkg-dev && rm -rf /var/lib/apt/lists/* \
  && mkdir /build

COPY ./podman/* /build/
WORKDIR /build
