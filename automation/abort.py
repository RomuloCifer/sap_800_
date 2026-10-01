"""Abortar a automacao com tecla global (F10)."""

from __future__ import annotations

from typing import Optional

from pynput import keyboard

_abort = False
_listener = None  # type: Optional[keyboard.Listener]

ABORT_KEY = keyboard.Key.f10
ABORT_KEY_NAME = "F10"


class AbortedError(Exception):
    """Levantada quando o usuario aborta com F10."""


def reset():
    # type: () -> None
    global _abort
    _abort = False


def request_abort():
    # type: () -> None
    global _abort
    if not _abort:
        _abort = True
        print("\n*** ABORTADO pelo usuario ({}) ***\n".format(ABORT_KEY_NAME))


def is_aborted():
    # type: () -> bool
    return _abort


def check():
    # type: () -> None
    if _abort:
        raise AbortedError("Automacao abortada com {}.".format(ABORT_KEY_NAME))


def _on_press(key):
    try:
        if key == ABORT_KEY:
            request_abort()
    except Exception:
        pass


def start_listener():
    # type: () -> None
    global _listener
    reset()
    if _listener is not None:
        return
    _listener = keyboard.Listener(on_press=_on_press)
    _listener.daemon = True
    _listener.start()
    print("Tecla de emergencia: {} (para a automacao)".format(ABORT_KEY_NAME))


def stop_listener():
    # type: () -> None
    global _listener
    if _listener is not None:
        try:
            _listener.stop()
        except Exception:
            pass
        _listener = None
