import os
import random
import shutil
import sys
import time
from contextlib import contextmanager

try:
    from sound.punch_type_sound import play_music, stop_music, play_sfx
except ImportError:
    def play_music(*args, **kwargs):
        pass

    def stop_music(*args, **kwargs):
        pass

    def play_sfx(*args, **kwargs):
        pass

WIDTH = 78
INNER = WIDTH - 2
MENU_HEIGHT = 26
FPS = 30

FONT = {
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],

    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],

    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "Q": [" ### ", "#   #", "# # #", "#  ##", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}
TITLE = "PUNCH TYPE"

def block_text(text):
    return [" ".join(FONT[ch][row] for ch in text) for row in range(5)]

PORTRAIT_W = 22

FRAME_IDLE = [
    "     .-\"\"\"\"\"-.      ",
    "    /  ,   ,  \\     ",
    "   |  (o) (o)  |    ",
    "    \\    ^    /     ",
    "     \\  ===  /      ",
    "  (@)==\\_____/==(@)  ",
    "      /|  *  |\\      ",
    "     / |     | \\     ",
    "       |_____|       ",
]
FRAME_GUARD = [
    "     .-\"\"\"\"\"-.      ",
    "    /  ,   ,  \\     ",
    " (@)|  (o) (o)  |(@) ",
    "    \\    ^    /     ",
    "     \\  ===  /      ",
    "     /\\_____/\\      ",
    "      /|  *  |\\      ",
    "     / |     | \\     ",
    "       |_____|       ",
]
FRAME_PUNCH = [
    "     .-\"\"\"\"\"-.      ",
    "    /  ,   ,  \\     ",
    "   |  (>) (<)  |    ",
    "    \\    O    /     ",
    "     \\  ===  /      ",
    "  (@)=\\_____/=====(@)",
    "      /|  *  |\\      ",
    "     / |     | \\     ",
    "       |_____|       ",
]

def portrait_art(t=0.0, punching=False):
    if punching or 5.0 <= (t % 6.0) < 5.3:
        frame = FRAME_PUNCH
    else:
        frame = FRAME_IDLE if int(t * 2) % 2 == 0 else FRAME_GUARD
        if (t % 3.2) < 0.15:
            frame = [l.replace("(o) (o)", "(-) (-)") for l in frame]
    return [l.center(PORTRAIT_W)[:PORTRAIT_W] for l in frame]

def portrait_box(title="FIGHTER", art=None):
    art = art or portrait_art()
    top = "+" + f" {title} ".center(PORTRAIT_W, "-") + "+"
    return [top, *["|" + l + "|" for l in art], "+" + "-" * PORTRAIT_W + "+"]

BUTTONS = [("1", "START"), ("2", "SHOP"), ("3", "EXIT")]
BUTTON_W = 19

def button_text(index, kind):
    num, name = BUTTONS[index]
    if kind == 1:
        return "|" + f"{num}  [ {name:^7} ]".center(BUTTON_W) + "|"
    return "+" + "=" * BUTTON_W + "+"

def draw_main_menu(gold=0):
    def row(text=""):
        return "|" + text.ljust(INNER)[:INNER] + "|"

    border = "+" + "=" * INNER + "+"
    stars = "*" * INNER

    lines = [border, row(f"  GOLD: {gold} [o]"), row()]
    lines += [row(l.center(INNER)) for l in block_text(TITLE)]
    lines += [row(), row(stars), row()]

    buttons = []
    for i in range(len(BUTTONS)):
        buttons += [button_text(i, 0), button_text(i, 1), button_text(i, 2)]
        if i < len(BUTTONS) - 1:
            buttons.append("")
    portrait = portrait_box()

    right_margin = 4
    left_w = INNER - PORTRAIT_W - 2 - right_margin
    for b, p in zip(buttons, portrait):
        lines.append(row(b.center(left_w) + p.ljust(PORTRAIT_W + 2) + " " * right_margin))

    lines += [row(), row(stars), row("Type 1, 2 or 3 and press ENTER".center(INNER)), border]
    return "\n".join(lines)

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
HOME = "\x1b[H"
CLEAR = "\x1b[2J"
CLEAR_EOL = "\x1b[K"
CLEAR_DOWN = "\x1b[J"

FIRE = [196, 202, 208, 214, 220, 226, 220, 214, 208, 202]

def c(n):
    return f"\x1b[38;5;{n}m"

def enable_ansi_on_windows():
    if os.name != "nt":
        return
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if k32.GetConsoleMode(handle, ctypes.byref(mode)):
            k32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        os.system("")

def _normalize(ch):
    ch = ch.lower()
    if ch.isdigit():
        return ch
    return {"w": "up", "s": "down", "\r": "enter", "\n": "enter",
            "q": "quit", "\x03": "quit", "\x04": "quit"}.get(ch, "")

if os.name == "nt":
    import msvcrt

    @contextmanager
    def raw_input_mode():
        yield

    def poll_key():
        if not msvcrt.kbhit():
            return ""
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
        if ch == "\x1b":
            return "quit"
        return _normalize(ch)

    def read_key():
        if not msvcrt.kbhit():
            return ""
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
            return ""
        return ch.upper()

    def flush_keys():
        while msvcrt.kbhit():
            msvcrt.getwch()

else:
    import select
    import termios
    import tty

    @contextmanager
    def raw_input_mode():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _ready():
        return bool(select.select([sys.stdin], [], [], 0)[0])

    def poll_key():
        if not _ready():
            return ""
        ch = os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
        if ch == "\x1b":
            seq = ""
            time.sleep(0.01)
            while _ready() and len(seq) < 2:
                seq += os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
            if not seq:
                return "quit"
            return {"[A": "up", "[B": "down"}.get(seq, "")
        return _normalize(ch)

    def read_key():
        if not select.select([sys.stdin], [], [], 0)[0]:
            return ""
        data = os.read(sys.stdin.fileno(), 32).decode(errors="ignore")
        if not data or data[0] == "\x1b":
            return ""
        return data[0].upper()

    def flush_keys():
        try:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass

EDGE = c(208) + "|" + RESET

_last_size = None

def _sync_size():
    global WIDTH, INNER
    size = shutil.get_terminal_size((80, 28))
    WIDTH = max(78, size.columns)
    INNER = WIDTH - 2
    return size

def _too_small(out, min_rows=None):
    global _last_size
    size = shutil.get_terminal_size((80, 28))
    if size != _last_size:
        _last_size = size
        out.write(CLEAR)
    need = min_rows or MENU_HEIGHT + 2
    if size.columns >= 80 and size.lines >= need:
        return False
    out.write(HOME + f"TERMINAL TOO SMALL: NEED 80x{need}, YOU HAVE "
              f"{size.columns}x{size.lines}. ENLARGE THE WINDOW." + CLEAR_EOL)
    out.flush()
    time.sleep(0.2)
    return True

def _plain_len(parts):
    return sum(len(text) for text, _ in parts)

def _fit(parts, width):
    extra = width - _plain_len(parts)
    return parts + [(" " * extra, "")] if extra > 0 else parts

def _paint(parts):
    return "".join(f"{style}{text}{RESET}" if style and text else text for text, style in parts)

def _row(parts):
    return EDGE + _paint(_fit(parts, INNER)) + EDGE

def _render(t, intro, sel, shown_gold, flash, punching):
    def visible(start):
        return (not intro) or t >= start

    size = _sync_size()
    lines = [c(208) + "+" + "=" * INNER + "+" + RESET]

    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines.append(_row([("  GOLD: ", c(220) + BOLD), (str(int(shown_gold)), c(226) + BOLD),
                       (" ", ""), (coin, c(220) + BOLD)]))
    lines.append(_row([]))

    rows = block_text(TITLE)
    tw = len(rows[0])
    reveal = tw if not intro else min(tw, int(t / 0.9 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))

    title_end = len(lines)

    def stars():
        shift = int(t * 10)
        return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                     for i in range(INNER)])

    lines += [_row([]), stars(), _row([])]

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(art=portrait_art(t, punching))

    for k in range(11):
        j, kind = divmod(k, 4)
        if kind == 3 or not visible(1.0 + 0.15 * j):
            left = []
        else:
            text = button_text(j, kind)
            active = j == sel
            style = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(245)
            if active and kind == 1:
                a = box_left - 4 + pulse
                arrow = c(196) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        if visible(1.5):
            p = portrait[k]
            border_style = c(45)
            if k in (0, len(portrait) - 1):
                right = [(p, border_style)]
            else:
                right = [(p[0], border_style), (p[1:-1], c(252)), (p[-1], border_style)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))

    mid_end = len(lines)
    lines += [_row([]), stars()]
    hint = "W/S or UP/DOWN to move   ENTER to select   or press 1 2 3"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:3] + [blank] * gap_top + lines[3:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)

_intro_done = False
_shown_gold = 0.0
_note_shown = False

_reason = ""

def _can_animate():
    global _reason, WIDTH, INNER
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _reason = ("this is not a real terminal (IDLE, Thonny, an IDE 'Run' panel or piped "
                   "input can't redraw the screen). Open Command Prompt / PowerShell / "
                   "Windows Terminal and run:  python punch_type_combined.py")
        return False

    size = shutil.get_terminal_size((80, 28))
    if size.columns < 80 or size.lines < MENU_HEIGHT + 2:
        _reason = (f"your terminal is {size.columns}x{size.lines}; the animated menu needs "
                   f"at least 80x{MENU_HEIGHT + 2}. Maximize the terminal or reduce its font size, then restart.")
        return False

    WIDTH = max(78, size.columns)
    INNER = WIDTH - 2
    return True

def _static_menu(gold):
    global _note_shown
    print(draw_main_menu(gold))
    if not _note_shown:
        _note_shown = True
        print(f"(Animation is off: {_reason})")
    try:
        return int(input("ENTER CHOICE: "))
    except ValueError:
        return 0
    except EOFError:
        return 3

