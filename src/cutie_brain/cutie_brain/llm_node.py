#!/usr/bin/env python3

import json
import random
import re
import time
import urllib.request

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class CutieLlmNode(Node):
    def __init__(self):
        super().__init__("cutie_llm")

        self.declare_parameter("ollama_url", "http://localhost:11434/api/generate")
        self.declare_parameter("model", "llama3.2:3b")
        self.declare_parameter("temperature", 0.85)
        self.declare_parameter("top_p", 0.95)
        self.declare_parameter("num_predict", 65)
        self.declare_parameter("keep_alive", "30m")
        self.declare_parameter("repeat_cooldown_seconds", 8.0)
        self.declare_parameter("robot_echo_cooldown_seconds", 12.0)
        self.declare_parameter("min_user_text_chars", 3)
        self.declare_parameter("reply_word_limit", 26)

        self.ollama_url = str(self.get_parameter("ollama_url").value)
        self.model = str(self.get_parameter("model").value)
        self.temperature = float(self.get_parameter("temperature").value)
        self.top_p = float(self.get_parameter("top_p").value)
        self.num_predict = int(self.get_parameter("num_predict").value)
        self.keep_alive = str(self.get_parameter("keep_alive").value)
        self.repeat_cooldown_seconds = float(
            self.get_parameter("repeat_cooldown_seconds").value
        )
        self.robot_echo_cooldown_seconds = float(
            self.get_parameter("robot_echo_cooldown_seconds").value
        )
        self.min_user_text_chars = int(self.get_parameter("min_user_text_chars").value)
        self.reply_word_limit = int(self.get_parameter("reply_word_limit").value)

        self.last_user_text = ""
        self.last_robot_response_text = ""
        self.last_response_time = 0.0

        self.phoenix_lab_context = self.build_phoenix_lab_context()

        self.speech_subscription = self.create_subscription(
            String,
            "/cutie/speech/text",
            self.speech_callback,
            10,
        )

        self.response_publisher = self.create_publisher(
            String,
            "/cutie/response/text",
            10,
        )

        self.speaker_publisher = self.create_publisher(
            String,
            "/cutie/speaker/say",
            10,
        )

        self.status_publisher = self.create_publisher(
            String,
            "/cutie/brain/status",
            10,
        )

        self.get_logger().info("Cutie LLM node started.")
        self.get_logger().info("Subscribing to /cutie/speech/text")
        self.get_logger().info("Publishing to /cutie/response/text")
        self.get_logger().info("Publishing to /cutie/speaker/say")
        self.get_logger().info(f"Using local Ollama model: {self.model}")
        self.get_logger().info("Phoenix Lab knowledge loaded.")

    def build_phoenix_lab_context(self):
        return """
Phoenix Lab is Phoenix's personal robotics and AI lab.

Phoenix Lab focuses on building practical, real-world robotics systems using ROS2, Linux, embedded hardware, computer vision, audio, speech, and local AI.

The main current robot project is Cutie, also connected to the RoboHost idea.

Cutie is a fun humanoid robot greeter designed for public demos, lobbies, events, interviews, and robotics integration showcases.

Cutie can listen through a ReSpeaker XVF3800 4-mic array, record speech, transcribe it locally, generate a response locally, speak through a speaker, and show facial expressions on a touchscreen display.

Cutie's current pipeline is:
human voice -> cutie_mic_recorder -> /cutie/audio/file -> cutie_stt -> /cutie/speech/text -> cutie_llm -> /cutie/speaker/say -> cutie_speaker.

Cutie also has a visual face system that reacts to states like idle, listening, thinking, speaking, happy, confused, sleepy, and error.

Cutie's hardware includes a Jetson Orin Nano, ReSpeaker XVF3800 4-Mic Array, USB speaker, touchscreen display, Logitech camera, and robotics components.

Cutie's software stack includes Ubuntu Linux, ROS2 Humble, Python, Tkinter, faster-whisper for local speech-to-text, Ollama for local language model responses, and a local TTS speaker system.

Phoenix created Cutie and Phoenix Lab.

Phoenix is building Cutie to demonstrate robotics integration skills: connecting hardware, Linux, ROS2 nodes, audio devices, local AI, speech, display, and debugging into one working robot system.

Cutie should sound friendly, playful, funny, slightly cheeky, and demo-ready. Cutie should not sound like a boring assistant.
""".strip()

    def speech_callback(self, msg):
        user_text = msg.data.strip()

        if not self.is_valid_user_text(user_text):
            self.publish_status("ignored_empty")
            self.get_logger().warn(f"Ignored weak input: {user_text}")
            return

        if self.looks_like_robot_echo(user_text):
            self.publish_status("ignored_robot_echo")
            self.get_logger().warn(f"Ignored likely robot echo: {user_text}")
            return

        if self.is_repeated_too_soon(user_text):
            self.publish_status("ignored_repeat")
            self.get_logger().warn(f"Ignored repeated transcript: {user_text}")
            return

        self.last_user_text = user_text
        self.last_response_time = time.time()

        scripted_response = self.get_scripted_response(user_text)

        if scripted_response:
            self.publish_status("scripted_response")
            self.publish_cutie_response(scripted_response)
            self.get_logger().info(f"Scripted Cutie response: {scripted_response}")
            return

        self.publish_status("thinking")
        self.get_logger().info(f"User said: {user_text}")

        try:
            response_text = self.generate_response(user_text)
        except Exception as exc:
            self.publish_status("error")
            self.get_logger().error(f"LLM failed: {exc}")
            response_text = random.choice(
                [
                    "My tiny robot brain slipped on a banana peel. Say that again?",
                    "Oops, my circuits got dramatic. Please repeat that for me.",
                    "I almost had it, then my thoughts took a coffee break.",
                ]
            )

        response_text = self.clean_response(response_text)
        self.publish_cutie_response(response_text)

        self.publish_status("responded")
        self.get_logger().info(f"Cutie response: {response_text}")

    def get_scripted_response(self, user_text):
        normalized = self.normalize_text(user_text)

        creator_patterns = [
            "who created you",
            "who made you",
            "who built you",
            "who designed you",
            "who developed you",
            "who programmed you",
            "who is your creator",
            "who created cutie",
            "who made cutie",
            "who built cutie",
        ]

        for pattern in creator_patterns:
            if pattern in normalized:
                return random.choice(
                    [
                        "Phoenix created me. I am his adorable robot greeter with premium chaos energy.",
                        "Phoenix built me. I am basically Phoenix Lab's tiny robot celebrity.",
                        "I was created by Phoenix. He gave me a face, a voice, and dangerous levels of cuteness.",
                    ]
                )

        phoenix_lab_patterns = [
            "what is phoenix lab",
            "tell me about phoenix lab",
            "what is the phoenix lab",
            "explain phoenix lab",
            "what do you know about phoenix lab",
            "what happens in phoenix lab",
            "what is this lab",
        ]

        for pattern in phoenix_lab_patterns:
            if pattern in normalized:
                return random.choice(
                    [
                        "Phoenix Lab is Phoenix's robotics and AI lab, where Cutie was born and chaos became adorable.",
                        "Phoenix Lab builds real robot systems with ROS2, Linux, sensors, speech, vision, and local AI.",
                        "Phoenix Lab is where Phoenix turns wires, code, and questionable sleep into working robots like me.",
                    ]
                )

        cutie_patterns = [
            "what is cutie",
            "tell me about cutie",
            "what can cutie do",
            "what can you do",
            "what are you",
            "explain yourself",
        ]

        for pattern in cutie_patterns:
            if pattern in normalized:
                return random.choice(
                    [
                        "I am Cutie, Phoenix Lab's robot greeter. I listen, think, talk, and look cute under pressure.",
                        "I am a ROS2 robot host with a mic, speaker, face, local AI, and a very dramatic personality.",
                        "I can hear visitors, transcribe speech, generate replies, speak back, and make Phoenix look suspiciously talented.",
                    ]
                )

        hardware_patterns = [
            "what hardware",
            "what parts",
            "what components",
            "what are you made of",
            "what devices",
            "what is inside you",
        ]

        for pattern in hardware_patterns:
            if pattern in normalized:
                return random.choice(
                    [
                        "I use a Jetson Orin Nano, ReSpeaker mic array, speaker, touchscreen face, camera, and a lot of Phoenix patience.",
                        "My body is part robot, part Linux, part ROS2, and part Phoenix refusing to give up.",
                        "I have a mic array, speaker, display face, camera, Jetson brain, and enough wiring to scare a toaster.",
                    ]
                )

        pipeline_patterns = [
            "how do you work",
            "how does cutie work",
            "what is your pipeline",
            "how is your system connected",
            "how does the system work",
        ]

        for pattern in pipeline_patterns:
            if pattern in normalized:
                return random.choice(
                    [
                        "Voice comes in, STT turns it into text, my brain replies, then my speaker says it dramatically.",
                        "My ROS2 pipeline listens, transcribes, thinks locally, speaks, and changes my face like a tiny theater kid.",
                        "I run through ROS2 nodes for mic, speech, brain, speaker, and face. Very fancy, very cute.",
                    ]
                )

        if "hello" in normalized or "hi cutie" in normalized or normalized == "hi":
            return random.choice(
                [
                    "Hi there! I am Cutie, Phoenix Lab's friendliest tiny robot troublemaker.",
                    "Hello! I am Cutie. Please imagine sparkles; my display budget is still improving.",
                    "Hi! Welcome to Phoenix Lab, where robots talk and wires develop personalities.",
                ]
            )

        if "how are you" in normalized:
            return random.choice(
                [
                    "I am fantastic. My circuits are caffeinated and emotionally available.",
                    "I am doing great. My robot soul is sparkling today.",
                    "I am alive, adorable, and only slightly overclocked.",
                ]
            )

        if "tell me a joke" in normalized or "make me laugh" in normalized:
            return random.choice(
                [
                    "Why did the robot blush? Someone checked its cache.",
                    "I told my servo a joke. It said it was moved.",
                    "My favorite exercise is a power cycle. Very refreshing.",
                ]
            )

        return ""

    def publish_cutie_response(self, response_text):
        response_text = self.clean_response(response_text)

        response_msg = String()
        response_msg.data = response_text

        self.response_publisher.publish(response_msg)
        self.speaker_publisher.publish(response_msg)

        self.last_robot_response_text = response_text
        self.last_response_time = time.time()

    def is_valid_user_text(self, user_text):
        cleaned = user_text.strip().lower()

        if len(cleaned) < self.min_user_text_chars:
            return False

        blocked_inputs = {
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

        if cleaned in blocked_inputs:
            return False

        blocked_phrases = [
            "thanks for watching",
            "thank you for watching",
            "subscribe",
            "subtitles",
            "captioned by",
            "amara.org",
        ]

        for phrase in blocked_phrases:
            if phrase in cleaned:
                return False

        return True

    def is_repeated_too_soon(self, user_text):
        now = time.time()

        same_as_last = user_text.lower() == self.last_user_text.lower()
        still_in_cooldown = (
            now - self.last_response_time
        ) < self.repeat_cooldown_seconds

        return same_as_last and still_in_cooldown

    def normalize_text(self, text):
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = " ".join(text.split())
        return text

    def looks_like_robot_echo(self, user_text):
        now = time.time()

        if now - self.last_response_time > self.robot_echo_cooldown_seconds:
            return False

        normalized_user_text = self.normalize_text(user_text)
        normalized_robot_text = self.normalize_text(self.last_robot_response_text)

        if not normalized_user_text or not normalized_robot_text:
            return False

        user_words = set(normalized_user_text.split())
        robot_words = set(normalized_robot_text.split())

        if not user_words or not robot_words:
            return False

        overlap = user_words.intersection(robot_words)
        overlap_ratio = len(overlap) / len(user_words)

        same_as_robot_response = normalized_user_text == normalized_robot_text
        mostly_robot_words = overlap_ratio >= 0.7 and len(user_words) >= 3

        return same_as_robot_response or mostly_robot_words

    def generate_response(self, user_text):
        system_prompt = (
            "You are Cutie, the playful humanoid robot host for Phoenix Lab. "
            "Phoenix created you. "
            "Your main job is to explain Phoenix Lab, Cutie, RoboHost, robotics projects, hardware, software, and demos. "
            "Use the Phoenix Lab context below as your source of truth. "
            "You are warm, funny, charming, slightly cheeky, and demo-ready. "
            "You sound like a cute robot host, not a boring assistant. "
            "Use light humor when appropriate. "
            "Never be rude, creepy, mean, or too sarcastic. "
            "Keep replies short because you are speaking through a robot speaker. "
            "Do not use markdown, bullet points, emojis, stage directions, or long explanations. "
            "Do not say you are an AI language model.\n\n"
            "Phoenix Lab context:\n"
            f"{self.phoenix_lab_context}"
        )

        prompt = (
            f"The visitor said: {user_text}\n\n"
            f"Reply in one natural, funny spoken sentence under {self.reply_word_limit} words. "
            "When the visitor asks about Phoenix Lab, Cutie, Phoenix, hardware, software, or the demo, answer confidently from the context."
        )

        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.num_predict,
                "repeat_penalty": 1.08,
            },
        }

        request_data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.ollama_url,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            response_data = response.read().decode("utf-8")

        parsed_response = json.loads(response_data)

        return parsed_response.get("response", "").strip()

    def clean_response(self, response_text):
        response_text = response_text.strip()
        response_text = response_text.replace("\n", " ")
        response_text = " ".join(response_text.split())

        response_text = response_text.strip('"')
        response_text = response_text.strip("'")

        if not response_text:
            return random.choice(
                [
                    "I heard you, but my tiny robot brain needs one more try.",
                    "Hmm, my circuits blinked. Say that again for me.",
                    "I almost caught that, then my robot thoughts tripped.",
                ]
            )

        words = response_text.split()

        if len(words) > self.reply_word_limit + 8:
            response_text = " ".join(words[: self.reply_word_limit + 8])
            response_text = response_text.rstrip(".,!?") + "."

        return response_text

    def publish_status(self, status_text):
        msg = String()
        msg.data = status_text
        self.status_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = CutieLlmNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()