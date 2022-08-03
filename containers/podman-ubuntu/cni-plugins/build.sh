#!/bin/sh

PKG_ROOT="$(pwd)/cni-plugins_${CNI_PLUGINS_VERSION}-1"

mkdir -p "${PKG_ROOT}/usr/local/libexec/cni"

git clone https://github.com/containernetworking/plugins.git
cd plugins
git checkout "v${CNI_PLUGINS_VERSION}"

./build_linux.sh
cp ./bin/* "${PKG_ROOT}/usr/local/libexec/cni/"
cd ..
mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"

dpkg-deb --build ${PKG_ROOT}

cp *.deb /packages