def run_main_menu(gold=0):
    global _intro_done, _shown_gold
    enable_ansi_on_windows()
    if not _can_animate():
        return _static_menu(gold)

    intro = not _intro_done
    shown = float(gold) if _shown_gold > gold else _shown_gold
    rate = max(1.0, (gold - shown) / 0.8)
    sel, typed, result = 0, "", 3
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = last = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                dt, last, t = now - last, now, now - t0
                if _too_small(out):
                    continue
                key = poll_key()

                if key == "up":
                    sel, typed = (sel - 1) % len(BUTTONS), ""
                    play_sfx("move")
                elif key == "down":
                    sel, typed = (sel + 1) % len(BUTTONS), ""
                    play_sfx("move")
                elif key.isdigit():
                    typed = (typed + key)[-3:]
                    if key in "123":
                        sel = int(key) - 1
                        play_sfx("move")
                elif key == "quit":
                    result = 3
                    break
                elif key == "enter":
                    result = 110 if typed.endswith("110") else sel + 1
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render(t + i * 0.05, intro, sel, shown, i % 2 == 0, True))
                        out.flush()
                        time.sleep(0.05)
                    break

                if shown < gold:
                    shown = min(float(gold), shown + rate * dt)
                out.write(_render(t, intro, sel, shown, False, False))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 3
    finally:
        _intro_done = True
        _shown_gold = float(gold)
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result

def _render_exit(t, punching):
    size = _sync_size()
    lines = [c(208) + "+" + "=" * INNER + "+" + RESET, _row([]), _row([])]

    rows = block_text("THANK YOU")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))

    title_end = len(lines)

    def stars():
        shift = int(t * 10)
        return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                     for i in range(INNER)])

    lines += [_row([]), stars(), _row([])]

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(art=portrait_art(t, punching))
    texts = {1: ("FOR PLAYING!", c(15) + BOLD),
             3: ("SEE YOU NEXT TIME,", c(250)),
             4: ("FIGHTER!", c(226) + BOLD)}

    for k in range(11):
        left = []
        if k in texts:
            text, style = texts[k]
            left = [(" " * ((left_w - len(text)) // 2), ""), (text, style)]
        elif 6 <= k <= 8:
            kind = k - 6
            if kind == 1:
                text = "|" + "PRESS ENTER".center(BUTTON_W) + "|"
            else:
                text = "+" + "=" * BUTTON_W + "+"
            style = c(226) + BOLD
            if kind == 1:
                a = box_left - 4 + pulse
                arrow = c(196) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        p = portrait[k]
        edge = c(45)
        if k in (0, len(portrait) - 1):
            right = [(p, edge)]
        else:
            right = [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))

    mid_end = len(lines)
    lines += [_row([]), stars()]
    hint = "THANK YOU FOR PLAYING!   PRESS ENTER TO EXIT"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:3] + [blank] * gap_top + lines[3:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)

VICTORY_BUTTONS = [("1", "RETRY"), ("2", "MENU"), ("3", "EXIT")]

def _victory_button(index, kind):
    num, name = VICTORY_BUTTONS[index]
    if kind == 1:
        return "|" + f"{num}  [ {name:^7} ]".center(BUTTON_W) + "|"
    return "+" + "=" * BUTTON_W + "+"

def _render_victory(t, sel, flash, punching, info):
    size = _sync_size()
    lines = [c(208) + "+" + "=" * INNER + "+" + RESET]

    grow = min(1.0, max(0.0, (t - 0.8) / 1.0))
    shown_gold = info["gold"] - info["earned"] + int(info["earned"] * grow)
    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines.append(_row([("  GOLD: ", c(220) + BOLD), (str(shown_gold), c(226) + BOLD),
                       (" ", ""), (coin, c(220) + BOLD)]))

    rows = block_text("YOU WIN")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))
    title_end = len(lines)

    def stars():
        shift = int(t * 10)
        return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                     for i in range(INNER)])

    note = info["note"]
    if note and t >= 1.0:
        style = c(FIRE[int(t * 8) % len(FIRE)]) + BOLD
        lines.append(_row([(" " * ((INNER - len(note)) // 2), ""), (note, style)]))
    else:
        lines.append(_row([]))
    lines.append(stars())

    count = min(1.0, max(0.0, (t - 1.0) / 0.8))
    stats = [("HITS GIVEN", info["phit"], 46), ("HITS TAKEN", info["ehit"], 196),
             ("CRITICAL HITS", info["crits"], 208), ("GOLD EARNED", info["earned"], 226)]
    cell = INNER // 4
    label_parts = []
    value_parts = []
    for i, (label, value, color) in enumerate(stats):
        width = cell if i < 3 else INNER - 3 * cell
        text = str(int(value * count))
        if label == "GOLD EARNED":
            text = "+" + text + " G"
        label_parts.append((label.center(width), c(250)))
        value_parts.append((text.center(width), c(color) + BOLD))
    lines.append(_row(label_parts))
    lines.append(_row(value_parts))
    lines.append(stars())

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(title="WINNER", art=portrait_art(t, punching))

    for k in range(11):
        j, kind = divmod(k, 4)
        if kind == 3 or t < 1.0 + 0.15 * j:
            left = []
        else:
            text = _victory_button(j, kind)
            active = j == sel
            style = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(245)
            if active and kind == 1:
                a = box_left - 4 + pulse
                arrow = c(196) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        if t >= 1.2:
            p = portrait[k]
            edge = c(45)
            if k in (0, len(portrait) - 1):
                right = [(p, edge)]
            else:
                right = [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))
    mid_end = len(lines)

    lines += [_row([]), stars()]
    hint = "W/S or UP/DOWN to move   ENTER to select   or press 1 2 3"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:2] + [blank] * gap_top + lines[2:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)

def run_victory_screen(gold, earned, phit, ehit, crits, note=""):
    enable_ansi_on_windows()
    if not _can_animate():
        return None
    info = {"gold": gold, "earned": earned, "phit": phit, "ehit": ehit,
            "crits": crits, "note": note}
    sel, result = 0, 3
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out):
                    continue
                key = poll_key()

                if key == "up":
                    sel = (sel - 1) % len(VICTORY_BUTTONS)
                    play_sfx("move")
                elif key == "down":
                    sel = (sel + 1) % len(VICTORY_BUTTONS)
                    play_sfx("move")
                elif key in ("1", "2", "3"):
                    sel = int(key) - 1
                    play_sfx("move")
                elif key == "quit":
                    result = 3
                    break
                elif key == "enter":
                    result = sel + 1
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render_victory(t + i * 0.05, sel, i % 2 == 0, True, info))
                        out.flush()
                        time.sleep(0.05)
                    break

                out.write(_render_victory(t, sel, False, False, info))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 3
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result

DEFEAT_BUTTONS = [("1", "RETRY"), ("2", "MENU")]
DEFEAT_RED = [196, 160, 124, 160]

def _defeat_button(index, kind):
    num, name = DEFEAT_BUTTONS[index]
    if kind == 1:
        return "|" + f"{num}  [ {name:^7} ]".center(BUTTON_W) + "|"
    return "+" + "=" * BUTTON_W + "+"

def _defeat_art(t):

    art = [l.replace("(o) (o)", "(x) (x)").replace("(>) (<)", "(x) (x)") for l in FRAME_IDLE]
    art[3] = art[3].replace("^", "~")
    art[5] = art[5].replace("(@)==", "(@)  ").replace("==(@)", "  (@)")
    if int(t * 2) % 2 == 1:
        art = [" " + l[:-1] for l in art]
    return [l.ljust(PORTRAIT_W)[:PORTRAIT_W] for l in art]

def _render_defeat(t, sel, flash, info):
    size = _sync_size()
    lines = [c(196) + "+" + "=" * INNER + "+" + RESET]

    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines.append(_row([("  GOLD: ", c(220) + BOLD), (str(info["gold"]), c(226) + BOLD),
                       (" ", ""), (coin, c(220) + BOLD)]))

    rows = block_text("YOU LOSE")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = DEFEAT_RED[(i // 2 + r - int(t * 6)) % len(DEFEAT_RED)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))
    title_end = len(lines)

    def dots():
        shift = int(t * 6)
        return _row([("x", c(196) + BOLD) if (i + shift) % 6 == 0 else (".", c(238))
                     for i in range(INNER)])

    msg = "DON'T GIVE UP, FIGHTER!"
    if t >= 1.0:
        lines.append(_row([(" " * ((INNER - len(msg)) // 2), ""), (msg, c(250) + BOLD)]))
    else:
        lines.append(_row([]))
    lines.append(dots())

    count = min(1.0, max(0.0, (t - 1.0) / 0.8))
    stats = [("HITS GIVEN", info["phit"], 46), ("HITS TAKEN", info["ehit"], 196),
             ("CRITICAL HITS", info["crits"], 208), ("GOLD EARNED", info["earned"], 226)]
    cell = INNER // 4
    label_parts = []
    value_parts = []
    for i, (label, value, color) in enumerate(stats):
        width = cell if i < 3 else INNER - 3 * cell
        text = str(int(value * count))
        if label == "GOLD EARNED":
            text = "+" + text + " G"
        label_parts.append((label.center(width), c(250)))
        value_parts.append((text.center(width), c(color) + BOLD))
    lines.append(_row(label_parts))
    lines.append(_row(value_parts))
    lines.append(dots())

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(title="KNOCKED OUT", art=_defeat_art(t))

    for k in range(11):
        j, kind = divmod(k, 4)
        if kind == 3 or j >= len(DEFEAT_BUTTONS) or t < 1.0 + 0.15 * j:
            left = []
        else:
            text = _defeat_button(j, kind)
            active = j == sel
            style = (c(15) + BOLD if flash else c(196) + BOLD) if active else c(245)
            if active and kind == 1:
                a = box_left - 4 + pulse
                arrow = c(226) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        if t >= 1.2:
            p = portrait[k]
            edge = c(196)
            if k in (0, len(portrait) - 1):
                right = [(p, edge)]
            else:
                right = [(p[0], edge), (p[1:-1], c(250)), (p[-1], edge)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))
    mid_end = len(lines)

    lines += [_row([]), dots()]
    hint = "W/S or UP/DOWN to move   ENTER to select   or press 1 2"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(196) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:2] + [blank] * gap_top + lines[2:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)

def run_defeat_screen(gold, earned, phit, ehit, crits):
    enable_ansi_on_windows()
    if not _can_animate():
        return None
    info = {"gold": gold, "earned": earned, "phit": phit, "ehit": ehit, "crits": crits}
    sel, result = 0, 2
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out):
                    continue
                key = poll_key()

                if key == "up":
                    sel = (sel - 1) % len(DEFEAT_BUTTONS)
                    play_sfx("move")
                elif key == "down":
                    sel = (sel + 1) % len(DEFEAT_BUTTONS)
                    play_sfx("move")
                elif key in ("1", "2"):
                    sel = int(key) - 1
                    play_sfx("move")
                elif key == "quit":
                    result = 2
                    break
                elif key == "enter":
                    result = sel + 1
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render_defeat(t + i * 0.05, sel, i % 2 == 0, info))
                        out.flush()
                        time.sleep(0.05)
                    break

                out.write(_render_defeat(t, sel, False, info))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 2
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result

def _static_exit():
    print("+" + "-" * 44 + "+")
    print("|" + "THANK YOU FOR PLAYING!".center(44) + "|")
    print("|" + "SEE YOU NEXT TIME, FIGHTER!".center(44) + "|")
    print("+" + "-" * 44 + "+")
    try:
        input("Press ENTER to exit...")
    except (EOFError, KeyboardInterrupt):
        pass

def run_exit_screen():
    enable_ansi_on_windows()
    if not _can_animate():
        _static_exit()
        return
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out):
                    continue
                key = poll_key()
                if key in ("enter", "quit"):
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render_exit(t + i * 0.05, True))
                        out.flush()
                        time.sleep(0.05)
                    break
                out.write(_render_exit(t, False))
                out.flush()
                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        pass
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()

SHOP_HEIGHT = 28

MAPS = [
    ("STREET", 208,
     ["|##| /||\\ |##|", "|##|/ || \\|##|"]),
    ("UNDERGROUND", 245,
     ["==|========|==", "  \\\\  ||  //  "]),
    ("BOXING RING", 196,
     ["+==+==+==+==+", "|  _[__]_   |"]),
]

ITEMS = [
    ("none", "NO GLOVES", 0,
     ["  .--.      .--.  ", " ( () )    ( () ) ", "  '--'      '--'  "], 250),
    ("spiked", "SPIKED GLOVES", 2500,
     [" ^ ^ ^      ^ ^ ^ ", " (@@@@@)    (@@@@@)", "  '---'      '---' "], 252),
    ("bomb", "BOMB GLOVES", 5000,
     ["  .--.   *   .--. ", " (@@@@) (o) (@@@@)", "  '--'       '--' "], 214),
    ("lava", "LAVA GLOVES", 10000,
     ["  ~^~^~     ~^~^~ ", " (@@@@@)   (@@@@@)", "  ~'~'~     ~'~'~ "], 202),
]

DESCRIPTIONS = {
    "none": "NO GLOVES: BASE DAMAGE | TWIN PUNCH ULT: 3 HITS = DOUBLE DAMAGE",
    "spiked": "SPIKED: 20% CRIT RATE | BERSERK ULT: 3 HITS = +250% BASE DAMAGE",
    "bomb": "BOMB: +200% BASE DAMAGE | BLOODLUST BANG ULT: 3 HITS = +500% DAMAGE",
    "lava": "LAVA: +150% DAMAGE, +30% CRIT | MULTXXXXX ULT: 5 HITS = STACKING +30%",
}

LOCK_MSG = [
    "",
    "MAP NOT UNLOCKED YET, DEFEAT THE HARD DIFFICULTY OF THE 1ST MAP",
    "MAP NOT UNLOCKED YET, DEFEAT THE HARD DIFFICULTY OF THE 2ND MAP",
]

_shop_reason = ""

def _header(t, shown, title):
    _sync_size()
    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines = [
        c(208) + "+" + "=" * INNER + "+" + RESET,
        _row([("  GOLD: ", c(220) + BOLD), (str(int(round(shown))), c(226) + BOLD),
              (" ", ""), (coin, c(220) + BOLD)]),
        _row([]),
    ]
    rows = block_text(title)
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                parts.append(("#", c(FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))
    lines.append(_row([]))
    return lines

def _stars(t):
    shift = int(t * 10)
    return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                 for i in range(INNER)])

def _footer(t, msg, msg_style, hint):
    return [
        _stars(t),
        _row([(msg.center(INNER), msg_style)] if msg else []),
        _row([(hint.center(INNER), c(245))]),
        c(208) + "+" + "=" * INNER + "+" + RESET,
    ]

def _portrait_rows(t, punching):
    return portrait_box(art=portrait_art(t, punching))

def _portrait_parts(box, k):
    p = box[k]
    edge = c(45)
    if k in (0, len(box) - 1):
        return [(p, edge)]
    return [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]

def _shop_frame(lines):
    size = _sync_size()
    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        top = extra // 4
        middle = extra // 4
        lines = (lines[:2] + [blank] * top + lines[2:9] + [blank] * middle + lines[9:-4]
                 + [blank] * (extra - top - middle) + lines[-4:])
    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)

