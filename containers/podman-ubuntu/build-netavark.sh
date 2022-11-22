#/bin/sh

set -eux

ARCH="$(uname -m)"
PKG_ROOT="$(pwd)/netavark_${NETAVARK_VERSION}"

mkdir -p "${PKG_ROOT}/usr/local/libexec/podman"

git clone --depth 1 --branch "v${NETAVARK_VERSION}" https://github.com/containers/netavark/
cd netavark
make
cp ./bin/netavark "${PKG_ROOT}/usr/local/libexec/podman/"
cd ..

git clone --depth 1 --branch "v${AARDVARK_DNS_VERSION}" https://github.com/containers/aardvark-dns/
cd aardvark-dns
make
cp ./bin/aardvark-dns "${PKG_ROOT}/usr/local/libexec/podman/"
cd ..

tar -zcvf /packages/aardvark_dns_${AARDVARK_DNS_VERSION}_${ARCH}.tar.gz -C "${PKG_ROOT}" usr