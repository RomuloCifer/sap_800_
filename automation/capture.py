"""Captura de texto na tela: arrastar seleção + Ctrl+C."""

from __future__ import annotations

import time

import pyperclip
from pynput.keyboard import Controller as KeyController
from pynput.keyboard import Key

from automation import docmap, win_mouse
from automation.utils import clean_value

_keyboard = KeyController()

MARKER = "__SAP800_BEFORE_COPY__"


def _win32_ctrl_c():
    # type: () -> None
    import ctypes
    from ctypes import wintypes

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_C = 0x43

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        _anonymous_ = ("i",)
        _fields_ = [("type", wintypes.DWORD), ("i", _I)]

    extra = ctypes.c_ulong(0)

    def _key(vk, flags=0):
        ki = KEYBDINPUT(vk, 0, flags, 0, ctypes.pointer(extra))
        inp = INPUT(type=INPUT_KEYBOARD, ki=ki)
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    _key(VK_CONTROL, 0)
    time.sleep(0.03)
    _key(VK_C, 0)
    time.sleep(0.03)
    _key(VK_C, KEYEVENTF_KEYUP)
    time.sleep(0.03)
    _key(VK_CONTROL, KEYEVENTF_KEYUP)


def drag_copy(x1, y1, x2, y2, label="texto", dry_run=False):
    # type: (int, int, int, int, str, bool) -> str
    """Arrasta de (x1,y1) até (x2,y2), Ctrl+C e devolve o texto limpo."""
    if dry_run:
        print("  [dry-run] selecionaria ({},{}) -> ({},{}) ({})".format(x1, y1, x2, y2, label))
        return "DRY_RUN_{}".format(label.upper().replace(" ", "_"))

    print("Capturando {} na tela ({},{}) -> ({},{})...".format(label, x1, y1, x2, y2))
    docmap.maybe_ask_step(
        kind="drag_copy",
        label=label,
        x=x1,
        y=y1,
        x2=x2,
        y2=y2,
    )
    pyperclip.copy(MARKER)
    time.sleep(0.1)

    win_mouse.drag_select(x1, y1, x2, y2)
    time.sleep(0.25)
    _win32_ctrl_c()
    time.sleep(0.3)
    value = clean_value(pyperclip.paste() or "")

    if not value or value == MARKER:
        # Fallback que já funcionava no ISSUER: arrasta de novo + Ctrl+C via pynput
        win_mouse.drag_select(x1, y1, x2, y2)
        time.sleep(0.25)
        with _keyboard.pressed(Key.ctrl):
            _keyboard.press("c")
            _keyboard.release("c")
        time.sleep(0.35)
        value = clean_value(pyperclip.paste() or "")

    if not value or value == MARKER:
        raise RuntimeError(
            "Não foi possível copiar '{}' da tela. "
            "Seleção: ({},{}) -> ({},{}).".format(label, x1, y1, x2, y2)
        )
    print("{} capturado: {!r}".format(label, value))
    return value
