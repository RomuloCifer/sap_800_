"""
Executor de sequências de automação (cliques / digitação / esperas).

Mouse via Win32 (mesmo sistema de coordenadas do capturador).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

import pyperclip
from pynput.keyboard import Controller as KeyController
from pynput.keyboard import Key

from automation import abort, docmap, localmap, win_mouse

DEFAULT_STEP_PAUSE = 1.5  # entre um passo e o próximo
CLICK_TYPE_DELAY = 0.35  # entre clique e digitar

_keyboard = KeyController()

_KEY_MAP = {
    "delete": Key.delete,
    "backspace": Key.backspace,
    "enter": Key.enter,
    "tab": Key.tab,
    "esc": Key.esc,
}


@dataclass
class Step:
    kind: str  # click | double_click | click_and_type | type | wait | press
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    seconds: float = 0.0
    wait_after: Optional[float] = None
    label: str = ""
    keys: List[str] = field(default_factory=list)
    delete_times: int = 0
    wiggle_x: int = 0
    tab_after: bool = False  # apertar Tab depois de digitar
    press_times: int = 1  # quantas vezes apertar a tecla (kind=press)
    press_interval: float = 0.25  # intervalo entre repetições da tecla
    # Digitar caractere a caractere (dispara autocomplete do SAP)
    type_slowly: bool = False
    char_interval: float = 0.2


def _type_text(text):
    # type: (str) -> None
    pyperclip.copy(text)
    time.sleep(0.05)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press("v")
        _keyboard.release("v")


def _type_chars(text, interval=0.2):
    # type: (str, float) -> None
    """Digita letra a letra (necessário para listas/autocomplete do SAP)."""
    for ch in text:
        abort.check()
        _keyboard.type(ch)
        _sleep(interval)


def _press_key(name, times=1, interval=0.05):
    # type: (str, int, float) -> None
    key = _KEY_MAP.get(name.lower(), name)
    for i in range(times):
        abort.check()
        _keyboard.press(key)
        _keyboard.release(key)
        if i + 1 < times:
            _sleep(interval)


def _sleep(seconds):
    # type: (float) -> None
    """Sleep em fatias para reagir rápido ao F10."""
    remaining = float(seconds)
    while remaining > 0:
        abort.check()
        chunk = min(0.1, remaining)
        time.sleep(chunk)
        remaining -= chunk


def run_steps(steps, dry_run=False, step_pause=DEFAULT_STEP_PAUSE, click_type_delay=CLICK_TYPE_DELAY):
    # type: (List[Step], bool, float, float) -> None
    win_mouse.ensure_dpi_awareness()
    total = len(steps)
    for i, step in enumerate(steps, start=1):
        abort.check()
        tag = step.label or step.kind
        print("[{}/{}] {}".format(i, total, tag))

        if dry_run:
            print("  -> {}".format(step))
            if step.tab_after:
                print("  (depois: TAB)")
        else:
            # --documentar: nome/obs só em passos com mouse (wait/press/type seguem)
            if step.kind in docmap.MOUSE_KINDS:
                docmap.maybe_ask_step(
                    kind=step.kind,
                    label=tag,
                    x=step.x,
                    y=step.y,
                    extra={
                        "text": step.text,
                        "keys": list(step.keys) if step.keys else None,
                    },
                )
            # --mapear / pontos_local: resolve XY desta máquina
            x, y = step.x, step.y
            if step.x is not None and step.y is not None:
                x, y = localmap.resolve(step.x, step.y, tag, kind=step.kind)

            if step.kind == "click":
                assert x is not None and y is not None
                win_mouse.click(x, y, clicks=1, wiggle_x=step.wiggle_x)
            elif step.kind == "double_click":
                assert x is not None and y is not None
                win_mouse.click(x, y, clicks=2, wiggle_x=step.wiggle_x)
            elif step.kind == "click_and_type":
                assert x is not None and y is not None
                assert step.text is not None
                win_mouse.click(x, y, clicks=1, wiggle_x=step.wiggle_x)
                _sleep(click_type_delay)
                if step.delete_times:
                    _press_key("delete", step.delete_times, interval=0.05)
                    _sleep(0.1)
                if step.type_slowly:
                    _type_chars(step.text, interval=step.char_interval)
                else:
                    _type_text(step.text)
                if step.tab_after:
                    _sleep(0.35)
                    _press_key("tab", 1)
                    _sleep(0.25)
            elif step.kind == "type":
                assert step.text is not None
                if step.type_slowly:
                    _type_chars(step.text, interval=step.char_interval)
                else:
                    _type_text(step.text)
                if step.tab_after:
                    _sleep(0.35)
                    _press_key("tab", 1)
                    _sleep(0.25)
            elif step.kind == "press":
                assert step.keys
                times = step.press_times if step.press_times > 0 else 1
                if step.seconds and step.seconds >= 1 and step.press_times <= 1:
                    times = int(step.seconds)
                _press_key(step.keys[0], times=times, interval=step.press_interval)
            elif step.kind == "click_and_press":
                assert x is not None and y is not None
                assert step.keys
                win_mouse.click(x, y, clicks=1, wiggle_x=step.wiggle_x)
                _sleep(click_type_delay)
                times = step.press_times if step.press_times > 0 else 1
                _press_key(step.keys[0], times=times, interval=step.press_interval)
            elif step.kind == "wait":
                _sleep(step.seconds)
            else:
                raise ValueError("Ação desconhecida: {}".format(step.kind))

        if step.kind == "wait":
            continue

        pause = step_pause
        if step.wait_after is not None:
            pause = step.wait_after
        elif step.seconds and step.kind not in ("wait", "press"):
            pause = step.seconds

        if i < total or step.wait_after is not None or (
            step.seconds and step.kind not in ("wait", "press")
        ):
            if not dry_run and pause > 0:
                _sleep(pause)
            elif dry_run and pause > 0:
                print("  (espera {:.1f}s)".format(pause))
