#/bin/sh

set -eux

PKG_ROOT="$(pwd)/netavark_${NETAVARK_VERSION}"
mkdir -p "${PKG_ROOT}/usr/local/bin"

git clone --depth 1 --branch "v${NETAVARK_VERSION}" https://github.com/containers/netavark/

cd netavark
make
make DESTDIR=$PKG_ROOT install
cd ..

tar -zcvf /packages/netavark_${NETAVARK_VERSION}_${ARCH}.tar.gz "${PKG_ROOT}/usr"