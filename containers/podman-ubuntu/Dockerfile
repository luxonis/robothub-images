FROM docker.io/debian:bullseye-slim

ARG GO_LANG_VERSION

RUN apt update
RUN apt-get install -y wget gcc git make gettext-base runc libsystemd-dev libseccomp-dev libc6-dev \
    libglib2.0-dev btrfs-progs iptables libassuan-dev libbtrfs-dev libdevmapper-dev libgpgme-dev \
    libgpg-error-dev libprotobuf-dev libprotobuf-c-dev libselinux1-dev uidmap libapparmor-dev

RUN wget "https://go.dev/dl/go${GO_LANG_VERSION}.linux-$(dpkg --print-architecture).tar.gz"
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf "go${GO_LANG_VERSION}.linux-$(dpkg --print-architecture).tar.gz"
ENV PATH="${PATH}:/usr/local/go/bin"
RUN go version

RUN apt-get install -y curl
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="${PATH}:$HOME/.cargo/bin"
RUN cargo --version

VOLUME /app
WORKDIR /app

CMD ["sh", "./build.sh"]
