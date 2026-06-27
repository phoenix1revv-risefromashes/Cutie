# Cutie ReSpeaker 4-Mic Array Bring-Up

## Goal

Bring up the ReSpeaker XVF3800 4-Mic Array on the Jetson and verify that Cutie can capture usable microphone audio before building the ROS2 audio node.

This bring-up focuses only on the Linux and native audio validation stage.

The goal is not speech recognition yet.

The goal is to prove:

- Linux detects the microphone array
- ALSA exposes it as a recording device
- The correct audio format, sample rate, and channel count are known
- A clear voice sample can be recorded from the microphone
- Failed or unclear recordings are not committed as valid evidence

## Hardware

- Jetson Orin Nano
- ReSpeaker XVF3800 4-Mic Array
- USB connection to Jetson
- Cutie project repository

## Bring-Up Philosophy

The microphone was brought up layer by layer.

The integration path is:

```text
Physical microphone
↓
USB / Linux detection
↓
ALSA recording device
↓
Native recording test with arecord
↓
Playback verification with aplay
↓
Python audio capture
↓
ROS2 microphone node
↓
Cutie listening behavior
```

This document covers the Linux, ALSA, and native recording stages.

Python and ROS2 integration are future work.

## Step 1: Verify ALSA Recording Hardware

The first check was to confirm that Linux exposes the ReSpeaker as an audio capture device.

Command:

```bash
arecord -l
```

Detected device:

```text
card 1: Array [reSpeaker XVF3800 4-Mic Array], device 0: USB Audio [USB Audio]
```

This confirmed that ALSA detected the ReSpeaker microphone array as:

```text
Card name: Array
Device: 0
Numeric address: card 1, device 0
```

## Step 2: List Usable ALSA Device Names

Command:

```bash
arecord -L
```

Relevant ReSpeaker entries:

```text
hw:CARD=Array,DEV=0
    reSpeaker XVF3800 4-Mic Array, USB Audio
    Direct hardware device without any conversions

plughw:CARD=Array,DEV=0
    reSpeaker XVF3800 4-Mic Array, USB Audio
    Hardware device with all software conversions

sysdefault:CARD=Array
    reSpeaker XVF3800 4-Mic Array, USB Audio
    Default Audio Device
```

The main target device for direct hardware testing is:

```text
hw:CARD=Array,DEV=0
```

A more flexible target for testing with ALSA conversions is:

```text
plughw:CARD=Array,DEV=0
```

## Important Terminology

### ALSA

ALSA means Advanced Linux Sound Architecture.

It is the low-level Linux audio system that exposes microphones, speakers, audio cards, sample rates, formats, and channels.

### Audio Card

In ALSA, a card means an audio hardware device registered by Linux.

For this bring-up, the ReSpeaker appears as:

```text
CARD=Array
```

### Audio Device

A device is an endpoint inside an ALSA card.

For this bring-up, the ReSpeaker capture device is:

```text
DEV=0
```

### Channel

A channel is one lane or stream of audio data.

Examples:

```text
1 channel  = mono audio
2 channels = two audio streams
4 channels = four audio streams
```

Although the hardware is a 4-mic array, ALSA reported this capture mode as 2 channels.

## Step 3: Initial Recording Attempt

An initial recording was attempted using mono capture:

```bash
arecord -D plughw:CARD=Array,DEV=0 -f S16_LE -r 16000 -c 1 -d 10 /tmp/cutie_respeaker_1ch_test.wav
```

Result:

```text
Playback was not clear.
The recording sounded like a long beep instead of recognizable voice.
```

This meant the microphone was detected, but the recording settings were likely incorrect.

The bad recording was not committed.

## Step 4: Debug the Hardware Parameters

To avoid guessing, the ReSpeaker hardware parameters were inspected.

Command:

```bash
arecord -D hw:CARD=Array,DEV=0 --dump-hw-params -d 1 /tmp/cutie_mic_probe.wav
```

Key output:

```text
FORMAT:  S16_LE
CHANNELS: 2
RATE: 16000
```

