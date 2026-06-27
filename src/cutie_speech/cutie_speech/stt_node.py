#!/usr/bin/env python3

from pathlib import Path

import rclpy
from faster_whisper import WhisperModel
from rclpy.node import Node
from std_msgs.msg import String


class CutieSttNode(Node):
    def __init__(self):
        super().__init__("cutie_stt")

        self.declare_parameter("model_size_or_path", "base.en")
        self.declare_parameter("device", "cpu")
        self.declare_parameter("compute_type", "int8")
        self.declare_parameter("language", "en")
        self.declare_parameter("beam_size", 1)
        self.declare_parameter("use_vad", True)

        self.declare_parameter("min_transcript_chars", 3)
        self.declare_parameter("min_transcript_words", 1)

        self.model_size_or_path = str(self.get_parameter("model_size_or_path").value)
        self.device = str(self.get_parameter("device").value)
        self.compute_type = str(self.get_parameter("compute_type").value)
        self.language = str(self.get_parameter("language").value)
        self.beam_size = int(self.get_parameter("beam_size").value)
        self.use_vad = bool(self.get_parameter("use_vad").value)

        self.min_transcript_chars = int(
            self.get_parameter("min_transcript_chars").value
        )
        self.min_transcript_words = int(
            self.get_parameter("min_transcript_words").value
        )

        self.transcript_publisher = self.create_publisher(
            String,
            "/cutie/speech/text",
            10,
        )

        self.status_publisher = self.create_publisher(
            String,
            "/cutie/speech/status",
            10,
        )

        self.audio_file_subscription = self.create_subscription(
            String,
            "/cutie/audio/file",
            self.audio_file_callback,
            10,
        )

        self.publish_status("loading_model")

        self.get_logger().info("Loading faster-whisper model...")
        self.get_logger().info(f"Model: {self.model_size_or_path}")
        self.get_logger().info(f"Device: {self.device}")
        self.get_logger().info(f"Compute type: {self.compute_type}")

        self.model = WhisperModel(
            self.model_size_or_path,
            device=self.device,
            compute_type=self.compute_type,
        )

        self.publish_status("ready")

        self.get_logger().info("Cutie STT node started.")
        self.get_logger().info("Subscribing to /cutie/audio/file")
        self.get_logger().info("Publishing to /cutie/speech/text")

    def audio_file_callback(self, msg):
        audio_path = Path(msg.data).expanduser()

        if not audio_path.exists():
            self.publish_status("error")
            self.get_logger().error(f"Audio file not found: {audio_path}")
            return

        self.publish_status("transcribing")
        self.get_logger().info(f"Transcribing audio file: {audio_path}")

        try:
            transcript = self.transcribe_audio(audio_path)
        except Exception as exc:
            self.publish_status("error")
            self.get_logger().error(f"STT failed: {exc}")
            return

        transcript = transcript.strip()

        if not self.is_valid_transcript(transcript):
            self.publish_status("empty")
            self.get_logger().warn(f"Ignored weak/noise transcript: {transcript}")
            return

        transcript_msg = String()
        transcript_msg.data = transcript

        self.transcript_publisher.publish(transcript_msg)

        self.publish_status("transcribed")
        self.get_logger().info(f"Published transcript: {transcript}")

    def transcribe_audio(self, audio_path):
        segments, info = self.model.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=self.use_vad,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
        )

        transcript_parts = []

        for segment in segments:
            text = segment.text.strip()

            if text:
                transcript_parts.append(text)

        return " ".join(transcript_parts).strip()

    def is_valid_transcript(self, transcript):
        cleaned = transcript.strip().lower()

        if len(cleaned) < self.min_transcript_chars:
            return False

        words = cleaned.split()

        if len(words) < self.min_transcript_words:
            return False

        blocked_exact_transcripts = {
            "you",
            "ok",
            "okay",
            "um",
            "uh",
            "hmm",
            "mm",
            "music",
            "noise",
        }

        blocked_phrases = [
            "thanks for watching",
            "thank you for watching",
            "subscribe",
            "subtitles",
            "captioned by",
            "amara.org",
        ]

        if cleaned in blocked_exact_transcripts:
            return False

        for phrase in blocked_phrases:
            if phrase in cleaned:
                return False

        return True

    def publish_status(self, status_text):
        msg = String()
        msg.data = status_text
        self.status_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = CutieSttNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()