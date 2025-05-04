# Base Docker Image for OAK4 oakapps

This Docker image is a multi-stage build designed to provide a minimal and efficient environment for running a Python 3.12 applications using [DepthAI v3](https://github.com/luxonis/depthai-core) alongside Nginx and libraries neccesary to provide local and remote access to frontend via oak_webrtc binary. 

Key Features
- Base Image: debian:bookworm-slim for both build and final stages.
- Python Version: 3.12, built from source with optimizations for usage on OAK4.
- Included Services:
    - nginx for serving static content and reverse proxying. Self-signed SSL certificates generated during the build process. 
	- oak_webrtc binary for DepthAI WebRTC functionalities.
	- runit for service supervision.

# Build and deploy

`docker buildx build --platform=linux/arm64 -t luxonis/oakapp-base:latest --push .`