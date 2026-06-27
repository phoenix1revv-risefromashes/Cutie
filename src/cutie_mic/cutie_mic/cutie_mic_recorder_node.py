#!/usr/bin/env python3

import queue
import threading
import time
import wave
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
import rclpy
import sounddevice as sd
from rclpy.node import Node
from std_msgs.msg import String


class CutieMicRecorderNode(Node):
    def __init__(self):
        super().__init__("cutie_mic_recorder")

        self.declare_parameter("sample_rate", 16000)
        self.declare_parameter("input_channels", 1)
        self.declare_parameter("block_duration", 0.1)
        self.declare_parameter("sound_threshold", 0.016)
        self.declare_parameter("record_seconds", 4.0)
        self.declare_parameter("pre_roll_seconds", 0.4)
        self.declare_parameter("cooldown_seconds", 1.5)

        self.declare_parameter("device_index", -1)
        self.declare_parameter("device_name_contains", "reSpeaker XVF3800")

        self.declare_parameter(
            "recordings_dir",
            str(Path.home() / "projects" / "Cutie" / "recordings"),
        )

        self.declare_parameter("self_speech_mute_enabled", True)
        self.declare_parameter("mute_seconds_after_speaker_say", 4.0)
        self.declare_parameter("speaking_seconds_per_word", 0.55)
        self.declare_parameter("min_self_speech_mute_seconds", 6.5)
        self.declare_parameter("max_self_speech_mute_seconds", 18.0)

        self.sample_rate = int(self.get_parameter("sample_rate").value)
        self.input_channels = int(self.get_parameter("input_channels").value)
        self.block_duration = float(self.get_parameter("block_duration").value)
        self.sound_threshold = float(self.get_parameter("sound_threshold").value)
        self.record_seconds = float(self.get_parameter("record_seconds").value)
        self.pre_roll_seconds = float(self.get_parameter("pre_roll_seconds").value)
        self.cooldown_seconds = float(self.get_parameter("cooldown_seconds").value)

        self.device_index = int(self.get_parameter("device_index").value)
        self.device_name_contains = str(
            self.get_parameter("device_name_contains").value
        ).strip()

        self.self_speech_mute_enabled = bool(
            self.get_parameter("self_speech_mute_enabled").value
        )
        self.mute_seconds_after_speaker_say = float(
            self.get_parameter("mute_seconds_after_speaker_say").value
        )
        self.speaking_seconds_per_word = float(
            self.get_parameter("speaking_seconds_per_word").value
        )
        self.min_self_speech_mute_seconds = float(
            self.get_parameter("min_self_speech_mute_seconds").value
        )
        self.max_self_speech_mute_seconds = float(
            self.get_parameter("max_self_speech_mute_seconds").value
        )

        self.recordings_dir = Path(
            str(self.get_parameter("recordings_dir").value)
        ).expanduser()
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        self.resolved_device_index = self.resolve_input_device()

        self.block_size = int(self.sample_rate * self.block_duration)
        self.record_target_frames = int(self.sample_rate * self.record_seconds)

        pre_roll_blocks = max(1, int(self.pre_roll_seconds / self.block_duration))

        self.status_publisher = self.create_publisher(
            String,
            "/cutie/audio/status",
            10,
        )

        self.file_publisher = self.create_publisher(
            String,
            "/cutie/audio/file",
            10,
        )

        self.speaker_subscription = self.create_subscription(
            String,
            "/cutie/speaker/say",
            self.speaker_say_callback,
            10,
        )

        self.latest_rms = 0.0
        self.is_recording = False
        self.record_frames = []
        self.record_frame_count = 0
        self.next_allowed_trigger_time = 0.0
        self.mute_until = 0.0
        self.pre_roll_buffer = deque(maxlen=pre_roll_blocks)

        self.lock = threading.Lock()
        self.save_queue = queue.Queue()

        self.save_thread = threading.Thread(
            target=self._save_worker,
            daemon=True,
        )
        self.save_thread.start()

        self.audio_stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.input_channels,
            blocksize=self.block_size,
            dtype="float32",
            callback=self._audio_callback,
            device=self.resolved_device_index,
        )

        self.audio_stream.start()

        self.status_timer = self.create_timer(0.2, self._publish_status)

        self.get_logger().info("Cutie mic recorder node started.")
        self.get_logger().info(f"Sample rate: {self.sample_rate} Hz")
        self.get_logger().info(f"Input channels: {self.input_channels}")
        self.get_logger().info(f"Block size: {self.block_size} samples")
        self.get_logger().info(f"Sound threshold: {self.sound_threshold}")
        self.get_logger().info(f"Record seconds: {self.record_seconds}")
        self.get_logger().info(f"Recordings directory: {self.recordings_dir}")
        self.get_logger().info(f"Resolved audio device index: {self.resolved_device_index}")
        self.get_logger().info(f"Self-speech mute enabled: {self.self_speech_mute_enabled}")

    def resolve_input_device(self):
        if self.device_index >= 0:
            self.get_logger().info(
                f"Using fixed sounddevice input index: {self.device_index}"
            )
            return self.device_index

        if not self.device_name_contains:
            self.get_logger().warn(
                "No device_index or device_name_contains set. Using default input device."
            )
            return None

        devices = sd.query_devices()
        search_text = self.device_name_contains.lower()

        for index, device in enumerate(devices):
            name = str(device["name"])
            max_input_channels = int(device["max_input_channels"])

            name_matches = search_text in name.lower()
            is_input_device = max_input_channels > 0

            if name_matches and is_input_device:
                self.get_logger().info(
                    f"Auto-selected input device {index}: {name}"
                )
                return index

        self.get_logger().error(
            f"Could not find input device containing: {self.device_name_contains}"
        )
        self.get_logger().error("Available input devices:")

        for index, device in enumerate(devices):
            name = str(device["name"])
            max_input_channels = int(device["max_input_channels"])

            if max_input_channels > 0:
                self.get_logger().error(
                    f"  index={index}, inputs={max_input_channels}, name={name}"
                )

        raise RuntimeError(
            f"No input device found containing: {self.device_name_contains}"
        )

    def speaker_say_callback(self, msg):
        if not self.self_speech_mute_enabled:
            return

        text = msg.data.strip()
        word_count = len(text.split())

        estimated_speaking_seconds = word_count * self.speaking_seconds_per_word

        mute_seconds = estimated_speaking_seconds + self.mute_seconds_after_speaker_say
        mute_seconds = max(self.min_self_speech_mute_seconds, mute_seconds)
        mute_seconds = min(self.max_self_speech_mute_seconds, mute_seconds)

        with self.lock:
            self.mute_until = time.time() + mute_seconds
            self.is_recording = False
            self.record_frames = []
            self.record_frame_count = 0
            self.next_allowed_trigger_time = self.mute_until

        self.publish_status_text("muted")
        self.get_logger().info(
            f"Muted mic for {mute_seconds:.2f}s while Cutie is speaking."
        )

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            self.get_logger().warn(f"Audio stream status: {status}")

        audio_block = indata.copy()

        if audio_block.ndim > 1:
            mono_block = np.mean(audio_block, axis=1).astype(np.float32)
        else:
            mono_block = audio_block.astype(np.float32)

        if mono_block.size > 0:
            rms = float(np.sqrt(np.mean(np.square(mono_block))))
        else:
            rms = 0.0

        now = time.time()

        with self.lock:
            self.latest_rms = rms

            if now < self.mute_until:
                self.is_recording = False
                self.record_frames = []
                self.record_frame_count = 0
                return

            self.pre_roll_buffer.append(mono_block.copy())

            if self.is_recording:
                self.record_frames.append(mono_block.copy())
                self.record_frame_count += len(mono_block)

                if self.record_frame_count >= self.record_target_frames:
                    completed_audio = np.concatenate(self.record_frames)

                    self.is_recording = False
                    self.record_frames = []
                    self.record_frame_count = 0
                    self.next_allowed_trigger_time = now + self.cooldown_seconds

                    self.save_queue.put(completed_audio)

            else:
                sound_detected = rms >= self.sound_threshold
                allowed_to_trigger = now >= self.next_allowed_trigger_time

                if sound_detected and allowed_to_trigger:
                    self.is_recording = True
                    self.record_frames = [
                        block.copy() for block in self.pre_roll_buffer
                    ]
                    self.record_frames.append(mono_block.copy())
                    self.record_frame_count = sum(
                        len(block) for block in self.record_frames
                    )

    def _publish_status(self):
        now = time.time()

        with self.lock:
            rms = self.latest_rms
            recording = self.is_recording
            muted = now < self.mute_until

        if muted:
            status_text = "muted"
        elif recording:
            status_text = "recording"
        elif rms >= self.sound_threshold:
            status_text = "sound_detected"
        else:
            status_text = "quiet"

        self.publish_status_text(status_text)

    def publish_status_text(self, status_text):
        msg = String()
        msg.data = status_text
        self.status_publisher.publish(msg)

    def _save_worker(self):
        while True:
            audio = self.save_queue.get()

            if audio is None:
                break

            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = self.recordings_dir / f"cutie_recording_{timestamp}.wav"

                self._write_wav(filename, audio)

                file_msg = String()
                file_msg.data = str(filename)
                self.file_publisher.publish(file_msg)

                self.publish_status_text("recorded")

                self.get_logger().info(f"Recorded audio file: {filename}")

            except Exception as exc:
                self.publish_status_text("error")
                self.get_logger().error(f"Failed to save recording: {exc}")

    def _write_wav(self, path, audio):
        audio = np.clip(audio, -1.0, 1.0)
        audio_int16 = (audio * 32767).astype(np.int16)

        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

    def destroy_node(self):
        try:
            self.audio_stream.stop()
            self.audio_stream.close()
        except Exception as exc:
            self.get_logger().warn(f"Could not close audio stream cleanly: {exc}")

        self.save_queue.put(None)

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = CutieMicRecorderNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()