# Build custom libusb

```shell
docker build --file build.Dockerfile -t libusb-build-env:v1.0 .
docker run -it -v $(pwd):/input -v $(pwd):/output libusb-build-env:v1.0 /input/build.sh
```

Then rename `libusb-1.0.so` to `libusb-1.0-amd64.so` or `libusb-1.0-arm64.so` respectively.