MAP_W = 44

def _map_cell(j, kind, st, t):
    name, color, scene = MAPS[j]
    locked = not st["unlocked"][j]
    active = j == st["sel"]
    flash = t < st.get("flash_until", 0)
    bs = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(240)
    ls = c(15) + BOLD if active else c(250)
    if locked:
        color = 240
        ls = c(196) + BOLD if active else c(240)
    if kind in (0, 3):
        return [("+" + "=" * (MAP_W - 2) + "+", bs)]
    art = scene[kind - 1].center(16)[:16]
    label = (("LOCKED" if locked else "MAP") if kind == 1 else name).center(25)[:25]
    return [("|", bs), (art, c(color)), ("|", bs), (label, ls), ("|", bs)]

def _render_maps(st, t):
    lines = _header(t, st["shown"], "CHOOSE MAP")
    box = _portrait_rows(t, t < st.get("flash_until", 0))
    pulse = int(t * 3) % 2
    for k in range(15):
        j, kind = divmod(k, 5)
        if kind == 4 or j >= len(MAPS):
            left = [(" " * (3 + MAP_W), "")]
            gap = [("   ", "")]
        else:
            active = j == st["sel"]
            arrow = c(196) + BOLD
            show = active and kind in (1, 2)
            lead = [((">> " if pulse else " >>"), arrow)] if show else [("   ", "")]
            left = lead + _map_cell(j, kind, st, t)
            gap = [(("<< " if pulse else " <<"), arrow)] if show else [("   ", "")]
        pk = k - 1
        right = _portrait_parts(box, pk) if 0 <= pk < len(box) else [(" " * 24, "")]
        lines.append(_row([(" " * max(0, (INNER - 74) // 2), "")] + left + gap + right))
    hint = "W/S or UP/DOWN to move   ENTER to select   ESC to go back"
    if t < st.get("msg_until", 0):
        lines += _footer(t, st["msg"], c(196) + BOLD, hint)
    else:
        lines += _footer(t, "", "", hint)
    return _shop_frame(lines)

def _handle_maps(st, key, t):
    if "done_at" in st:
        return
    if key == "up":
        st["sel"] = (st["sel"] - 1) % len(MAPS)
        play_sfx("move")
    elif key == "down":
        st["sel"] = (st["sel"] + 1) % len(MAPS)
        play_sfx("move")
    elif key.isdigit() and key in "123":
        st["sel"] = int(key) - 1
        play_sfx("move")
    elif key == "quit":
        st["result"] = 0
        st["done_at"] = t
        play_sfx("back")
    elif key == "enter":
        if not st["unlocked"][st["sel"]]:
            st["msg"] = LOCK_MSG[st["sel"]]
            st["msg_until"] = t + 2.5
            play_sfx("denied")
        else:
            st["result"] = st["sel"] + 1
            play_sfx("select")
            st["flash_until"] = t + 0.4
            st["done_at"] = t + 0.4

CARD_W = 22

def _card_cell(k, local, st, t):
    gid, label, price, art, base = ITEMS[k]
    active = k == st["sel"]
    flash = t < st.get("flash_until", 0)
    bs = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(240)
    if local in (0, 6):
        return [("+" + "-" * (CARD_W - 2) + "+", bs)]
    if 1 <= local <= 3:
        color = c(FIRE[(int(t * 8) + local + k) % len(FIRE)]) if gid == "lava" else c(base)
        return [("|", bs), (art[local - 1].center(CARD_W - 2)[:CARD_W - 2], color), ("|", bs)]
    if local == 4:
        style = c(15) + BOLD if active else c(250)
        return [("|", bs), (f"[ {label} ]".center(CARD_W - 2)[:CARD_W - 2], style), ("|", bs)]
    if st["equipped"] == gid:
        txt, style = "EQUIPPED", c(46) + BOLD
    elif gid in st["owned"]:
        txt, style = "OWNED", c(51)
    elif st["mode"] == "pick":
        txt, style = "LOCKED", c(196)
    else:
        txt = f"{price} G"
        style = c(226) + BOLD if st["gold"] >= price else c(196)
    return [("|", bs), (txt.center(CARD_W - 2), style), ("|", bs)]

def _render_shop(st, t):
    lines = _header(t, st["shown"], "SHOP" if st["mode"] == "shop" else "EQUIPMENTS")
    box = _portrait_rows(t, t < st.get("flash_until", 0))
    for kr in range(15):
        if kr == 7:
            card_row = None
        else:
            card_row, local = (0, kr) if kr < 7 else (1, kr - 8)
        if card_row is None:
            left = [(" " * (3 + CARD_W * 2 + 2), "")]
        else:
            a, b = card_row * 2, card_row * 2 + 1
            left = ([("   ", "")] + _card_cell(a, local, st, t) + [("  ", "")]
                    + _card_cell(b, local, st, t))
        pk = kr - 1
        right = _portrait_parts(box, pk) if 0 <= pk < len(box) else [(" " * 24, "")]
        lines.append(_row([(" " * max(0, (INNER - 76) // 2), "")] + left + [("   ", "")] + right))
    if t < st.get("msg_until", 0):
        msg, msg_style = st["msg"], st.get("msg_style", "")
    else:
        msg, msg_style = DESCRIPTIONS.get(ITEMS[st["sel"]][0], ""), c(250)
    hint = ("W/S or UP/DOWN to move   1-4 jump   ENTER equip   ESC back" if st["mode"] == "pick"
            else "W/S or UP/DOWN to move   1-4 jump   ENTER buy   ESC back")
    lines += _footer(t, msg, msg_style, hint)
    return _shop_frame(lines)

def _try_buy(st, t):
    gid, label, price, _, _ = ITEMS[st["sel"]]
    if st["mode"] == "pick":
        if gid in st["owned"]:
            st["equipped"] = gid
            st["flash_until"] = t + 0.4
            st["done_at"] = t + 0.4
            st["msg"], st["msg_style"] = f"{label} EQUIPPED", c(46) + BOLD
            play_sfx("select")
        else:
            st["msg"], st["msg_style"] = "YOU DONT HAVE THAT YET", c(196) + BOLD
            play_sfx("denied")
    elif gid in st["owned"]:
        st["equipped"] = gid
        play_sfx("select")
        st["msg"], st["msg_style"] = f"{label} EQUIPPED", c(46) + BOLD
    elif st["gold"] >= price:
        st["gold"] -= price
        st["owned"].add(gid)
        play_sfx("buy")
        st["equipped"] = gid
        st["flash_until"] = t + 0.4
        st["msg"], st["msg_style"] = f"PURCHASED {label}!  -{price} GOLD", c(226) + BOLD
    else:
        st["msg"], st["msg_style"] = "NOT ENOUGH GOLD!", c(196) + BOLD
        play_sfx("denied")
    st["msg_until"] = t + 2.0

def _handle_shop(st, key, t):
    if "done_at" in st:
        return
    if key == "up":
        st["sel"] = (st["sel"] - 1) % len(ITEMS)
        play_sfx("move")
    elif key == "down":
        st["sel"] = (st["sel"] + 1) % len(ITEMS)
        play_sfx("move")
    elif key.isdigit() and key in "1234":
        st["sel"] = int(key) - 1
        play_sfx("move")
    elif key == "quit":
        if st["mode"] == "pick":
            st["equipped"] = None
        st["done_at"] = t
        play_sfx("back")
    elif key == "enter":
        _try_buy(st, t)

def _shop_can_animate():
    global _shop_reason
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _shop_reason = ("this is not a real terminal. Open Command Prompt / PowerShell / "
                   "Windows Terminal and run:  python punch_type_combined.py")
        return False
    size = shutil.get_terminal_size((80, 30))
    if size.columns < 80 or size.lines < SHOP_HEIGHT + 2:
        _shop_reason = (f"your terminal is {size.columns}x{size.lines}; this screen needs at least "
                   f"80x{SHOP_HEIGHT + 2}. Maximize the terminal or reduce its font size, then restart.")
        return False

    _sync_size()
    return True

def _animate(st, render, handle):
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = last = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                dt, last, t = now - last, now, now - t0
                if _too_small(out, SHOP_HEIGHT + 2):
                    continue
                handle(st, poll_key(), t)
                if "done_at" in st and t >= st["done_at"]:
                    break
                if st["shown"] != st["gold"]:
                    step = max(60.0, abs(st["shown"] - st["gold"]) / 0.5) * dt
                    if st["shown"] > st["gold"]:
                        st["shown"] = max(float(st["gold"]), st["shown"] - step)
                    else:
                        st["shown"] = min(float(st["gold"]), st["shown"] + step)
                out.write(render(st, t))
                out.flush()
                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        st.setdefault("result", 0)
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()

def _static_maps(gold, unlocked):
    print("=== CHOOSE MAP ===    GOLD:", gold)
    for i, (name, _, _) in enumerate(MAPS, 1):
        print(f"  {i}. MAP {name}" + ("" if unlocked[i - 1] else "   [LOCKED]"))
    print(f"(Animation is off: {_shop_reason})")
    while True:
        try:
            n = int(input("ENTER CHOICE (0 = back): "))
        except (ValueError, EOFError):
            return 0
        if not 1 <= n <= len(MAPS):
            return 0
        if unlocked[n - 1]:
            return n
        print(LOCK_MSG[n - 1])

def _static_shop(gold, owned, equipped, mode="shop"):
    print(f"(Animation is off: {_shop_reason})")
    while True:
        print(f"\n=== CHOOSE EQUIPMENTS ===    GOLD: {gold}")
        for i, (gid, label, price, _, _) in enumerate(ITEMS, 1):
            tag = ("EQUIPPED" if gid == equipped else "OWNED" if gid in owned
                   else "LOCKED" if mode == "pick" else f"{price} G")
            print(f"  {i}. {label:<14} {tag}")
        try:
            n = int(input("BUY / EQUIP (0 = back): "))
        except (ValueError, EOFError):
            return equipped, gold, owned
        if n == 0:
            return (None if mode == "pick" else equipped), gold, owned
        if 1 <= n <= len(ITEMS):
            gid, label, price, _, _ = ITEMS[n - 1]
            if mode == "pick":
                if gid in owned:
                    return gid, gold, owned
                print("YOU DONT HAVE THAT YET")
            elif gid in owned:
                equipped = gid
            elif gold >= price:
                gold -= price
                owned.add(gid)
                equipped = gid
                print(f"Purchased {label}!")
            else:
                print("NOT ENOUGH GOLD!")

def run_map_select(gold=0, unlocked=(1, 1, 1)):
    enable_ansi_on_windows()
    unlocked = [bool(u) for u in unlocked] + [True] * len(MAPS)
    unlocked = unlocked[:len(MAPS)]
    if not _shop_can_animate():
        return _static_maps(gold, unlocked)
    st = {"sel": 0, "gold": gold, "shown": float(gold), "result": 0, "unlocked": unlocked}
    _animate(st, _render_maps, _handle_maps)
    return st["result"]

def run_shop(gold=0, owned=None, equipped="none", mode="shop"):
    enable_ansi_on_windows()
    owned = set(owned or ()) | {"none"}
    if not _shop_can_animate():
        return _static_shop(gold, owned, equipped, mode)
    sel = next((i for i, it in enumerate(ITEMS) if it[0] == equipped), 0)
    st = {"sel": sel, "gold": gold, "shown": float(gold), "owned": owned,
          "equipped": equipped, "msg": "", "mode": mode}
    _animate(st, _render_shop, _handle_shop)
    return st["equipped"], st["gold"], st["owned"]

DIFF_HEIGHT = 26

DIFFICULTIES = [
    {"name": "EASY", "stars": "*", "color": 46, "hp": 500, "dmg": 10, "time": "3s", "win": 500,
     "keys": "QWERTY"},
    {"name": "MEDIUM", "stars": "**", "color": 220, "hp": 1000, "dmg": 25, "time": "2s", "win": 800,
     "keys": "QWERTYASDFGH"},
    {"name": "HARD", "stars": "***", "color": 196, "hp": 1500, "dmg": 50, "time": "1.5s", "win": 1000,
     "keys": "QWERTYASDFGHZXCVB"},
]
DIFF_BTN_W = 31
BACK_BTN_W = 15

_diff_reason = ""

def _diff_button(label, stars, inner, kind):
    if kind != 1:
        return "+" + "-" * inner + "+"
    if stars:
        text = (" " + stars.ljust(3)).ljust(4) + label.center(inner - 8) + " " * 4
    else:
        text = label.center(inner)
    return "|" + text + "|"

def _button_parts(text, style, active, kind, box_left, pulse, arrow_color):
    if active and kind == 1:
        a = box_left - 4 + pulse
        arrow = arrow_color + BOLD
        return [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
    return [(" " * box_left, ""), (text, style)]

def _diff_frame(lines):
    size = _sync_size()
    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        top = extra // 4
        middle = extra // 4
        lines = (lines[:2] + [blank] * top + lines[2:8] + [blank] * middle + lines[8:-3]
                 + [blank] * (extra - top - middle) + lines[-3:])
    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)

def _render_difficulty(t, sel, flash, punching):
    _sync_size()
    inner = INNER
    lines = [c(208) + "+" + "=" * inner + "+" + RESET]

    label = "S E L E C T"
    lines.append(_row([(" " * ((inner - len(label)) // 2), ""), (label, c(250) + BOLD)]))

    rows = block_text("DIFFICULTY")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.5 * tw))
    pad = (inner - tw) // 2
    sweep = int(t * 30) % (tw + 30) - 10
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                hot = 0 <= (i - sweep + r) < 5
                parts.append(("#", (c(196) if hot else c(255)) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))

    uline = []
    for i in range(tw):
        hot = 0 <= (i - sweep) < 8
        uline.append(("=" if i < reveal else " ", c(196) + BOLD if hot else c(250)))
    lines.append(_row([(" " * pad, "")] + uline))

    left_w = min(inner - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (inner - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, inner - lead - left_w - PORTRAIT_W - 2)
    pulse = int(t * 3) % 2
    art = portrait_art(t, punching)
    if sel == 2:
        art = [l.replace("(o) (o)", "(>) (<)").replace("(-) (-)", "(>) (<)") for l in art]
    portrait = portrait_box(art=art)

    for k in range(15):
        j, kind = divmod(k, 4)
        left = []
        if k <= 10 and kind != 3 and t >= 0.5 + 0.12 * j:
            d = DIFFICULTIES[j]
            box_left = (left_w - (DIFF_BTN_W + 2)) // 2
            text = _diff_button(d["name"], d["stars"], DIFF_BTN_W, kind)
            active = j == sel
            if active:
                if kind != 1:
                    text = "+" + "=" * DIFF_BTN_W + "+"
                style = (c(15) if flash else c(d["color"])) + BOLD
            else:
                style = c(240)
            left = _button_parts(text, style, active, kind, box_left, pulse, c(d["color"]))
        elif k >= 12 and t >= 0.5 + 0.12 * 3:
            kind = k - 12
            box_left = (left_w - (BACK_BTN_W + 2)) // 2
            text = _diff_button("<- BACK", "", BACK_BTN_W, kind)
            active = sel == 3
            if active:
                if kind != 1:
                    text = "+" + "=" * BACK_BTN_W + "+"
                style = (c(15) if flash else c(250)) + BOLD
            else:
                style = c(240)
            left = _button_parts(text, style, active, kind, box_left, pulse, c(250))
        left = _fit(left, left_w)

        if k <= 10 and t >= 0.8:
            p = portrait[k]
            edge = c(45)
            if k in (0, len(portrait) - 1):
                right = [(p, edge)]
            else:
                right = [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))

    if sel < 3:
        d = DIFFICULTIES[sel]
        info = f"HP {d['hp']} | DMG {d['dmg']} | REACT {d['time']} | WIN +{d['win']} G | KEYS {d['keys']}"
        info_style = c(d["color"]) + BOLD
    else:
        info = "Return to the main menu"
        info_style = c(250)
    lines.append(_row([(" " * ((inner - len(info)) // 2), ""), (info, info_style)]))

    hint = "W/S or UP/DOWN to move   ENTER to select   1 2 3 pick   4 or ESC back"
    lines.append(_row([(" " * ((inner - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * inner + "+" + RESET)
    return _diff_frame(lines)

def _diff_can_animate():
    global _diff_reason, WIDTH, INNER
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _diff_reason = ("this is not a real terminal. Open Command Prompt / PowerShell / "
                   "Windows Terminal and run:  python punch_type_combined.py")
        return False
    size = shutil.get_terminal_size((80, 30))
    if size.columns < 80 or size.lines < DIFF_HEIGHT + 2:
        _diff_reason = (f"your terminal is {size.columns}x{size.lines}; this screen needs at least "
                   f"80x{DIFF_HEIGHT + 2}. Maximize the terminal or reduce its font size, then restart.")
        return False
    WIDTH = max(78, size.columns)
    INNER = WIDTH - 2
    return True

def _static_difficulty():
    print(f"(Animation is off: {_diff_reason})")
    print("CONTROLS FOR EASY MODE IS QWERTY. FOR MEDIUM AND HARD, MORE LETTERS ARE ADDED.")
    print("=====================")
    print("Select Difficulty")
    print("1.EASY")
    print("2.MEDIUM")
    print("3.HARD")
    print("4.BACK")
    print("=====================")
    try:
        return int(input())
    except ValueError:
        return 0
    except EOFError:
        return 4

def run_difficulty_menu():
    enable_ansi_on_windows()
    if not _diff_can_animate():
        return _static_difficulty()

    sel, result = 0, 4
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out, DIFF_HEIGHT + 2):
                    continue
                key = poll_key()

                if key == "up":
                    sel = (sel - 1) % 4
                    play_sfx("move")
                elif key == "down":
                    sel = (sel + 1) % 4
                    play_sfx("move")
                elif key in ("1", "2", "3", "4"):
                    sel = int(key) - 1
                    play_sfx("move")
                elif key == "quit":
                    result = 4
                    play_sfx("back")
                    break
                elif key == "enter":
                    result = sel + 1
                    play_sfx("back" if sel == 3 else "select")
                    for i in range(8):
                        out.write(_render_difficulty(t + i * 0.05, sel, i % 2 == 0, sel < 3))
                        out.flush()
                        time.sleep(0.05)
                    break

                out.write(_render_difficulty(t, sel, False, False))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 4
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result

W = 78
H = 27
MIN_COLS = W + 2
MIN_ROWS = H + 2

REASON = ""

ENEMY_NAMES = {1: "STREET THUG", 2: "IRON MIKE", 3: "THE CHAMPION"}
DIFF_NAMES = {1: "EASY", 2: "MEDIUM", 3: "HARD"}
HIT_WORDS = ["CLEAN HIT!", "PERFECT PUNCH!", "NICE!", "WELL TIMED!"]
ESAY = ["AYAAAAAN NAAAA", "NGAWNGAW", "ARAYKUPOOOOO", "MAMAAAAAAA"]
SAY = ["WOOOOOOW!!!!", "UNSTOPPABLE!!!", "UY BAGSAK!!"]

class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.ch = [[" "] * w for _ in range(h)]
        self.st = [[""] * w for _ in range(h)]

    def put(self, x, y, text, style=""):
        if not 0 <= y < self.h:
            return
        for i, ch in enumerate(text):
            if 0 <= x + i < self.w:
                self.ch[y][x + i] = ch
                self.st[y][x + i] = style

    def put_solid(self, x, y, text, style):
        left = len(text) - len(text.lstrip())
        right = len(text.rstrip())
        for i in range(left, right):
            ch = text[i]
            s = style(ch) if callable(style) else style
            self.put(x + i, y, ch, s)

    def lines(self):
        out = []
        for y in range(self.h):
            row = []
            start = 0
            for x in range(1, self.w + 1):
                if x == self.w or self.st[y][x] != self.st[y][start]:
                    text = "".join(self.ch[y][start:x])
                    style = self.st[y][start]
                    row.append(style + text + RESET if style else text)
                    start = x
            out.append("".join(row))
        return out

LEVELS = [(6, 3), (4, 2), (3, 2), (2, 1), (1, 1)]
SX = 1
SY = 1
FLOOR = 15

def scale_art(rows, sx, sy):
    out = []
    for row in rows:
        out += ["".join(ch * sx for ch in row)] * sy
    return out

def set_layout(cols, rows):
    global W, H, SX, SY, FLOOR
    W = cols - 1
    H = rows - 1
    SX, SY = 1, 1
    for sx, sy in LEVELS:
        if ENEMY_W * sx + 16 <= W and 17 * sy <= H - 10:
            SX, SY = sx, sy
            break
    FLOOR = H - 6 - 6 * SY

def _sprite(w, h, parts):
    grid = [[" "] * w for _ in range(h)]
    for x, y, text in parts:
        for i, ch in enumerate(text):
            grid[y][x + i] = ch
    return ["".join(row) for row in grid]

ENEMY_W = 32
ENEMY_H = 11

ENEMY_IDLE = _sprite(ENEMY_W, ENEMY_H, [
    (11, 0, ".---------."),
    (9, 1, "/   ,     ,   \\"),
    (1, 2, ".---."), (8, 2, "|   (O)   (O)   |"), (26, 2, ".---."),
    (0, 3, "(@@@@@)"), (8, 3, "|       >       |"), (25, 3, "(@@@@@)"),
    (0, 4, "(@@@@@)"), (10, 4, "\\    ===    /"), (25, 4, "(@@@@@)"),
    (1, 5, "'---'"), (12, 5, "'-.___.-'"), (26, 5, "'---'"),
    (9, 6, "/|     #     |\\"),
    (8, 7, "/ |     #     | \\"),
    (7, 8, "/  |     #     |  \\"),
    (9, 9, "|_______#_______|"),
    (10, 10, "/ |   | |   | \\"),
])

def _swap_eyes(rows, left, right):
    return [r.replace("(O)", left, 1).replace("(O)", right, 1) for r in rows]

ENEMY_WINDUP = _swap_eyes(ENEMY_IDLE, "(>)", "(<)")
ENEMY_HURT = _swap_eyes(ENEMY_IDLE, "(X)", "(X)")

FIST_BIG = [
    r"   .-~~~~~~-.   ",
    r"  / @@@@@@@@ \  ",
    r" | @@@@@@@@@@ | ",
    r" | @@@@@@@@@@ | ",
    r"  \ @@@@@@@@ /  ",
    r"   '-.____.-'   ",
]

GLOVE_W = 14
GLOVE = [
    r"   .------.   ",
    r"  /  ,--,  \  ",
    r" |  ( () )  | ",
    r" |   '--'   | ",
    r"  \  ====  /  ",
    r"   '------'   ",
]
GLOVE_TOP = {
    2: r"  ^ ^ ^ ^ ^   ",
    3: r"   .--**--.   ",
    4: r"  ~^~^~^~^~   ",
}
GLOVE_COLOR = {1: 196, 2: 252, 3: 214}

ULT_NAMES = {1: "TWIN PUNCH", 2: "BERSERK", 3: "BLOODLUST BANG", 4: "LAVA MULTXXXX"}
ULT_SFX = {1: "ult", 2: "ult_berserk", 3: "ult_bloodlust", 4: "ult_lava"}

def enemy_style(ch):
    return c(196) + BOLD if ch == "@" else c(180)

crowd_cache = {}

def crowd_rows(width):
    if width not in crowd_cache:
        rng = random.Random(7)
        crowd_cache[width] = ["".join(rng.choice("oO.o.") for _ in range(width)) for _ in range(3)]
    return crowd_cache[width]

def _bricks(cv, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        offset = 0 if y % 2 == 0 else 2
        cv.put(x0, y, ("|###" * 20)[offset:offset + (x1 - x0 + 1)], c(238))

def _bg_street(cv, gt):
    bw = 10 + (W - 78) // 4
    _bricks(cv, 1, bw, 3, FLOOR - 1)
    _bricks(cv, W - 1 - bw, W - 2, 3, FLOOR - 1)
    sign_y = 3 + (FLOOR - 3) // 3
    cv.put(2, sign_y, "PUNCH", c(124) + BOLD)
    cv.put(2, sign_y + 1, "TYPE!", c(124) + BOLD)
    lamp_x = bw + 5
    lamp = c(226) + BOLD if int(gt * 7) % 23 else c(94)
    cv.put(lamp_x, 4, ".(*).", lamp)
    for y in range(5, FLOOR):
        cv.put(lamp_x + 2, y, "|", c(240))
    trash_x = W - bw - 15
    cv.put(trash_x, FLOOR - 3, ".-----------.", c(240))
    cv.put(trash_x, FLOOR - 2, "|   TRASH   |", c(240))
    cv.put(trash_x, FLOOR - 1, "'-----------'", c(240))

def _bg_underground(cv, gt):
    cv.put(1, 3, "=" * (W - 2), c(240))
    cv.put(1, 4, "=" * (W - 2), c(238))
    for x in (W * 12 // 78, W - 15):
        for y in range(5, FLOOR):
            cv.put(x, y, "[]", c(240))
    for x in (W * 22 // 78, W - 24):
        cv.put(x, 5, "|", c(240))
        cv.put(x - 1, 6, "(o)", c(226) + BOLD)
    cv.put(W * 32 // 78, 5 + int(gt * 8) % (FLOOR - 6), "'", c(39))

def _bg_ring(cv):
    for i, row in enumerate(crowd_rows(W - 2)):
        cv.put(1, 3 + i, row, c(238 + i))
    for x in (3, W - 6):
        for y in range(6, FLOOR):
            cv.put(x, y, "[#]", c(240))
    for y, color in ((FLOOR - 7, 196), (FLOOR - 5, 255), (FLOOR - 3, 33)):
        cv.put(1, y, "=" * (W - 2), c(color))

def draw_background(cv, map_id, gt):
    cv.put(1, FLOOR, "_" * (W - 2), c(240))
    for y in range(FLOOR + 1, H - 5):
        for x in range(1 + (y % 2) * 2, W - 1, 4):
            cv.put(x, y, ".", c(238))
    if map_id == 2:
        _bg_underground(cv, gt)
    elif map_id == 3:
        _bg_ring(cv)
    else:
        _bg_street(cv, gt)

def hp_bar(cv, x, y, shown, maximum, width=30):
    frac = max(0.0, min(1.0, shown / maximum)) if maximum else 0.0
    fill = int(frac * width + 0.5)
    if shown > 0 and fill == 0:
        fill = 1
    color = 46 if frac > 0.5 else (226 if frac > 0.25 else 196)
    cv.put(x, y, "[", c(250))
    cv.put(x + 1, y, "#" * fill, c(color) + BOLD)
    cv.put(x + 1 + fill, y, "-" * (width - fill), c(240))
    cv.put(x + width + 1, y, "]", c(250))

def number(v):
    return str(int(round(v)))

def hp_text(v, m):
    return f"{max(0, int(v + 0.999))}/{int(m)}"

def current_pose(s, gt):
    phase = s["phase"]
    if phase == "prompt":
        left = s["window"] - (gt - s["t0"])
        return "windup" if left <= s["window"] * 0.35 else "idle"
    if phase == "anim":
        p = (gt - s["t0"]) / s["dur"]
        if s["kind"] == "enemy":
            return "punch"
        return "hurt" if p >= 0.3 else "idle"
    if phase == "end" and s["won"]:
        return "hurt"
    return "idle"

def draw_enemy(cv, s, gt):
    pose = current_pose(s, gt)
    rows = ENEMY_IDLE
    dx = [-1, 0, 1, 0][int(gt * 3) % 4]
    dy = 0
    if pose == "windup":
        rows = ENEMY_WINDUP
        dx = (int(gt * 25) % 3) - 1
    elif pose == "punch":
        rows = ENEMY_WINDUP
        dx, dy = 0, 1
    elif pose == "hurt":
        rows = ENEMY_HURT
        dx = 0 if s["phase"] == "end" else (2 if int(gt * 24) % 2 else -2)
    x0 = (W - ENEMY_W * SX) // 2 + dx * SX
    y0 = FLOOR - ENEMY_H * SY + dy * SY
    for i, row in enumerate(scale_art(rows, SX, SY)):
        cv.put_solid(x0, y0 + i, row, enemy_style)
    if pose == "windup":
        cv.put(x0 + 14 * SX, y0 - 1, "! ! !", c(196) + BOLD)
    elif pose == "hurt":
        cv.put(x0 + 3 * SX, y0 + SY, "*", c(226) + BOLD)
        cv.put(x0 + 28 * SX, y0 + 2 * SY, "*", c(226) + BOLD)
        cv.put(x0 + 14 * SX, y0 - 1, "x x", c(226) + BOLD)
    elif pose == "punch":
        p = (gt - s["t0"]) / s["dur"]
        if p > 0.15:
            fist = scale_art(FIST_BIG, SX, SY)
            fx = (W - len(fist[0])) // 2
            fy = FLOOR - ENEMY_H * SY + 6 * SY
            for i, row in enumerate(fist):
                cv.put_solid(fx, fy + i, row, enemy_style)

def draw_gloves(cv, s, gt, st):
    if st["glove"] == 4:
        style = c(FIRE[int(gt * 8) % len(FIRE)]) + BOLD
    else:
        style = c(GLOVE_COLOR.get(st["glove"], 196)) + BOLD
    art = list(GLOVE)
    if st["glove"] in GLOVE_TOP:
        art[0] = GLOVE_TOP[st["glove"]]
    art = scale_art(art, SX, SY)
    gw = GLOVE_W * SX
    cx = W // 2
    top = FLOOR - ENEMY_H * SY

    pos = {"L": (3, FLOOR + int(gt * 2) % 2), "R": (W - 3 - gw, FLOOR + (int(gt * 2) + 1) % 2)}
    punching = None
    if s["phase"] == "anim" and s["kind"] == "player":
        p = (gt - s["t0"]) / s["dur"]
        if p < 0.4:
            t = p / 0.4
        elif p < 0.6:
            t = 1.0
        else:
            t = max(0.0, 1.0 - (p - 0.6) / 0.4)
        side = s["side"]
        rx, ry = pos[side]
        tx, ty = (cx - gw - 1, top + 2 * SY) if side == "L" else (cx + 1, top + 2 * SY)
        pos[side] = (int(rx + (tx - rx) * t), int(ry + (ty - ry) * t))
        punching = side
        if 0.3 <= p <= 0.75:
            word = "CRIT!" if s["crit"] else "POW!"
            cv.put(cx - 4, top - 1, f"* {word} *", c(226) + BOLD)
            cv.put(cx - 9, top + SY, "\\ | /", c(226))
            cv.put(cx + 7, top + 3 * SY, "* !", c(226))
    elif s["phase"] == "anim" and s["kind"] == "enemy":
        p = (gt - s["t0"]) / s["dur"]
        if 0.2 <= p <= 0.7:
            pos["L"] = (pos["L"][0] - 2 * SX, pos["L"][1])
            pos["R"] = (pos["R"][0] + 2 * SX, pos["R"][1])

    for side in ("L", "R"):
        if side == punching:
            continue
        for i, row in enumerate(art):
            cv.put_solid(pos[side][0], pos[side][1] + i, row, style)
    if punching:
        x, y = pos[punching]
        for i, row in enumerate(art):
            cv.put_solid(x, y + i, row, style)

def centered(cv, y, text, style):
    cv.put((W - len(text)) // 2, y, text, style)

def draw_prompt(cv, s, gt):
    y0 = FLOOR + 2 * SY
    if s["phase"] == "prompt":
        left = max(0.0, s["window"] - (gt - s["t0"]))
        frac = left / s["window"]
        color = 46 if frac > 0.5 else (226 if frac > 0.25 else 196)
        centered(cv, y0, "P R E S S", c(245))
        centered(cv, y0 + 1, f"[ {s['letter']} ]   {left:.1f} sec", c(color) + BOLD)
        width = max(24, min(24 * SX, W - 2 * GLOVE_W * SX - 12))
        fill = int(frac * width + 0.5)
        centered(cv, y0 + 2, "[" + "#" * fill + "-" * (width - fill) + "]", c(color))
    elif gt < s["msg_until"]:
        centered(cv, y0, s["msg"], s["msg_style"])
        if s["msg2"]:
            centered(cv, y0 + 2, s["msg2"], c(250))

def draw_end_box(cv, s, gt):
    won = s["won"]
    color = c(46) + BOLD if won else c(196) + BOLD
    lines = ["+------------------------+",
             "|        K . O .         |",
             "|" + ("YOU WIN!" if won else "YOU LOSE!").center(24) + "|",
             "|" + ("PRESS ENTER" if gt - s["t0"] > 1.0 else "").center(24) + "|",
             "+------------------------+"]
    top = FLOOR - ENEMY_H * SY + 3 * SY
    for i, line in enumerate(lines):
        cv.put((W - len(line)) // 2, top + i, line, color)

def draw_frame(cv, border):
    cv.put(0, 0, "+" + "=" * (W - 2) + "+", border)
    cv.put(0, H - 1, "+" + "=" * (W - 2) + "+", border)
    for y in (2, H - 5):
        cv.put(0, y, "+" + "-" * (W - 2) + "+", c(240))
        cv.put(0, y, "+", border)
        cv.put(W - 1, y, "+", border)
    for y in range(1, H - 1):
        cv.put(0, y, "|", border)
        cv.put(W - 1, y, "|", border)

def render(s, st, gt, size):
    cols, rows = size
    set_layout(cols, rows)
    cv = Canvas(W, H)
    draw_background(cv, st["map"], gt)
    draw_enemy(cv, s, gt)
    draw_gloves(cv, s, gt, st)
    draw_prompt(cv, s, gt)
    if s["phase"] == "end":
        draw_end_box(cv, s, gt)

    bar_w = max(30, W - 48)
    cv.put(2, 1, "ENEMY: " + ENEMY_NAMES.get(st["difficulty"], "ENEMY"), c(15) + BOLD)
    hp_bar(cv, 30, 1, s["shown_e"], st["enemy_max"], bar_w)
    cv.put(33 + bar_w, 1, hp_text(s["shown_e"], st["enemy_max"]), c(250))

    cv.put(2, H - 4, "PLAYER: GEARLESS JOE", c(15) + BOLD)
    hp_bar(cv, 30, H - 4, s["shown_p"], st["player_max"], bar_w)
    cv.put(33 + bar_w, H - 4, hp_text(s["shown_p"], st["player_max"]), c(250))

    status = (f"HITS GAVE: {st['phit']}  HITS TAKEN: {st['ehit']}  WRONG: {s['wrong']}  "
              f"SLOW: {s['slow']}  CRITS: {st['crits']}  LAST: {s['last']}")
    centered(cv, H - 3, status, c(250))
    centered(cv, H - 2, "Press the letter shown before the timer runs out! Wrong key = you get hit.",
             c(240))

    flash = gt < s["flash_until"]
    draw_frame(cv, c(196) + BOLD if flash else c(208))

    diff = DIFF_NAMES.get(st["difficulty"], "")
    cv.put(3, 2, f" {diff}  KEYS: {st['keys']} ", c(245))
    need = st["ult_need"]
    ready = st["ult"] >= need
    meter = "#" * min(st["ult"], need) + "-" * max(0, need - st["ult"])
    cv.put(W - 22, H - 5, f" ULT [{meter}] " + ("READY!" if ready else ""),
           (c(226) + BOLD) if ready else c(245))

    return HOME + (CLEAR_EOL + "\n").join(cv.lines()) + CLEAR_EOL + CLEAR_DOWN

def new_scene(st):
    return {
        "phase": "intro", "t0": 0.0, "until": 0.0, "dur": 0.4, "kind": "", "side": "R",
        "letter": "", "last_letter": "", "window": 2.0, "landed": 0,
        "msg": "GET READY!", "msg_style": c(250) + BOLD, "msg2": "", "msg_until": 99.0,
        "flash_until": 0.0, "wrong": 0, "slow": 0, "last": "-", "crit": False, "won": False,
        "shown_e": float(st["enemy"]), "shown_p": float(st["player"]),
    }

def set_msg(s, gt, text, style, msg2="", seconds=1.2):
    s["msg"] = text
    s["msg_style"] = style
    s["msg2"] = msg2
    s["msg_until"] = gt + seconds

def reaction_window(st, landed):
    base = st["react"]
    return max(base * 0.7, base * (1 - 0.02 * landed))

def start_gap(s, gt):
    s["phase"] = "gap"
    s["until"] = gt + random.uniform(0.5, 0.9)

def start_prompt(s, st, gt):
    pool = [ch for ch in st["keys"] if ch != s["last_letter"]] or list(st["keys"])
    s["letter"] = random.choice(pool)
    s["last_letter"] = s["letter"]
    s["window"] = reaction_window(st, s["landed"])
    s["phase"] = "prompt"
    s["t0"] = gt
    s["msg_until"] = 0.0
    flush_keys()

def do_hit(hooks, s, gt):
    res = hooks["player_hit"]()
    dmg = number(res["damage"])
    s["landed"] += 1
    s["last"] = "-" + dmg
    s["crit"] = res["crit"]
    s["side"] = "L" if s["side"] == "R" else "R"
    s["phase"], s["kind"], s["t0"], s["dur"] = "anim", "player", gt, 0.4

    if res["ult"]:
        play_sfx(ULT_SFX.get(hooks["state"]()["glove"], "ult"))
    elif res["crit"]:
        play_sfx("crit")
    else:
        play_sfx("punch")

    if res["ult"]:
        extra = "+5 HP!" if res["heal"] else random.choice(SAY)
        set_msg(s, gt, f"ULT: {res['ult']}!  -{dmg}", c(201) + BOLD, extra)
    elif res["crit"]:
        set_msg(s, gt, f"CRITICAL HIT!  -{dmg}", c(226) + BOLD)
    else:
        set_msg(s, gt, f"{random.choice(HIT_WORDS)}  -{dmg}", c(46) + BOLD)

def do_miss(hooks, s, gt, reason):
    res = hooks["enemy_hit"]()
    dmg = number(res["damage"])
    if reason == "wrong":
        s["wrong"] += 1
        text = "MISSED!  YOU GOT HIT!"
    else:
        s["slow"] += 1
        text = "TOO SLOW!  YOU GOT HIT!"
    s["last"] = "+" + dmg + " taken"
    s["phase"], s["kind"], s["t0"], s["dur"] = "anim", "enemy", gt, 0.45
    play_sfx("hurt")
    s["flash_until"] = gt + 0.35
    set_msg(s, gt, f"{text}  -{dmg}", c(196) + BOLD, random.choice(ESAY) if res["enraged"] else "")

def update(hooks, s, gt, key):
    st = hooks["state"]()
    phase = s["phase"]
    if phase == "intro":
        if gt > 0.7:
            if not s.get("bell"):
                s["bell"] = True
                play_sfx("bell")
            set_msg(s, gt, "FIGHT!", c(226) + BOLD, "", 1.0)
        if gt > 1.2:
            start_gap(s, gt)
    elif phase == "gap":
        if gt >= s["until"]:
            start_prompt(s, st, gt)
    elif phase == "prompt":
        left = s["window"] - (gt - s["t0"])
        if 0 < left <= s["window"] * 0.35 and not s.get("ticked"):
            s["ticked"] = True
            play_sfx("tick")
        if left <= 0:
            do_miss(hooks, s, gt, "slow")
        elif len(key) == 1 and key.isalpha():
            if key == s["letter"]:
                do_hit(hooks, s, gt)
            else:
                do_miss(hooks, s, gt, "wrong")
    elif phase == "anim":
        if gt - s["t0"] >= s["dur"]:
            st = hooks["state"]()
            if st["enemy"] <= 0 or st["player"] <= 0:
                s["phase"] = "end"
                s["won"] = st["enemy"] <= 0
                s["t0"] = gt
                play_sfx("ko_win" if s["won"] else "ko_lose")
                flush_keys()
            else:
                if not s.get("roared") and st["enemy"] <= st["enemy_max"] * 0.25:
                    s["roared"] = True
                    play_sfx("roar")
                start_gap(s, gt)
    elif phase == "end":
        if gt - s["t0"] > 1.0 and key in ("\r", "\n"):
            s["phase"] = "done"

def ease_bars(s, st, dt):
    k = min(1.0, dt * 12)
    for name, real in (("shown_e", st["enemy"]), ("shown_p", st["player"])):
        s[name] += (real - s[name]) * k
        if abs(real - s[name]) < 0.5:
            s[name] = float(real)

def too_small(size):
    return size[0] < MIN_COLS or size[1] < MIN_ROWS

def fight_loop(hooks, s, out):
    last = time.monotonic()
    gt = 0.0
    size = None
    while True:
        now = time.monotonic()
        dt = min(now - last, 0.1)
        last = now

        new_size = tuple(shutil.get_terminal_size((MIN_COLS, MIN_ROWS)))
        if new_size != size:
            size = new_size
            out.write(CLEAR)
        if too_small(size):
            out.write(HOME + f"TERMINAL TOO SMALL - NEED {MIN_COLS}x{MIN_ROWS}, "
                      f"YOU HAVE {size[0]}x{size[1]}. FIGHT IS PAUSED." + CLEAR_EOL)
            out.flush()
            flush_keys()
            time.sleep(0.2)
            continue

        gt += dt
        key = read_key()
        if key == "\x03":
            raise KeyboardInterrupt
        update(hooks, s, gt, key)
        if s["phase"] == "done":
            return
        st = hooks["state"]()
        ease_bars(s, st, dt)
        out.write(render(s, st, gt, size))
        out.flush()

        spare = 1.0 / FPS - (time.monotonic() - now)
        if spare > 0:
            time.sleep(spare)

def can_animate():
    global REASON
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        REASON = ("this is not a real terminal. Open Command Prompt / PowerShell / "
                  "Windows Terminal and run:  python punch_type_combined.py")
        return False
    size = shutil.get_terminal_size((MIN_COLS, MIN_ROWS))
    if too_small(size):
        REASON = (f"your terminal is {size.columns}x{size.lines}; the fight needs at least "
                  f"{MIN_COLS}x{MIN_ROWS}. Maximize the window or reduce the font size.")
        return False
    return True

def run_combat(hooks):
    if not can_animate():
        return False
    enable_ansi_on_windows()
    s = new_scene(hooks["state"]())
    out = sys.stdout
    interrupted = False
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    try:
        with raw_input_mode():
            flush_keys()
            fight_loop(hooks, s, out)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
        flush_keys()
    if interrupted:
        raise SystemExit
    return True

ult = 0
gold = 0
pdamage = 20
pdmg = 30

player = 100
ehit = 0
phit = 0
x = 1
has_spiked = 0
has_bomb = 0
has_lava = 0
crits = 0
map2 = 0
map3 = 0
choice4 = 0

def retry():
    global gold
    global gg
    global x
    global player
    global enemy
    global pdmg
    global map2
    global map3

    if enemy <= 0:
        if choice2 == 1:
            gol = 500
            gold += 500

        elif choice2 == 2:
            gol = 800
            gold += 800
        elif choice2 == 3:
            gol = 1000
            gold += 1000

        note = ""
        if choice2 == 3:
            if choice4 == 1:
                map2 = 1
                note = "CONGRATULATIONS, YOU'VE UNLOCKED UNDERGROUND MAP"
            elif choice4 == 2:
                map3 = 1
                note = "CONGRATULATIONS, YOU'VE UNLOCKED BOXING RING MAP"
            elif choice4 == 3:
                note = "CONGRATULATIONS, YOU ARE THE CHAMPION!!!"

        lamon = victory_screen(gol, note)
        match lamon:
            case 1:
                gg = 1
                player = 100
                enemy = hp
                pdmg = 30

            case 2:
                x = 1
                gg = 0
                return

            case 3:
                exit_screen()
                sys.exit()

    if player <= 0:
        if choice2 == 1:
            gol=150
            gold += 150
        elif choice2 == 2:
            gol = 300
            gold += 300
        elif choice2 == 3:
            gol = 450
            gold += 450
        gold += 50

        ulit = defeat_screen(gol)
        match ulit:
            case 1:
                gg = 1
                player = 100
                enemy = hp
                pdmg = 30
            case 2:
                x = 1
                gg = 0
                return

def owned_set():
    owned = {"none"}
    if has_spiked == 1:
        owned.add("spiked")
    if has_bomb == 1:
        owned.add("bomb")
    if has_lava == 1:
        owned.add("lava")
    return owned

def shop():
    global gold
    global has_spiked
    global has_bomb
    global has_lava
    _, gold, owned = run_shop(gold, owned_set(), "none", mode="shop")
    has_spiked = 1 if "spiked" in owned else 0
    has_bomb = 1 if "bomb" in owned else 0
    has_lava = 1 if "lava" in owned else 0

GLOVE_NUMBER = {"none": 1, "spiked": 2, "bomb": 3, "lava": 4}
DIFFICULTY_STATS = {1: (500, 10), 2: (1000, 25), 3: (1500, 50)}

def prepare_fight():
    global gg
    global x
    global choice4
    global choice6
    while True:
        picked_map = run_map_select(gold, (1, map2, map3))
        if picked_map == 0:
            return False
        choice4 = picked_map
        picked, _, _ = run_shop(gold, owned_set(), "none", mode="pick")
        if picked is not None:
            choice6 = GLOVE_NUMBER[picked]
            gg = 1
            x = 0
            return True

def gamemenu():
    global x
    global enemy
    global hp
    global dmg
    global edmg
    global choice2
    global gg

    gg = 0
    if choice1 != 1:
        return
    while True:
        choice2 = run_difficulty_menu()
        if choice2 not in (1, 2, 3):
            return
        hp, dmg = DIFFICULTY_STATS[choice2]
        enemy = hp
        edmg = dmg
        if prepare_fight():
            return

def fight_classic():
    global ult
    global ehit
    global phit

    ult = 0
    ehit = 0
    phit = 0
    d = DIFFICULTIES[choice2 - 1]
    window = float(d["time"].rstrip("s"))
    while player > 0 and enemy > 0 and gg == 1:
        letter = random.choice(d["keys"])
        print("ENEMY:", enemy, "| PLAYER:", player)
        print(d["name"])
        print(letter)
        start = time.time()
        answer = input().strip().upper()
        if time.time() - start <= window and answer == letter:
            res = combat_player_hit()
            if res["ult"]:
                print("ULT ACTIVATED -", res["ult"])
            print("CRITICAL!!!" if res["crit"] else "NICE!", "-", number(res["damage"]))
        else:
            res = combat_enemy_hit()
            print("MISSED -", number(res["damage"]))
        print()

ULT_NEED = {1: 3, 2: 3, 3: 3, 4: 5}

def combat_state():
    d = DIFFICULTIES[choice2 - 1]
    return {"player": player, "player_max": 100, "enemy": enemy, "enemy_max": hp,
            "ult": ult, "ult_need": ULT_NEED[choice6], "phit": phit, "ehit": ehit,
            "crits": crits, "difficulty": choice2, "map": choice4, "glove": choice6,
            "keys": d["keys"], "react": float(d["time"].rstrip("s"))}

def combat_player_hit():
    global ult
    global enemy
    global player
    global phit
    global pdamage
    global pdmg
    global crits

    crit = random.randint(1, 100)
    crit_hit = False
    ult_name = ""
    heal = 0

    if choice6 == 1:
        pdamage = 20
        if ult >= 3:
            ult_name = ULT_NAMES[1]
            pdamage *= 2
    elif choice6 == 2:
        pdamage = 20
        if crit <= 25:
            pdamage *= 3
            crit_hit = True
        if ult >= 3:
            ult_name = ULT_NAMES[2]
            pdamage *= 2.5
            ult = 2
    elif choice6 == 3:
        pdamage = 20 * 2
        if ult >= 3:
            ult_name = ULT_NAMES[3]
            pdamage *= 5
            ult = 0
            player += 5
            heal = 5
    elif choice6 == 4:
        pdamage = 20 * 1.5
        if crit <= 30:
            pdamage = pdmg * 3
            crit_hit = True
        if ult >= 5:
            ult_name = ULT_NAMES[4]
            pdmg += 30 * .30
            ult = 4

    ult += 1
    if choice6 == 4 and ult >= 5 and not crit_hit:
        damage = pdmg
    else:
        damage = pdamage
    if crit_hit:
        crits += 1
    enemy -= damage
    phit += 1
    return {"damage": damage, "crit": crit_hit, "ult": ult_name, "heal": heal}

def combat_enemy_hit():
    global player
    global ehit
    global ult
    global pdmg

    dmg = edmg
    enraged = enemy <= hp * 0.25
    if enraged:
        dmg = edmg * 2
    player -= dmg
    ehit += 1
    ult = 0
    pdmg = 30
    return {"damage": dmg, "enraged": enraged}

COMBAT_HOOKS = {"state": combat_state, "player_hit": combat_player_hit,
                "enemy_hit": combat_enemy_hit}

def fight():
    global ult
    global ehit
    global phit

    ult = 0
    ehit = 0
    phit = 0
    if not run_combat(COMBAT_HOOKS):
        print("(First-person view is off: " + REASON + ")")
        fight_classic()

def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")

def show_centered(lines, extra=0):
    size = shutil.get_terminal_size((80, 24))
    width = max(len(line) for line in lines)
    left = max(0, (size.columns - width) // 2)
    top = max(0, (size.lines - len(lines) - extra) // 2)
    clear_screen()
    print("\n" * top, end="")
    for line in lines:
        print((" " * left + line)[:size.columns - 1])
    return left

def box_row(text, width):
    return "|" + text[:width].center(width) + "|"

def stat_row(label, value, width):
    indent = max(0, (width - 26) // 2)
    text = " " * indent + label.ljust(16) + str(value).rjust(10)
    return "|" + text.ljust(width)[:width] + "|"

def victory_screen(earned, note):
    animated = run_victory_screen(gold, earned, phit, ehit, crits, note)
    if animated is not None:
        return animated
    trophy = [
        "   .-=======-.   ",
        "  ( |  K.O.  | )  ",
        "   '-.     .-'   ",
        "      |   |      ",
        "     _|___|_     ",
        "    |_______|    ",
    ]
    message = ""
    while True:
        size = shutil.get_terminal_size((80, 24))
        width = max(30, min(52, size.columns - 2))
        border = "+" + "-" * width + "+"
        lines = [border, box_row("Y O U   W I N !", width)]
        if size.lines >= 26:
            lines += [box_row(row.ljust(19), width) for row in trophy]
        lines += [box_row(note, width), border]
        lines += [stat_row("HITS GIVEN", phit, width),
                  stat_row("HITS TAKEN", ehit, width),
                  stat_row("CRITICAL HITS", crits, width),
                  stat_row("GOLD EARNED", "+" + str(earned) + " G", width),
                  border]
        lines += [box_row("1. RETRY", width), box_row("2. MENU", width),
                  box_row("3. EXIT", width), border]
        lines += [box_row(message, width), border]
        left = show_centered(lines, 2)
        try:
            answer = input(" " * left + "ENTER CHOICE: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 3
        if answer in ("1", "2", "3"):
            return int(answer)
        message = "INVALID CHOICE. TYPE 1, 2 OR 3."

def defeat_screen(earned):
    animated = run_defeat_screen(gold, earned, phit, ehit, crits)
    if animated is not None:
        return animated
    print("YOU LOSE!")
    print("1.RETRY  HITS TAKEN: ", ehit)
    print("2. MENU   HITS GAVE: ", phit)
    print("YOU'VE EARNED ", earned, " GOLD       CRITS: ", crits)
    while True:
        try:
            answer = input("ENTER CHOICE: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 2
        if answer in ("1", "2"):
            return int(answer)

def exit_screen():
    run_exit_screen()

if __name__ == "__main__":
    while x == 1:
        play_music()
        choice1 = run_main_menu(gold)
        if choice1 == 2:
            shop()
        if choice1 == 1:

            gamemenu()
            while gg == 1:
                stop_music()
                print("FIGHT!")
                fight()
                retry()

        if choice1 == 3:
            stop_music()
            exit_screen()
            break
        if choice1 == 110:
            play_sfx("cheat")
            print("YOU'VE UNLOCKED ALL GLOVES AND MAPS!")
            has_spiked = 1
            has_bomb = 1
            has_lava = 1
            map2 = 1
            map3 = 1
