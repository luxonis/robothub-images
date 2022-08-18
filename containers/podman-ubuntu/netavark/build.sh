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

tar -zcvf /packages/netavark_${NETAVARK_VERSION}_${ARCH}.tar.gz -C "${PKG_ROOT}" usr