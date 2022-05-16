# RobotHub apps

## What is RobotHub app ##

RobotHub app is docker container with special **robotapp.yml** which defines initial app configuration and describes how the app should be shown in the RobotHub app list.


## Connecting your first robot to the RobotHub

1. Login to your account at https://hub.luxonis.com/
2. Go to robot list and click on "Add new robot" button
3. Copy the command to your linux device and robot should appear in the list of your robots in no more than 10 - 20 seconds after the installation is finished.

**Supported operating systems**: currently we support all Ubuntu Server versions from 20.04.

**Supported platforms**: x86 and arm64 (raspberry) and **only 64bit versions of operating systems are supported!**


## Making first app

1. Register you account at https://hub.luxonis.com/
2. Install RobotHub CLI: 
```bash
    curl https://stg.luxonis.com/cli/robothub-cli-linux
```
3. Run the following command and log-in to RobotHub
```bash
    ./robothub-cli-linux login
```
4. Clone this repository
```bash
    git clone https://github.com/luxonis/robothub-apps
    cd robothub-apps
```
5. Open hello-world example and upload the app to RobotHub
```bash
    cd hello-world
    ./robothub-cli-linux app push .
```

## Deploying the first app to the robots

1. Login to your account at https://hub.luxonis.com/
2. Choose robot and click on Perception apps tab
3. Click on Launch App button, choose your app and wait until the app is deployed to the robot
4. The app should be running on the robot

## App debugging ##

??


## App components ##

**robotapp.yml** describes app configuration which is presented in the RobotHub web UI. Each app must have this file present.


**Dockerfile** contains information about how to build the app container











