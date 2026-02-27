# neosnake-animation.py
# Neo Snake Animation - Multiple rainbow snakes in random motion with turns
# pip install textual
# python3 neosnake-animation.py

import random
from typing import Tuple, List, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.events import Key
from textual.timer import Timer
from rich.text import Text

DIRS = {
    "right": (1, 0),
    "left": (-1, 0),
    "down": (0, 1),
    "up": (0, -1),
}

HEAD_CHARS = {
    (1, 0): '▶',   # right
    (-1, 0): '◀',  # left
    (0, 1): '▼',   # down
    (0, -1): '▲',  # up
}

TURN_PROB = 0.15  # chance to turn each step
NUM_SNAKES = 5
MIN_LENGTH = 10
MAX_LENGTH = 30

class Snake:
    def __init__(self, width: int, height: int, hue_start: int):
        self.width = width
        self.height = height
        self.hue_start = hue_start
        start_x = random.randint(0, width - 1)
        start_y = random.randint(0, height - 1)
        self.dir: Tuple[int, int] = random.choice(list(DIRS.values()))
        length = random.randint(MIN_LENGTH, MAX_LENGTH)
        self.body: List[Tuple[int, int]] = []
        for i in range(length):
            px = (start_x - i * self.dir[0]) % self.width
            py = (start_y - i * self.dir[1]) % self.height
            self.body.append((px, py))

    def move(self):
        # Random turn?
        if random.random() < TURN_PROB:
            # Turn left or right (90 degrees)
            turns = [(-self.dir[1], self.dir[0]), (self.dir[1], -self.dir[0])]
            self.dir = random.choice(turns)

        # Move head
        hx, hy = self.body[0]
        nx = (hx + self.dir[0]) % self.width
        ny = (hy + self.dir[1]) % self.height
        self.body.insert(0, (nx, ny))

        # Occasionally grow or shrink for variety
        if random.random() < 0.02:
            # Grow
            pass  # just don't pop
        elif random.random() < 0.01 and len(self.body) > MIN_LENGTH:
            # Shrink
            self.body.pop()
            self.body.pop()  # pop twice to shrink
        else:
            # Normal: pop tail
            self.body.pop()

class NeoSnakeAnimation(App):
    """Neo Snake Animation - Multiple snakes in random motion with revolutions/turns"""

    CSS = """
    Screen {
        background: #000;
    }
    Header {
        background: #001a00;
        color: lime;
        dock: top;
    }
    Static#playfield {
        background: #000;
        color: #0a0;
        width: 100%;
        height: 1fr;
        padding: 0;
        margin: 0;
    }
    Footer {
        background: #001a00;
        color: lime;
        dock: bottom;
    }
    """

    def __init__(self):
        super().__init__()
        self.WIDTH = 100
        self.HEIGHT = 30
        self.snakes: List[Snake] = []
        self.animation_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="playfield")
        yield Footer()

    def on_mount(self) -> None:
        self.playfield = self.query_one(Static)
        self.title = "🐍 Neo Snake Animation | Q/Esc=Quit | P=Pause"
        
        # Initialize multiple snakes with different hue starts
        for i in range(NUM_SNAKES):
            hue_start = i * (360 // NUM_SNAKES)
            self.snakes.append(Snake(self.WIDTH, self.HEIGHT, hue_start))
        
        self.speed = 0.08  # faster for animation
        self.animation_timer = self.set_interval(self.speed, self.update_snakes)
        self.update_display()

    def update_snakes(self) -> None:
        for snake in self.snakes:
            snake.move()
        self.update_display()

    def update_display(self) -> None:
        lines: List[Text] = []
        # Collect all snake positions (overlaps will show last drawn)
        for y in range(self.HEIGHT):
            line = Text()
            for x in range(self.WIDTH):
                ch = " "
                style = "#0003"
                for snake in self.snakes:
                    if (x, y) in snake.body:
                        idx = snake.body.index((x, y))
                        ch, style = self._get_snake_char_style(snake, idx)
                        break  # first snake wins overlap
                line.append(ch, style)
            lines.append(line)
        self.playfield.update("\n".join(str(line) for line in lines))

    def _get_snake_char_style(self, snake: Snake, idx: int) -> Tuple[str, str]:
        if idx == 0:  # head
            ch = HEAD_CHARS[snake.dir]
            return ch, f"bold hsl({snake.hue_start}, 100%, 70%)"  # neon head
        n_segs = len(snake.body)
        if idx == n_segs - 1:  # tail
            return "‚", "dim"  # comma-like tail
        # body segment
        prev_pos = snake.body[idx - 1]
        next_pos = snake.body[idx + 1]
        dir_in = (
            snake.body[idx][0] - prev_pos[0],
            snake.body[idx][1] - prev_pos[1],
        )
        dir_out = (
            next_pos[0] - snake.body[idx][0],
            next_pos[1] - snake.body[idx][1],
        )
        if dir_in == dir_out:
            # straight
            ch = "─" if dir_in[0] != 0 else "│"
        else:
            # bend
            to_prev_dir = (-dir_in[0], -dir_in[1])
            to_next_dir = dir_out
            ch = self._get_bend_char(to_prev_dir, to_next_dir)
        # rainbow style
        hue = (snake.hue_start + idx * 12) % 360
        brightness = max(25, 65 - (idx / n_segs) * 45)  # fade to tail
        style = f"hsl({hue}, 90%, {brightness}%)"
        return ch, style

    def _get_bend_char(self, arm1: Tuple[int, int], arm2: Tuple[int, int]) -> str:
        arms = {arm1, arm2}
        if arms == {(1, 0), (0, 1)}:
            return "┌"
        if arms == {(-1, 0), (0, 1)}:
            return "┐"
        if arms == {(1, 0), (0, -1)}:
            return "└"
        if arms == {(-1, 0), (0, -1)}:
            return "┘"
        return "+"

    def on_key(self, event: Key) -> None:
        key = event.key.lower()
        if key in ("p", "space"):
            if self.animation_timer and self.animation_timer.is_active:
                self.animation_timer.stop()
                self.title = self.title.replace("Animation", "Animation ⏸️ PAUSED")
            else:
                self.animation_timer = self.set_interval(self.speed, self.update_snakes)
                self.title = self.title.replace(" ⏸️ PAUSED", "")
        elif key in ("q", "escape"):
            self.exit()


if __name__ == "__main__":
    app = NeoSnakeAnimation()
    app.run()