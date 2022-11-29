FROM docker.io/debian:bullseye-slim

ARG GO_LANG_VERSION

RUN apt update
RUN apt-get install -y wget gcc git make gettext-base runc libsystemd-dev libseccomp-dev libc6-dev \
    libglib2.0-dev btrfs-progs iptables libassuan-dev libbtrfs-dev libdevmapper-dev libgpgme-dev \
    libgpg-error-dev libprotobuf-dev libprotobuf-c-dev libselinux1-dev uidmap libapparmor-dev

RUN wget "https://go.dev/dl/go${NODE_VERSION}.linux-$(dpkg --print-architecture).tar.gz"
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf "go${NODE_VERSION}.linux-$(dpkg --print-architecture).tar.gz"
ENV PATH="${PATH}:/usr/local/go/bin"
RUN go version

VOLUME /app
WORKDIR /app

CMD ["sh", "./build.sh"]
