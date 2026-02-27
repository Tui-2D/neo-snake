# neosnake-rainbow-animation.py
# Multiple colorful snakes in random motion – vibrant rainbow edition
# python3 neosnake-rainbow-animation.py

import random
from typing import Tuple, List, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.events import Key
from textual.timer import Timer
from rich.text import Text

DIRS = [(1,0), (-1,0), (0,1), (0,-1)]

HEAD_CHARS = {
    (1, 0):  '▶',
    (-1, 0): '◀',
    (0, 1):  '▼',
    (0, -1): '▲',
}

TURN_PROB = 0.18          # slightly more chaotic turns
GROW_PROB = 0.025         # chance to grow a bit
SHRINK_PROB = 0.012       # chance to shrink (but not too small)

NUM_SNAKES = 12
MIN_LENGTH = 8
MAX_LENGTH = 45

class Snake:
    def __init__(self, width: int, height: int, base_hue: int):
        self.width = width
        self.height = height
        self.base_hue = base_hue
        start_x = random.randint(0, width - 1)
        start_y = random.randint(0, height - 1)
        self.dir: Tuple[int, int] = random.choice(DIRS)
        length = random.randint(MIN_LENGTH, MAX_LENGTH)
        self.body: List[Tuple[int, int]] = []
        dx, dy = -self.dir[0], -self.dir[1]  # grow backwards from head
        x, y = start_x, start_y
        for _ in range(length):
            self.body.append((x % width, y % height))
            x += dx
            y += dy

    def move(self):
        # Random turn
        if random.random() < TURN_PROB:
            # 90° left or right
            turns = [(-self.dir[1], self.dir[0]), (self.dir[1], -self.dir[0])]
            self.dir = random.choice(turns)

        # Move head forward
        hx, hy = self.body[0]
        nx = (hx + self.dir[0]) % self.width
        ny = (hy + self.dir[1]) % self.height
        self.body.insert(0, (nx, ny))

        # Occasionally grow or shrink for liveliness
        if random.random() < GROW_PROB:
            # grow → don't pop tail
            pass
        elif random.random() < SHRINK_PROB and len(self.body) > MIN_LENGTH + 4:
            self.body.pop()
            if random.random() < 0.4:  # sometimes shrink more
                self.body.pop()
        else:
            # normal movement
            self.body.pop()


class RainbowSnakeAnimation(App):
    """Rainbow Snake Party – many colorful snakes wandering randomly"""

    CSS = """
    Screen {
        background: #000004;
    }
    Header {
        background: #0a001a;
        color: #ff88ff;
        dock: top;
    }
    Static#playfield {
        background: #000;
        width: 100%;
        height: 1fr;
        padding: 0;
        margin: 0;
    }
    Footer {
        background: #0a001a;
        color: #88ffff;
        dock: bottom;
    }
    """

    def __init__(self):
        super().__init__()
        self.WIDTH = 110
        self.HEIGHT = 32
        self.snakes: List[Snake] = []
        self.animation_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="playfield")
        yield Footer()

    def on_mount(self) -> None:
        self.playfield = self.query_one(Static)
        self.title = "🌈 Rainbow Snake Party | Q/Esc=Quit | P=Pause"

        # Create snakes with very different base colors
        hues = [0, 20, 40, 60, 120, 180, 240, 270, 300, 330, 15, 55]  # red, orange, yellow, lime, green, cyan, blue, purple, magenta, pink, variations
        for i in range(NUM_SNAKES):
            hue = hues[i % len(hues)]
            self.snakes.append(Snake(self.WIDTH, self.HEIGHT, hue))

        self.speed = 0.07
        self.animation_timer = self.set_interval(self.speed, self.update_snakes)
        self.update_display()

    def update_snakes(self) -> None:
        for snake in self.snakes:
            snake.move()
        self.update_display()

    def update_display(self) -> None:
        lines: List[Text] = []
        for y in range(self.HEIGHT):
            line = Text()
            for x in range(self.WIDTH):
                drawn = False
                for snake in self.snakes:
                    if (x, y) in snake.body:
                        idx = snake.body.index((x, y))
                        ch, style = self._get_char_style(snake, idx)
                        line.append(ch, style)
                        drawn = True
                        break  # first snake that occupies the cell wins (no blending)
                if not drawn:
                    line.append(" ", "#111122")
            lines.append(line)
        self.playfield.update("\n".join(str(line) for line in lines))

    def _get_char_style(self, snake: Snake, idx: int) -> Tuple[str, str]:
        n = len(snake.body)
        if idx == 0:  # head
            ch = HEAD_CHARS[snake.dir]
            return ch, f"bold hsl({snake.base_hue}, 100%, 75%)"

        if idx == n - 1:  # tail
            return "·", f"dim hsl({snake.base_hue}, 60%, 35%)"

        # body segment
        prev = snake.body[idx - 1]
        nxt  = snake.body[idx + 1]
        dir_in  = (snake.body[idx][0] - prev[0], snake.body[idx][1] - prev[1])
        dir_out = (nxt[0] - snake.body[idx][0], nxt[1] - snake.body[idx][1])

        if dir_in == dir_out:
            ch = "─" if dir_in[0] != 0 else "│"
        else:
            # bend
            to_prev = (-dir_in[0], -dir_in[1])
            to_next = dir_out
            ch = self._bend_char(to_prev, to_next)

        # color gradient along body
        hue = (snake.base_hue + idx * 8) % 360
        sat = 90 - (idx / n) * 30
        light = 70 - (idx / n) * 45
        style = f"hsl({hue}, {sat}%, {light}%)"

        return ch, style

    def _bend_char(self, a: Tuple[int,int], b: Tuple[int,int]) -> str:
        s = {a, b}
        if s == {(1,0), (0,1)}:   return "┌"
        if s == {(-1,0),(0,1)}:   return "┐"
        if s == {(1,0), (0,-1)}:  return "└"
        if s == {(-1,0),(0,-1)}:  return "┘"
        return "╬"

    def on_key(self, event: Key) -> None:
        k = event.key.lower()
        if k in ("p", "space"):
            if self.animation_timer and self.animation_timer.is_active:
                self.animation_timer.stop()
                self.title = self.title.replace("Party", "Party [PAUSED]")
            else:
                self.animation_timer = self.set_interval(self.speed, self.update_snakes)
                self.title = self.title.replace(" [PAUSED]", "")
        elif k in ("q", "escape"):
            self.exit()


if __name__ == "__main__":
    app = RainbowSnakeAnimation()
    app.run()