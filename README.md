# RobotHub Images Repository

This repository contains the Dockerfiles used to build the images for RobotHub apps.

## Table of Contents

- [Available Images](#available-images)
- [Building Images](#building-images)
  - [Scripts Overview](#scripts-overview)
  - [Using the Scripts](#using-the-scripts)
  - [Configuration: versions.conf](#configuration-versionsconf)
  - [Dockerfiles](#dockerfiles)
  - [Additional Scripts and Utilities](#additional-scripts-and-utilities)
- [Automated Workflow](#automated-workflow)
  - [Workflow Triggers](#workflow-triggers)
  - [Key Jobs](#key-jobs)
- [Making first app](#making-first-app)
- [License](#license)

## Available Images

> [!NOTE]
> All images are available at [GitHub Packages](https://github.com/luxonis/robothub-images/pkgs/container/robothub-app-v2).

### Robotics Vision Core

- `RVC2` ([OAK Series 2](https://docs.luxonis.com/projects/hardware/en/latest/pages/articles/oak-s2/))
- `RVC3` ([OAK Series 3](https://docs.luxonis.com/projects/hardware/en/latest/pages/articles/oak-s3/))

### Variant

- `minimal`: Ubuntu-based image with minimal dependencies for running RobotHub apps
- `regular`: Ubuntu-based image for running RobotHub apps (recommended)

### ROS2

- `ros2humble`: Ubuntu-based image for running RobotHub apps with ROS2 Humble installed


## Building Images

The `scripts` directory contains the scripts used to build and publish the images.

```bash
scripts
├── build-images-base.sh
├── build-images-core.sh
├── build-images-custom.sh
├── build-images.sh
├── make-manifests.sh
└── versions.conf
```

### Scripts Overview

The build process is powered by a collection of scripts, each serving a unique purpose:

- `build-images.sh`: The main script that orchestrates the build process.
- `build-images-base.sh`: Focuses on different robot vision cores (RVCs) images based on the base image stored in:
  - `dockerfiles/base.Dockerfile`
  - `dockerfiles/depthai-v3-git/base.Dockerfile`
- `build-images-core.sh`: Builds images for core image stored in `dockerfiles/core.Dockerfile`.
- `build-images-custom.sh`: For custom application images (builtin-apps) stored in:
  - `dockerfiles/custom/builtin-app.Dockerfile`
  - `dockerfiles/custom/rae-provisioning-app.Dockerfile`
  - `dockerfiles/depthai-v3-git/builtin-app.Dockerfile`
- `make-manifests.sh`: Handles the creation of multi-arch manifests.

### Using the Scripts

The `build-images.sh` script is the primary script that orchestrates the build process. It calls other scripts to construct the images. For local testing, `build-images.sh` can be executed directly from the command line. To run this script locally, you must have `docker` installed.

To perform a local build without pushing the images to a registry, you should comment out the `push` command in the bash scripts. This prevents the images from being uploaded, allowing you to test the build process and images locally.

```bash
export ARCH=amd64 # or arm64
export IMAGE_REF_NAME=robothub-app-v2 # or robothub-app-v2-dev
export IMAGE_VERSION=$(date +%Y.%j.%H%M)

./scripts/build-images.sh
```

### Configuration: `versions.conf`

The `versions.conf` file is used to manage and specify the versions of dependencies for different Robotics Vision Core (RVC) devices within the RobotHub Images project.

To update or change the version of `depthai` or any other dependency for a specific RVC device, modify the corresponding entry in the `versions.conf` file.

Each line in `versions.conf` specifies a device identifier followed by the versions of its dependencies, separated by commas. The general format is:
```bash
<robotics_vision_core>=<depthai_version>,<depthai_sdk_version>
```

### Dockerfiles

The `dockerfiles` directory contains the Dockerfiles used to build the images.

```bash
dockerfiles
├── base.Dockerfile
├── core.Dockerfile
├── custom
│   ├── builtin-app.Dockerfile
│   └── rae-provisioning-app.Dockerfile
└── depthai-v3-git
    ├── base.Dockerfile
    └── builtin-app.Dockerfile
```

### Additional Scripts and Utilities

The `context` directory also contains additional scripts and utilities used to support the build process.

```bash
context
├── download-patched-libusb
├── install-depthai-from-git
├── install-depthai-version
├── install-luxonis-packages
├── requirements-builtin-app.txt
├── requirements-minimal.txt
├── requirements-rae-provisioning-app.txt
└── requirements-regular.txt

```

## Automated Workflow

The GitHub Actions workflow `publish-images.yml` orchestrates the build and publish process, utilizing scripts to generate different Docker images.

### Workflow Triggers
The workflow is configured with two triggers that influence the naming convention of the docker images:

- **Manual (`workflow_dispatch`)**: Initiates an on-demand build process.
  - Images built from manual triggers are tagged with `dev` in their names, designated as `robothub-app-v2-dev`, indicating development versions.
  - To trigger a manual build:
    - navigate to the [Actions](https://github.com/luxonis/robothub-images/actions/workflows/publish-images.yml) tab 
    - click the `Run workflow` button
    - select a branch to build from (e.g. `main`)
    - click the `Run workflow` button to initiate the build process


- **Release (`release`)**: Automatically triggered when a new release is published.
  - Release-triggered builds are tagged as `robothub-app-v2`, representing stable, production-ready versions.

### Key Jobs

1. **Generate Image Version**: Dynamically creates a version tag for the images from the build date and time.
2. **Build & Push Images**: Leverages multiple scripts to build images for different architectures and pushes them to GitHub Packages.
3. **Make Multi-Arch Manifests**: Consolidates images into multi-architecture manifests, facilitating platform-agnostic pulls.


## Making first app

Please visit [RobotHub documentation page](https://docs-beta.luxonis.com/develop/prepare-env/) for more information about how to make your
first app.

## License

This project is licensed under the terms of the MIT license.

If you have any questions about Perception Apps or RobotHub, please visit our [Documentation](https://docs-beta.luxonis.com/) or ask us directly on the [forums](https://discuss.luxonis.com).
