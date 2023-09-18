#!/usr/bin/sh

pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-snapshot-local/ depthai==2.22.0.0.dev0+8b9eceb316ce60d57d9157ecec48534b548e8904
pip3 install --no-deps --no-cache-dir git+https://github.com/luxonis/depthai.git@rvc3_develop#subdirectory=depthai_sdk
pip3 install --no-deps --no-cache-dir robothub-oak
