#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    display = LaunchConfiguration("display")
    xauthority = LaunchConfiguration("xauthority")

    mic_device_name_contains = LaunchConfiguration("mic_device_name_contains")
    mic_input_channels = LaunchConfiguration("mic_input_channels")
    mic_record_seconds = LaunchConfiguration("mic_record_seconds")
    mic_sound_threshold = LaunchConfiguration("mic_sound_threshold")

    self_speech_mute_enabled = LaunchConfiguration("self_speech_mute_enabled")
    mute_seconds_after_speaker_say = LaunchConfiguration("mute_seconds_after_speaker_say")
    speaking_seconds_per_word = LaunchConfiguration("speaking_seconds_per_word")
    min_self_speech_mute_seconds = LaunchConfiguration("min_self_speech_mute_seconds")
    max_self_speech_mute_seconds = LaunchConfiguration("max_self_speech_mute_seconds")

    stt_model = LaunchConfiguration("stt_model")
    stt_device = LaunchConfiguration("stt_device")
    stt_compute_type = LaunchConfiguration("stt_compute_type")
    stt_language = LaunchConfiguration("stt_language")

    llm_model = LaunchConfiguration("llm_model")
    ollama_url = LaunchConfiguration("ollama_url")
    llm_temperature = LaunchConfiguration("llm_temperature")
    llm_top_p = LaunchConfiguration("llm_top_p")
    llm_num_predict = LaunchConfiguration("llm_num_predict")
    llm_reply_word_limit = LaunchConfiguration("llm_reply_word_limit")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "display",
                default_value=":0",
                description="X display for Cutie touchscreen face.",
            ),
            DeclareLaunchArgument(
                "xauthority",
                default_value="/home/phoenix/.Xauthority",
                description="Xauthority file for GUI display access.",
            ),

            DeclareLaunchArgument(
                "mic_device_name_contains",
                default_value="reSpeaker XVF3800",
                description="Part of the ReSpeaker input device name used for automatic mic selection.",
            ),
            DeclareLaunchArgument(
                "mic_input_channels",
                default_value="2",
                description="Number of microphone input channels.",
            ),
            DeclareLaunchArgument(
                "mic_record_seconds",
                default_value="8.0",
                description="Length of each recorded speech chunk in seconds.",
            ),
            DeclareLaunchArgument(
                "mic_sound_threshold",
                default_value="0.016",
                description="RMS threshold for starting recording.",
            ),

            DeclareLaunchArgument(
                "self_speech_mute_enabled",
                default_value="true",
                description="Mute mic while Cutie is speaking to avoid hearing itself.",
            ),
            DeclareLaunchArgument(
                "mute_seconds_after_speaker_say",
                default_value="4.0",
                description="Extra mute time after estimated speaker duration.",
            ),
            DeclareLaunchArgument(
                "speaking_seconds_per_word",
                default_value="0.55",
                description="Estimated speaker duration per spoken word.",
            ),
            DeclareLaunchArgument(
                "min_self_speech_mute_seconds",
                default_value="5.0",
                description="Minimum mute duration whenever Cutie speaks.",
            ),
            DeclareLaunchArgument(
                "max_self_speech_mute_seconds",
                default_value="18.0",
                description="Maximum mute duration whenever Cutie speaks.",
            ),

            DeclareLaunchArgument(
                "stt_model",
                default_value="base.en",
                description="faster-whisper model size or local model path.",
            ),
            DeclareLaunchArgument(
                "stt_device",
                default_value="cpu",
                description="STT device: cpu or cuda.",
            ),
            DeclareLaunchArgument(
                "stt_compute_type",
                default_value="int8",
                description="STT compute type, usually int8 for CPU.",
            ),
            DeclareLaunchArgument(
                "stt_language",
                default_value="en",
                description="Speech language for STT.",
            ),

            DeclareLaunchArgument(
                "llm_model",
                default_value="llama3.2:3b",
                description="Local Ollama model for Cutie brain.",
            ),
            DeclareLaunchArgument(
                "ollama_url",
                default_value="http://localhost:11434/api/generate",
                description="Local Ollama generate API endpoint.",
            ),
            DeclareLaunchArgument(
                "llm_temperature",
                default_value="0.85",
                description="LLM creativity. Higher means more playful.",
            ),
            DeclareLaunchArgument(
                "llm_top_p",
                default_value="0.95",
                description="LLM sampling top_p.",
            ),
            DeclareLaunchArgument(
                "llm_num_predict",
                default_value="65",
                description="Maximum generated tokens for Cutie's reply.",
            ),
            DeclareLaunchArgument(
                "llm_reply_word_limit",
                default_value="26",
                description="Maximum spoken reply length in words.",
            ),

            SetEnvironmentVariable("DISPLAY", display),
            SetEnvironmentVariable("XAUTHORITY", xauthority),
            SetEnvironmentVariable("PYTHONUNBUFFERED", "1"),

            Node(
                package="cutie_mic",
                executable="cutie_mic_recorder",
                name="cutie_mic_recorder",
                output="screen",
                parameters=[
                    {
                        "device_name_contains": mic_device_name_contains,
                        "input_channels": ParameterValue(
                            mic_input_channels,
                            value_type=int,
                        ),
                        "record_seconds": ParameterValue(
                            mic_record_seconds,
                            value_type=float,
                        ),
                        "sound_threshold": ParameterValue(
                            mic_sound_threshold,
                            value_type=float,
                        ),
                        "self_speech_mute_enabled": ParameterValue(
                            self_speech_mute_enabled,
                            value_type=bool,
                        ),
                        "mute_seconds_after_speaker_say": ParameterValue(
                            mute_seconds_after_speaker_say,
                            value_type=float,
                        ),
                        "speaking_seconds_per_word": ParameterValue(
                            speaking_seconds_per_word,
                            value_type=float,
                        ),
                        "min_self_speech_mute_seconds": ParameterValue(
                            min_self_speech_mute_seconds,
                            value_type=float,
                        ),
                        "max_self_speech_mute_seconds": ParameterValue(
                            max_self_speech_mute_seconds,
                            value_type=float,
                        ),
                    }
                ],
            ),

            Node(
                package="cutie_speech",
                executable="cutie_stt",
                name="cutie_stt",
                output="screen",
                parameters=[
                    {
                        "model_size_or_path": stt_model,
                        "device": stt_device,
                        "compute_type": stt_compute_type,
                        "language": stt_language,
                    }
                ],
            ),

            Node(
                package="cutie_brain",
                executable="cutie_llm",
                name="cutie_llm",
                output="screen",
                parameters=[
                    {
                        "model": llm_model,
                        "ollama_url": ollama_url,
                        "temperature": ParameterValue(
                            llm_temperature,
                            value_type=float,
                        ),
                        "top_p": ParameterValue(
                            llm_top_p,
                            value_type=float,
                        ),
                        "num_predict": ParameterValue(
                            llm_num_predict,
                            value_type=int,
                        ),
                        "reply_word_limit": ParameterValue(
                            llm_reply_word_limit,
                            value_type=int,
                        ),
                    }
                ],
            ),

            Node(
                package="cutie_speaker",
                executable="cutie_speaker",
                name="cutie_speaker",
                output="screen",
            ),

            Node(
                package="cutie_face",
                executable="cutie_face",
                name="cutie_face",
                output="screen",
            ),
        ]
    )