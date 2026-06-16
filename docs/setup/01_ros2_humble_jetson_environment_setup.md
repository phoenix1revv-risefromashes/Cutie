# ROS2 Humble Jetson Environment Setup

## Purpose

This document records the first development setup milestone for Cutie: installing ROS2 Humble on the Jetson target computer, configuring the terminal environment, automating ROS2 loading through `.bashrc`, and verifying basic ROS2 topic communication.

This step prepares the Jetson to run Cutie as a modular ROS2-based robot system.

## Target Machine

| Item | Value |
|---|---|
| Target Computer | NVIDIA Jetson Orin Nano / Orin Nano Super |
| Operating System | Ubuntu 22.04.5 LTS |
| Ubuntu Codename | jammy |
| CPU Architecture | aarch64 |
| ROS2 Distribution | Humble |

## Why ROS2 Humble

The Jetson target computer runs Ubuntu 22.04 Jammy. ROS2 Humble is the correct ROS2 distribution for Ubuntu 22.04-based robot development.

Cutie will run its robot modules as independent ROS2 nodes that communicate through topics, services, and actions.

## Installation Pipeline

### 1. Update Ubuntu Package List

```bash
sudo apt update
```

This refreshes Ubuntu's package index.

### 2. Install Repository Tools

```bash
sudo apt install software-properties-common curl -y
```

This installs tools needed to manage repositories and download package configuration files.

### 3. Enable Ubuntu Universe Repository

```bash
sudo add-apt-repository universe -y
```

The Universe repository is required before adding the ROS2 package source.

### 4. Update Package List Again

```bash
sudo apt update
```

This refreshes package information after enabling Universe.

### 5. Get Latest ROS Apt Source Package Version

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
```

This command retrieves the latest `ros-apt-source` release version and stores it in the `ROS_APT_SOURCE_VERSION` environment variable.

### 6. Download ROS2 Apt Source Package

```bash
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"
```

This downloads the ROS2 apt-source package for the current Ubuntu codename.

For this Jetson, the Ubuntu codename is:

```text
jammy
```

### 7. Install ROS2 Apt Source Package

```bash
sudo dpkg -i /tmp/ros2-apt-source.deb
```

This configures the system so Ubuntu's package manager can find official ROS2 packages.

### 8. Update Package List After Adding ROS2 Source

```bash
sudo apt update
```

This makes ROS2 packages visible to `apt`.

### 9. Upgrade Existing Packages

```bash
sudo apt upgrade -y
```

This updates existing system packages before installing ROS2.

### 10. Install ROS2 Humble Base

```bash
sudo apt install ros-humble-ros-base -y
```

This installs the core ROS2 Humble runtime and communication framework.

### 11. Install ROS2 Development Tools

```bash
sudo apt install ros-dev-tools python3-colcon-common-extensions -y
```

This installs tools needed for ROS2 package development and workspace builds.

## Environment Setup

ROS2 must be sourced before its commands and packages are available in a terminal.

Manual setup command:

```bash
source /opt/ros/humble/setup.bash
```

This loads ROS2 Humble into the current terminal session.

## Automating ROS2 Loading with `.bashrc`

To avoid manually sourcing ROS2 every time a new terminal opens, the following block was added to the bottom of:

```text
~/.bashrc
```

```bash
# Load ROS2 Humble
source /opt/ros/humble/setup.bash

# Check and confirm if ROS2 is loaded successfully in the terminal
if [ -n "$ROS_DISTRO" ]; then
    echo "ROS2 $ROS_DISTRO is loaded in this terminal"
fi
```

After this change, every new terminal automatically loads ROS2 Humble.

Expected terminal message:

```text
ROS2 humble is loaded in this terminal
```

## Bash Concepts Learned

### `source`

The `source` command reads a shell script and applies its environment changes to the current terminal session.

```bash
source /opt/ros/humble/setup.bash
```

This does not install ROS2. It only makes ROS2 available in the current terminal.

### `.bashrc`

`.bashrc` is a Bash startup file located in the user's home directory:

```text
~/.bashrc
```

It runs automatically whenever a new interactive Bash terminal opens.

### `$ROS_DISTRO`

`ROS_DISTRO` is an environment variable set by ROS2 after sourcing the setup file.

After loading ROS2 Humble:

```bash
echo $ROS_DISTRO
```

Expected output:

```text
humble
```

### `if [ -n "$ROS_DISTRO" ]; then`

This checks whether the `ROS_DISTRO` variable is not empty.

If it is not empty, the terminal prints a confirmation message.

## Verification 1: ROS2 CLI Availability

Command:

```bash
ros2
```

Expected result:

```text
ROS2 command groups are displayed:
action
bag
interface
launch
node
pkg
run
service
topic
```

This confirms that ROS2 is installed and available in the terminal.

## Verification 2: Basic ROS2 Topic Communication

A two-terminal test was performed.

### Terminal 1: Subscriber

```bash
ros2 topic echo /cutie_test
```

This starts a temporary subscriber that listens to `/cutie_test`.

### Terminal 2: Publisher

```bash
ros2 topic pub /cutie_test std_msgs/msg/String "{data: 'Hello from Cutie'}"
```

This starts a temporary publisher that sends a string message to `/cutie_test`.

### Expected Subscriber Output

```text
data: Hello from Cutie
---
```

## What This Proves

This setup proves:

1. ROS2 Humble is installed on the Jetson.
2. ROS2 loads automatically in new terminals.
3. The `ros2` command-line interface works.
4. Basic ROS2 topic communication works.
5. A publisher and subscriber can match through DDS.
6. A typed ROS2 message can move between independent processes.

## Cutie Development Meaning

This is the first working communication layer for Cutie.

The test pattern:

```text
temporary publisher → /cutie_test → temporary subscriber
```

maps directly to future Cutie modules:

```text
cutie_vision_node → /person_detected → cutie_orchestrator_node
cutie_orchestrator_node → /face_expression → cutie_face_node
cutie_health_monitor_node → /system_health → cutie_readiness_report_node
```

## Status

ROS2 Humble installation, terminal environment setup, `.bashrc` automation, and basic topic communication verification completed successfully.
