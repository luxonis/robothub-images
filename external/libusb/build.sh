#!/bin/bash

wget https://github.com/libusb/libusb/releases/download/v1.0.26/libusb-1.0.26.tar.bz2 -O /tmp/libusb.tar.bz2
tar xf /tmp/libusb.tar.bz2 -C /tmp/
cd /tmp/libusb-1.0.26
rm ./libusb/os/linux_netlink.c
cp /input/linux_netlink.c ./libusb/os/linux_netlink.c
./configure --disable-udev
make -j$(nproc)
cp ./libusb/.libs/libusb-1.0.so.0.3.0 /output/libusb-1.0.so
