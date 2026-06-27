#!/usr/bin/env python3

import time
import tkinter as tk

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

BACKGROUND_COLOR = "#07111f"
EYE_COLOR = "#9ee7ff"
EYE_OUTLINE = "#d7f7ff"
PUPIL_COLOR = "#07111f"
MOUTH_COLOR = "#ffb6d9"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#ffd166"
CHEEK_COLOR = "#ff8fab"
ERROR_COLOR = "#ff5c5c"


class CutieFaceApp(Node):
    def __init__(self):
        super().__init__("cutie_face")

        self.window = tk.Tk()
        self.window.title("Cutie Face App")
        self.window.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        self.window.resizable(False, False)

        self.is_fullscreen = True
        self.window.attributes("-fullscreen", self.is_fullscreen)

        self.canvas = tk.Canvas(
            self.window,
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            bg=BACKGROUND_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.is_running = True
        self.current_expression = "idle"
        self.expression_until = 0.0
        self.caption_text = "Hi, I am Cutie."
        self.pending_single_tap = None

        self.expression_order = [
            "idle",
            "happy",
            "listening",
            "thinking",
            "speaking",
            "sleepy",
            "confused",
            "error",
        ]

        self.expression_index = 0

        self.expression_drawers = {
            "idle": self.draw_idle_face,
            "happy": self.draw_happy_face,
            "listening": self.draw_listening_face,
            "thinking": self.draw_thinking_face,
            "speaking": self.draw_speaking_face,
            "sleepy": self.draw_sleepy_face,
            "confused": self.draw_confused_face,
            "error": self.draw_error_face,
        }

        self.create_subscription(
            String,
            "/cutie/face/state",
            self.face_state_callback,
            10,
        )

        self.create_subscription(
            String,
            "/cutie/audio/status",
            self.audio_status_callback,
            10,
        )

        self.create_subscription(
            String,
            "/cutie/speech/status",
            self.speech_status_callback,
            10,
        )

        self.create_subscription(
            String,
            "/cutie/brain/status",
            self.brain_status_callback,
            10,
        )

        self.create_subscription(
            String,
            "/cutie/speaker/say",
            self.speaker_say_callback,
            10,
        )

        self.register_controls()
        self.set_expression("idle")

        self.get_logger().info("Cutie face app started as a ROS2 node.")
        self.get_logger().info("Listening for robot state topics.")

    def register_controls(self):
        self.window.bind("q", self.close)
        self.window.bind("<Escape>", self.close)
        self.window.bind("f", self.toggle_fullscreen)

        self.window.bind("1", lambda event: self.request_expression("idle", force=True))
        self.window.bind("2", lambda event: self.request_expression("happy", force=True))
        self.window.bind(
            "3", lambda event: self.request_expression("listening", force=True)
        )
        self.window.bind(
            "4", lambda event: self.request_expression("thinking", force=True)
        )
        self.window.bind(
            "5", lambda event: self.request_expression("speaking", force=True)
        )
        self.window.bind(
            "6", lambda event: self.request_expression("sleepy", force=True)
        )
        self.window.bind(
            "7", lambda event: self.request_expression("confused", force=True)
        )
        self.window.bind("8", lambda event: self.request_expression("error", force=True))

        self.canvas.bind("<Button-1>", self.handle_screen_tap)
        self.canvas.bind("<Double-Button-1>", self.handle_screen_double_tap)

    def face_state_callback(self, msg):
        expression_name = msg.data.strip().lower()

        self.request_expression(
            expression_name,
            seconds=3.0,
            caption="Manual face state.",
            force=True,
        )

    def audio_status_callback(self, msg):
        status = msg.data.strip().lower()

        if status == "recording":
            self.request_expression(
                "listening",
                seconds=2.0,
                caption="I am listening...",
            )

        elif status == "error":
            self.request_expression(
                "error",
                seconds=3.0,
                caption="Audio error.",
            )

    def speech_status_callback(self, msg):
        status = msg.data.strip().lower()

        if status == "transcribing":
            self.request_expression(
                "thinking",
                seconds=4.0,
                caption="Thinking about what I heard...",
            )

        elif status == "transcribed":
            self.request_expression(
                "happy",
                seconds=1.5,
                caption="I heard you.",
            )

        elif status == "empty":
            self.request_expression(
                "confused",
                seconds=2.0,
                caption="Hmm, I did not catch that.",
            )

        elif status == "error":
            self.request_expression(
                "error",
                seconds=3.0,
                caption="Speech recognition error.",
            )

    def brain_status_callback(self, msg):
        status = msg.data.strip().lower()

        if status == "thinking":
            self.request_expression(
                "thinking",
                seconds=5.0,
                caption="Let me think...",
            )

        elif status == "responded":
            self.request_expression(
                "happy",
                seconds=1.5,
                caption="Here is my answer.",
            )

        elif status == "error":
            self.request_expression(
                "error",
                seconds=3.0,
                caption="Brain error.",
            )

    def speaker_say_callback(self, msg):
        text = msg.data.strip()

        if not text:
            return

        word_count = len(text.split())
        speaking_seconds = max(2.0, min(8.0, word_count * 0.35))

        self.request_expression(
            "speaking",
            seconds=speaking_seconds,
            caption=text,
            force=True,
        )

    def request_expression(self, expression_name, seconds=2.0, caption=None, force=False):
        if expression_name not in self.expression_drawers:
            print(f"[CutieFaceApp] Unknown expression: {expression_name}")
            return

        if caption is not None:
            self.caption_text = caption

        now = time.time()

        same_expression_is_active = (
            expression_name == self.current_expression
            and self.expression_until != 0.0
            and now < self.expression_until
        )

        if same_expression_is_active and not force:
            return

        self.set_expression(expression_name, seconds=seconds)

    def handle_screen_tap(self, event=None):
        if self.pending_single_tap is not None:
            return

        self.pending_single_tap = self.window.after(220, self.cycle_expression)

    def handle_screen_double_tap(self, event=None):
        if self.pending_single_tap is not None:
            self.window.after_cancel(self.pending_single_tap)
            self.pending_single_tap = None

        self.close()

    def cycle_expression(self):
        self.pending_single_tap = None

        self.expression_index = (self.expression_index + 1) % len(self.expression_order)
        next_expression = self.expression_order[self.expression_index]

        self.caption_text = "Manual face test mode."
        self.set_expression(next_expression)

    def set_expression(self, expression_name, seconds=0.0):
        if expression_name not in self.expression_drawers:
            print(f"[CutieFaceApp] Unknown expression: {expression_name}")
            return

        self.current_expression = expression_name

        if seconds > 0.0:
            self.expression_until = time.time() + seconds
        else:
            self.expression_until = 0.0

        if expression_name in self.expression_order:
            self.expression_index = self.expression_order.index(expression_name)

        self.expression_drawers[expression_name]()

    def return_to_idle_if_needed(self):
        if self.expression_until == 0.0:
            return

        if time.time() < self.expression_until:
            return

        self.expression_until = 0.0
        self.caption_text = "Hi, I am Cutie."
        self.set_expression("idle")

    def ros_tick(self):
        if not self.is_running:
            return

        rclpy.spin_once(self, timeout_sec=0.0)
        self.return_to_idle_if_needed()
        self.window.after(50, self.ros_tick)

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.window.attributes("-fullscreen", self.is_fullscreen)

    def close(self, event=None):
        self.is_running = False
        self.window.destroy()

    def clear_screen(self):
        self.canvas.delete("all")

    def draw_header(self, expression_label):
        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            45,
            text="CUTIE",
            fill=EYE_COLOR,
            font=("Arial", 32, "bold"),
        )

        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            85,
            text=expression_label,
            fill=TEXT_COLOR,
            font=("Arial", 16),
        )

    def draw_footer(self):
        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            560,
            text=self.caption_text,
            fill=TEXT_COLOR,
            font=("Arial", 14),
            width=SCREEN_WIDTH - 100,
        )

    def draw_eye(self, x1, y1, x2, y2, pupil_offset_x=0, pupil_offset_y=0):
        self.canvas.create_oval(
            x1,
            y1,
            x2,
            y2,
            fill=EYE_COLOR,
            outline=EYE_OUTLINE,
            width=4,
        )

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        pupil_radius = 16

        self.canvas.create_oval(
            center_x - pupil_radius + pupil_offset_x,
            center_y - pupil_radius + pupil_offset_y,
            center_x + pupil_radius + pupil_offset_x,
            center_y + pupil_radius + pupil_offset_y,
            fill=PUPIL_COLOR,
            outline=PUPIL_COLOR,
        )

    def draw_closed_eye(self, x1, y, x2):
        self.canvas.create_arc(
            x1,
            y - 40,
            x2,
            y + 40,
            start=200,
            extent=140,
            style=tk.ARC,
            outline=EYE_COLOR,
            width=8,
        )

    def draw_smile(self, y_offset=0, width=8):
        self.canvas.create_arc(
            370,
            330 + y_offset,
            654,
            500 + y_offset,
            start=200,
            extent=140,
            style=tk.ARC,
            outline=MOUTH_COLOR,
            width=width,
        )

    def draw_open_mouth(self):
        self.canvas.create_oval(
            442,
            370,
            582,
            470,
            fill=MOUTH_COLOR,
            outline="#ffd6e8",
            width=5,
        )

        self.canvas.create_oval(
            477,
            395,
            547,
            455,
            fill=BACKGROUND_COLOR,
            outline=BACKGROUND_COLOR,
        )

    def draw_idle_face(self):
        self.clear_screen()
        self.draw_header("Idle facial expression")

        self.draw_eye(250, 190, 390, 330)
        self.draw_eye(634, 190, 774, 330)
        self.draw_smile()

        self.draw_footer()

    def draw_happy_face(self):
        self.clear_screen()
        self.draw_header("Happy facial expression")

        self.draw_eye(235, 175, 395, 335, pupil_offset_y=-4)
        self.draw_eye(629, 175, 789, 335, pupil_offset_y=-4)

        self.canvas.create_oval(
            185,
            325,
            245,
            385,
            fill=CHEEK_COLOR,
            outline=CHEEK_COLOR,
        )

        self.canvas.create_oval(
            779,
            325,
            839,
            385,
            fill=CHEEK_COLOR,
            outline=CHEEK_COLOR,
        )

        self.canvas.create_arc(
            335,
            300,
            689,
            520,
            start=200,
            extent=140,
            style=tk.ARC,
            outline=MOUTH_COLOR,
            width=11,
        )

        self.draw_footer()

    def draw_listening_face(self):
        self.clear_screen()
        self.draw_header("Listening facial expression")

        self.draw_eye(250, 190, 390, 330, pupil_offset_y=-10)
        self.draw_eye(634, 190, 774, 330, pupil_offset_y=-10)

        self.canvas.create_arc(
            135,
            220,
            245,
            330,
            start=290,
            extent=140,
            style=tk.ARC,
            outline=ACCENT_COLOR,
            width=5,
        )

        self.canvas.create_arc(
            90,
            190,
            280,
            360,
            start=290,
            extent=140,
            style=tk.ARC,
            outline=ACCENT_COLOR,
            width=4,
        )

        self.canvas.create_arc(
            779,
            220,
            889,
            330,
            start=110,
            extent=140,
            style=tk.ARC,
            outline=ACCENT_COLOR,
            width=5,
        )

        self.canvas.create_arc(
            744,
            190,
            934,
            360,
            start=110,
            extent=140,
            style=tk.ARC,
            outline=ACCENT_COLOR,
            width=4,
        )

        self.canvas.create_line(
            430,
            430,
            594,
            430,
            fill=MOUTH_COLOR,
            width=7,
            capstyle=tk.ROUND,
        )

        self.draw_footer()

    def draw_thinking_face(self):
        self.clear_screen()
        self.draw_header("Thinking facial expression")

        self.draw_eye(250, 190, 390, 330, pupil_offset_x=-6)
        self.draw_eye(634, 190, 774, 330, pupil_offset_x=6)

        self.canvas.create_arc(
            390,
            360,
            634,
            470,
            start=200,
            extent=140,
            style=tk.ARC,
            outline=MOUTH_COLOR,
            width=7,
        )

        self.canvas.create_oval(
            430,
            145,
            455,
            170,
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR,
        )

        self.canvas.create_oval(
            500,
            125,
            535,
            160,
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR,
        )

        self.canvas.create_oval(
            590,
            105,
            635,
            150,
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR,
        )

        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            505,
            text="thinking...",
            fill=ACCENT_COLOR,
            font=("Arial", 22, "bold"),
        )

        self.draw_footer()

    def draw_speaking_face(self):
        self.clear_screen()
        self.draw_header("Speaking facial expression")

        self.draw_eye(250, 190, 390, 330)
        self.draw_eye(634, 190, 774, 330)

        self.draw_open_mouth()

        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            510,
            text="speaking...",
            fill=ACCENT_COLOR,
            font=("Arial", 22, "bold"),
        )

        self.draw_footer()

    def draw_sleepy_face(self):
        self.clear_screen()
        self.draw_header("Sleepy facial expression")

        self.draw_closed_eye(250, 260, 390)
        self.draw_closed_eye(634, 260, 774)

        self.canvas.create_arc(
            430,
            360,
            594,
            465,
            start=200,
            extent=140,
            style=tk.ARC,
            outline=MOUTH_COLOR,
            width=7,
        )

        self.canvas.create_text(
            735,
            145,
            text="Z",
            fill=ACCENT_COLOR,
            font=("Arial", 30, "bold"),
        )

        self.canvas.create_text(
            780,
            105,
            text="z",
            fill=ACCENT_COLOR,
            font=("Arial", 24, "bold"),
        )

        self.canvas.create_text(
            815,
            75,
            text="z",
            fill=ACCENT_COLOR,
            font=("Arial", 18, "bold"),
        )

        self.draw_footer()

    def draw_confused_face(self):
        self.clear_screen()
        self.draw_header("Confused facial expression")

        self.draw_eye(250, 190, 390, 330, pupil_offset_x=-10, pupil_offset_y=6)
        self.draw_eye(634, 190, 774, 330, pupil_offset_x=12, pupil_offset_y=-8)

        self.canvas.create_line(
            245,
            165,
            390,
            135,
            fill=ACCENT_COLOR,
            width=8,
            capstyle=tk.ROUND,
        )

        self.canvas.create_line(
            634,
            135,
            779,
            165,
            fill=ACCENT_COLOR,
            width=8,
            capstyle=tk.ROUND,
        )

        self.canvas.create_line(
            420,
            430,
            470,
            410,
            520,
            430,
            570,
            410,
            620,
            430,
            fill=MOUTH_COLOR,
            width=7,
            smooth=True,
            capstyle=tk.ROUND,
        )

        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            505,
            text="?",
            fill=ACCENT_COLOR,
            font=("Arial", 42, "bold"),
        )

        self.draw_footer()

    def draw_error_face(self):
        self.clear_screen()
        self.draw_header("Error facial expression")

        self.draw_eye(250, 190, 390, 330, pupil_offset_y=8)
        self.draw_eye(634, 190, 774, 330, pupil_offset_y=8)

        self.canvas.create_line(
            430,
            435,
            594,
            435,
            fill=ERROR_COLOR,
            width=8,
            capstyle=tk.ROUND,
        )

        self.canvas.create_text(
            SCREEN_WIDTH // 2,
            505,
            text="!",
            fill=ERROR_COLOR,
            font=("Arial", 48, "bold"),
        )

        self.draw_footer()

    def run(self):
        self.window.after(50, self.ros_tick)
        self.window.mainloop()


def main(args=None):
    rclpy.init(args=args)

    app = CutieFaceApp()

    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        app.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()