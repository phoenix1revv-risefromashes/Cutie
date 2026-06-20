#!/usr/bin/env python3

import tkinter as tk


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


class CutieFaceApp:
    def __init__(self):
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

        self.current_expression = "idle"

        self.expression_order = [
            "idle",
            "happy",
            "listening",
            "speaking",
            "sleepy",
            "confused",
        ]

        self.expression_index = 0
        self.pending_single_tap = None

        self.expression_drawers = {
            "idle": self.draw_idle_face,
            "happy": self.draw_happy_face,
            "listening": self.draw_listening_face,
            "speaking": self.draw_speaking_face,
            "sleepy": self.draw_sleepy_face,
            "confused": self.draw_confused_face,
        }

        self.register_controls()
        self.set_expression("idle")

    def register_controls(self):
        self.window.bind("q", self.close)
        self.window.bind("<Escape>", self.close)
        self.window.bind("f", self.toggle_fullscreen)

        self.window.bind("1", lambda event: self.set_expression("idle"))
        self.window.bind("2", lambda event: self.set_expression("happy"))
        self.window.bind("3", lambda event: self.set_expression("listening"))
        self.window.bind("4", lambda event: self.set_expression("speaking"))
        self.window.bind("5", lambda event: self.set_expression("sleepy"))
        self.window.bind("6", lambda event: self.set_expression("confused"))

        self.canvas.bind("<Button-1>", self.handle_screen_tap)
        self.canvas.bind("<Double-Button-1>", self.handle_screen_double_tap)

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

        self.set_expression(next_expression)

    def set_expression(self, expression_name):
        if expression_name not in self.expression_drawers:
            print(f"[CutieFaceApp] Unknown expression: {expression_name}")
            return

        self.current_expression = expression_name

        if expression_name in self.expression_order:
            self.expression_index = self.expression_order.index(expression_name)

        self.expression_drawers[expression_name]()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.window.attributes("-fullscreen", self.is_fullscreen)

    def close(self, event=None):
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
            text="Tap: Next Expression | Double Tap: Quit | f Fullscreen | q/Esc Quit",
            fill=TEXT_COLOR,
            font=("Arial", 14),
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

    def run(self):
        self.window.mainloop()


def main():
    app = CutieFaceApp()
    app.run()


if __name__ == "__main__":
    main()