#!/bin/sh

set -eux

export PACKAGE_ARCH="$(dpkg --print-architecture)"

PKG_ROOT="$(pwd)/cni-plugins_${CNI_PLUGINS_VERSION}"

mkdir -p "${PKG_ROOT}/usr/local/libexec/cni"

git clone --depth 1 --branch "v${CNI_PLUGINS_VERSION}" https://github.com/containernetworking/plugins.git
cd plugins

./build_linux.sh
cp ./bin/* "${PKG_ROOT}/usr/local/libexec/cni/"
cd ..
mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"

dpkg-deb --build ${PKG_ROOT}

cp *.deb /packages

tar -zcvf /packages/cni-plugins_${CNI_PLUGINS_VERSION}.tar.gz "${PKG_ROOT}/usr"
