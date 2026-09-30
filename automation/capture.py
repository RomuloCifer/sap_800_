"""Captura de texto na tela: arrastar seleção + Ctrl+C."""

from __future__ import annotations

import time

import pyperclip
from pynput.keyboard import Controller as KeyController
from pynput.keyboard import Key

from automation import docmap, localmap, win_mouse
from automation.utils import clean_value

_keyboard = KeyController()

MARKER = "__SAP800_BEFORE_COPY__"


def _win32_ctrl_key(vk_letter):
    # type: (int) -> None
    """Ctrl + tecla (ex.: VK_A=0x41, VK_C=0x43) via SendInput."""
    import ctypes
    from ctypes import wintypes

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11

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
    _key(vk_letter, 0)
    time.sleep(0.03)
    _key(vk_letter, KEYEVENTF_KEYUP)
    time.sleep(0.03)
    _key(VK_CONTROL, KEYEVENTF_KEYUP)


def _win32_ctrl_c():
    # type: () -> None
    _win32_ctrl_key(0x43)  # C


def _win32_ctrl_a():
    # type: () -> None
    _win32_ctrl_key(0x41)  # A


def _read_clipboard_or_retry(label, redo_fn):
    # type: (str, object) -> str
    value = clean_value(pyperclip.paste() or "")
    if value and value != MARKER:
        return value
    redo_fn()
    time.sleep(0.35)
    value = clean_value(pyperclip.paste() or "")
    if not value or value == MARKER:
        raise RuntimeError("Não foi possível copiar '{}' da tela.".format(label))
    return value


def click_point(x, y, label="clique", dry_run=False, wait_after=0.0, wiggle_x=0):
    # type: (int, int, str, bool, float, int) -> None
    """Clique simples (passa por --documentar / --mapear)."""
    if dry_run:
        print("  [dry-run] clicaria ({},{}) ({})".format(x, y, label))
        return
    print("Clique {} em ({},{})...".format(label, x, y))
    docmap.maybe_ask_step(kind="click", label=label, x=x, y=y)
    x, y = localmap.resolve(x, y, label, kind="click")
    win_mouse.click(x, y, clicks=1, wiggle_x=wiggle_x)
    if wait_after > 0:
        time.sleep(wait_after)


def drag_only(x1, y1, x2, y2, label="arrastar", dry_run=False):
    # type: (int, int, int, int, str, bool) -> None
    """Só arrasta (ex.: barra de rolagem) — sem copiar."""
    if dry_run:
        print("  [dry-run] arrastaria ({},{}) -> ({},{}) ({})".format(x1, y1, x2, y2, label))
        return
    print("Arrastando {} ({},{}) -> ({},{})...".format(label, x1, y1, x2, y2))
    docmap.maybe_ask_step(
        kind="drag_copy",
        label=label,
        x=x1,
        y=y1,
        x2=x2,
        y2=y2,
    )
    x1, y1, x2, y2 = localmap.resolve_drag(x1, y1, x2, y2, label)
    win_mouse.drag_select(x1, y1, x2, y2)
    time.sleep(0.2)


def click_select_all_copy(x, y, label="texto", dry_run=False):
    # type: (int, int, str, bool) -> str
    """
    Clica no campo, Ctrl+A (seleciona tudo) e Ctrl+C.
    Necessário quando o texto é longo e não cabe na tela.
    """
    if dry_run:
        print("  [dry-run] Ctrl+A+C em ({},{}) ({})".format(x, y, label))
        return "DRY_RUN_{}".format(label.upper().replace(" ", "_"))

    print("Capturando {} com Ctrl+A em ({},{})...".format(label, x, y))
    docmap.maybe_ask_step(kind="click", label=label, x=x, y=y)
    x, y = localmap.resolve(x, y, label, kind="click")

    pyperclip.copy(MARKER)
    time.sleep(0.1)
    win_mouse.click(x, y, clicks=1)
    time.sleep(0.25)
    _win32_ctrl_a()
    time.sleep(0.15)
    _win32_ctrl_c()
    time.sleep(0.3)

    def _redo():
        win_mouse.click(x, y, clicks=1)
        time.sleep(0.2)
        with _keyboard.pressed(Key.ctrl):
            _keyboard.press("a")
            _keyboard.release("a")
        time.sleep(0.12)
        with _keyboard.pressed(Key.ctrl):
            _keyboard.press("c")
            _keyboard.release("c")

    value = _read_clipboard_or_retry(label, _redo)
    print("{} capturado: {!r}".format(label, value))
    return value


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
    x1, y1, x2, y2 = localmap.resolve_drag(x1, y1, x2, y2, label)
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
