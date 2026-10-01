"""Abortar a automacao com tecla global (F10)."""

from __future__ import annotations

import time
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


def sleep(seconds):
    # type: (float) -> None
    """Sleep em fatias, reagindo ao F10."""
    remaining = float(seconds)
    while remaining > 0:
        check()
        chunk = min(0.1, remaining)
        time.sleep(chunk)
        remaining -= chunk


def _on_press(key):
    try:
        if key == ABORT_KEY:
            request_abort()
    except Exception:
        pass


def start_listener(fresh=False):
    # type: (bool) -> None
    """
    Garante o listener global do F10.

    fresh=True: zera o flag de abort (início de um fluxo novo).
    Se o listener já estiver ativo e fresh=False, NÃO zera o flag
    (evita “apagar” um F10 já pressionado ao entrar numa parte).
    """
    global _listener
    if _listener is not None:
        if fresh:
            reset()
        return
    reset()
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
