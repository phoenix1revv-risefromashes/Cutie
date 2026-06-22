# Cutie Speaker Node Bring-Up

This document describes the first working speaker node for Cutie.

The speaker node gives Cutie dynamic voice output through ROS2. It receives text on a ROS2 topic, generates a female TTS voice using Piper, saves the generated audio as a temporary WAV file, and plays it through the USB speaker.

## Purpose

The goal of this node is to make Cutie speak from ROS2 instead of only playing audio manually from the terminal.

The voice pipeline is:

```text
ROS2 text message
    ↓
/cutie/speaker/say
    ↓
cutie_speaker node
    ↓
Piper TTS voice generation
    ↓
temporary WAV file
    ↓
aplay audio playback
    ↓
USB speaker output
```

This makes the speaker system modular. Other robot nodes do not need to know how Piper, WAV files, or Linux audio playback work. They only need to publish text to the speaker topic.

## ROS2 Package

Package name:

```text
cutie_speaker
```

Runtime node name:

```text
cutie_speaker
```

Main executable:

```text
speaker_node
```

Run command:

```bash
ros2 run cutie_speaker speaker_node
```

## ROS2 Topics

### Input Topic

```text
/cutie/speaker/say
```

Message type:

```text
std_msgs/msg/String
```

Purpose:

```text
Receives text that Cutie should speak.
```

Example:

```bash
ros2 topic pub --once /cutie/speaker/say std_msgs/msg/String "{data: 'Hi there. I am Cutie. My ROS speaker node is working now.'}"
```

### Status Topic

```text
/cutie/speaker/status
```

Message type:

```text
std_msgs/msg/String
```

Purpose:

```text
Publishes the current state of the speaker node.
```

Example status values:

```text
idle
queued
generating
speaking
done
error
```

This status topic will be useful later when connecting the speaker node to the face node. For example, the face app can show a speaking expression when the speaker status becomes `speaking`.

## Hardware Audio Verification

Before testing the ROS2 node, the speaker hardware and Linux audio path were tested directly.

Useful commands:

```bash
aplay -l
```

This lists available playback devices.

Example direct WAV test:

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

If the default output is wrong, test a specific ALSA device:

```bash
aplay -D plughw:CARD_NUMBER,0 /usr/share/sounds/alsa/Front_Center.wav
```

Example:

```bash
aplay -D plughw:2,0 /usr/share/sounds/alsa/Front_Center.wav
```

Speaker test:

```bash
speaker-test -D plughw:CARD_NUMBER,0 -c 2 -t wav
```

Sine wave test:

```bash
speaker-test -D plughw:CARD_NUMBER,0 -c 2 -t sine -f 440
```

The ROS2 speaker node should only be tested after native Linux audio playback works cleanly.

## Piper TTS Setup

Piper is used as the local text-to-speech engine.

Install required tools:

```bash
sudo apt update
sudo apt install -y python3-pip wget alsa-utils
```

Install Piper:

```bash
python3 -m pip install --user --upgrade piper-tts
```

Make sure local Python tools are in the shell path:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify Piper:

```bash
which piper
piper --help
```

## Voice Models

Voice models are stored outside the ROS2 package code:

```text
models/voices/female/
```

Example model path:

```text
models/voices/female/en_US-amy-medium.onnx
```

The `.onnx` file is the actual neural voice model. The matching `.onnx.json` file contains model configuration.

The voice model files can be large, so they are not required to be committed directly to the repository. The repository should document how to download them instead.

Example Amy medium download:

```bash
mkdir -p models/voices/female

wget -O models/voices/female/en_US-amy-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx

wget -O models/voices/female/en_US-amy-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json
```

Optional Lessac high download:

```bash
wget -O models/voices/female/en_US-lessac-high.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx

wget -O models/voices/female/en_US-lessac-high.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx.json
```

## Manual TTS Test

Before using ROS2, Piper was tested directly from the terminal.

Example:

```bash
echo "Hi there. I am Cutie. It is nice to meet you." | \
piper \
  --model models/voices/female/en_US-amy-medium.onnx \
  --output_file /tmp/cutie_test.wav

aplay /tmp/cutie_test.wav
```

This verifies:

```text
text input
    ↓
Piper voice generation
    ↓
WAV file
    ↓
speaker playback
```

## Important Voice Tuning Note

Piper variation settings were tested, but they caused audio artifacts.

The problematic settings included:

```text
noise_scale
noise_w
length_scale
```

Increasing these settings made the voice sound more varied at first, but also created static, radio-like noise, and long noisy tails after speech.

For the first stable version of the speaker node, these settings are intentionally not used.

The stable v0.1 strategy is:

```text
Use clean/default Piper generation.
Use a female voice model.
Improve warmth through sentence wording.
Avoid unstable variation controls.
```

## Build

From the Cutie workspace root:

```bash
cd ~/projects/Cutie

source /opt/ros/humble/setup.bash

colcon build --symlink-install --packages-select cutie_speaker

source install/setup.bash
```

The `--symlink-install` flag is useful during development because edits to Python source files are reflected without needing a full rebuild every time.

## Run the Speaker Node

Terminal 1:

```bash
cd ~/projects/Cutie

source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run cutie_speaker speaker_node
```

Expected logs:

```text
Cutie speaker node started.
Listening on /cutie/speaker/say
```

## Test from ROS2

Terminal 2:

```bash
cd ~/projects/Cutie

source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 topic pub --once /cutie/speaker/say std_msgs/msg/String "{data: 'Hi there. I am Cutie. My ROS speaker node is working now.'}"
```

Expected behavior:

```text
The speaker node receives the message.
Piper generates a WAV file.
aplay plays the WAV file.
Cutie speaks through the USB speaker.
```

## Monitor Speaker Status

Optional third terminal:

```bash
cd ~/projects/Cutie

source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 topic echo /cutie/speaker/status
```

Expected status flow:

```text
queued
generating
speaking
done
idle
```

## Troubleshooting

### Publisher waits forever

If this appears:

```text
Waiting for at least 1 matching subscription(s)...
```

It means the publisher is running, but no node is currently subscribed to `/cutie/speaker/say`.

Check that the speaker node is running:

```bash
ros2 node list
```

Expected:

```text
/cutie_speaker
```

Check the topic:

```bash
ros2 topic info /cutie/speaker/say
```

Expected:

```text
Subscription count: 1
```

### No sound or static

First test native Linux audio, not ROS2:

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

If needed, test the exact device:

```bash
aplay -D plughw:CARD_NUMBER,0 /usr/share/sounds/alsa/Front_Center.wav
```

If native audio is broken, the ROS2 node is not the problem yet. Fix the Linux audio output path first.

### Piper command not found

Check:

```bash
which piper
```

If missing, install Piper and make sure `~/.local/bin` is in `PATH`.

```bash
python3 -m pip install --user --upgrade piper-tts
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Voice model not found

Check that the model exists:

```bash
ls -lh models/voices/female
```

The node expects a valid `.onnx` model path.

## Current Result

The speaker node was successfully tested.

Cutie can now speak dynamically from a ROS2 topic using a local female Piper TTS voice.

This confirms the first working ROS2 voice output pipeline for Cutie.
