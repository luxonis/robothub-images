#!/usr/bin/sh

pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-release-local/ depthai==2.22.0.0
pip3 install --no-deps --no-cache-dir depthai_sdk
pip3 install --no-deps --no-cache-dir robothub-oak
