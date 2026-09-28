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

from automation import win_mouse

DEFAULT_STEP_PAUSE = 0.8
CLICK_TYPE_DELAY = 0.2

_keyboard = KeyController()


@dataclass
class Step:
    kind: str  # click | double_click | click_and_type | type | wait
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    seconds: float = 0.0
    wait_after: Optional[float] = None
    label: str = ""
    keys: List[str] = field(default_factory=list)


def _type_text(text):
    # type: (str) -> None
    pyperclip.copy(text)
    time.sleep(0.05)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press("v")
        _keyboard.release("v")


def run_steps(steps, dry_run=False, step_pause=DEFAULT_STEP_PAUSE, click_type_delay=CLICK_TYPE_DELAY):
    # type: (List[Step], bool, float, float) -> None
    win_mouse.ensure_dpi_awareness()
    total = len(steps)
    for i, step in enumerate(steps, start=1):
        tag = step.label or step.kind
        print("[{}/{}] {}".format(i, total, tag))

        if dry_run:
            print("  -> {}".format(step))
        else:
            if step.kind == "click":
                assert step.x is not None and step.y is not None
                win_mouse.click(step.x, step.y, clicks=1)
            elif step.kind == "double_click":
                assert step.x is not None and step.y is not None
                win_mouse.click(step.x, step.y, clicks=2)
            elif step.kind == "click_and_type":
                assert step.x is not None and step.y is not None
                assert step.text is not None
                win_mouse.click(step.x, step.y, clicks=1)
                time.sleep(click_type_delay)
                _type_text(step.text)
            elif step.kind == "type":
                assert step.text is not None
                _type_text(step.text)
            elif step.kind == "wait":
                time.sleep(step.seconds)
            else:
                raise ValueError("Ação desconhecida: {}".format(step.kind))

        if step.kind == "wait":
            continue

        pause = step_pause
        if step.wait_after is not None:
            pause = step.wait_after
        elif step.seconds and step.kind != "wait":
            pause = step.seconds

        if i < total or step.wait_after is not None or (step.seconds and step.kind != "wait"):
            if not dry_run and pause > 0:
                time.sleep(pause)
            elif dry_run and pause > 0:
                print("  (espera {:.1f}s)".format(pause))