This showed that the correct capture settings are:

```text
Format:   S16_LE
Rate:     16000 Hz
Channels: 2
```

## Root Cause of the Bad Recording

The first test used:

```text
-c 1
```

That asked ALSA to capture one channel.

The hardware parameter probe showed:

```text
CHANNELS: 2
```

So the initial recording command did not match the channel count reported by the device.

The corrected command must use:

```text
-c 2
```

## Step 5: Correct Recording Command

The corrected recording command is:

```bash
arecord -D hw:CARD=Array,DEV=0 -f S16_LE -r 16000 -c 2 --vumeter=stereo -d 10 /tmp/cutie_respeaker_2ch_test.wav
```

Meaning:

```text
-D hw:CARD=Array,DEV=0    Use the ReSpeaker microphone directly
-f S16_LE                 Use 16-bit signed little-endian audio
-r 16000                  Record at 16,000 samples per second
-c 2                      Record 2 audio channels
--vumeter=stereo          Show live audio level for both channels
-d 10                     Record for 10 seconds
/tmp/...wav               Save temporary recording outside the repo
```

The file is first saved to `/tmp` so that failed recordings are not accidentally committed.

## Step 6: Playback Verification

Command:

```bash
aplay /tmp/cutie_respeaker_2ch_test.wav
```

Expected result:

```text
The playback should contain recognizable voice, not only a beep or noise.
```

If the audio is clear, the test sample can be copied into the project as bring-up evidence.

Command:

```bash
mkdir -p assets/audio
cp /tmp/cutie_respeaker_2ch_test.wav assets/audio/cutie_respeaker_2ch_test.wav
```

## Validation Result

The microphone bring-up is considered successful when:

- `arecord -l` shows the ReSpeaker 4-mic array
- `arecord -L` shows `hw:CARD=Array,DEV=0`
- Hardware parameter probing reports:
  - `FORMAT: S16_LE`
  - `CHANNELS: 2`
  - `RATE: 16000`
- A corrected two-channel recording produces recognizable voice
- Failed mono recordings are not committed

## Final Working Native Recording Command

```bash
arecord -D hw:CARD=Array,DEV=0 -f S16_LE -r 16000 -c 2 --vumeter=stereo -d 10 /tmp/cutie_respeaker_2ch_test.wav
```

Playback command:

```bash
aplay /tmp/cutie_respeaker_2ch_test.wav
```

## Debugging Summary

During microphone bring-up, the ReSpeaker was detected correctly by ALSA, but the first recording produced unclear audio.

Instead of assuming the hardware was bad, the device was inspected using `arecord --dump-hw-params`.

The hardware reported that it expected:

```text
S16_LE format
16000 Hz sample rate
2 channels
```

The recording command was updated to match those settings.

This was a real audio-layer debugging step:

```text
Symptom: long beep / unclear playback
Investigation: inspect ALSA hardware parameters
Root cause: wrong channel count
Fix: record with 2 channels instead of 1
```

## Interview Explanation

A concise way to explain this bring-up:

```text
I brought up the ReSpeaker 4-mic array layer by layer. First I verified that ALSA detected it as a recording device. Then I listed the usable ALSA device names and targeted it directly as hw:CARD=Array,DEV=0. My first mono recording produced a long beep, so I debugged the audio capture settings using arecord --dump-hw-params. The device reported S16_LE format, 16000 Hz sample rate, and 2 channels. I corrected the recording command to match those hardware parameters, which is an example of debugging the audio capture layer instead of guessing.
```

## Future Work

After native microphone bring-up, the next steps are:

1. Create a minimal Python audio test
2. Measure live microphone loudness
3. Detect speech-like sound activity
4. Create a ROS2 `cutie_audio` package
5. Add a microphone status node
6. Publish audio state on a topic such as `/cutie/audio_status`
7. Connect audio state to the Cutie face display module

Planned robot behavior:

```text
quiet room → idle face
voice detected → listening face
robot speaking → speaking face
```
