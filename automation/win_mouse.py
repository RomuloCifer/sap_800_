"""
Mouse via Win32 (GetCursorPos / SetCursorPos / SendInput).

Garante o mesmo sistema de coordenadas na captura e no clique,
com DPI awareness por monitor.
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

_DPI_DONE = False

# Constantes SendInput / mouse
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _I)]


def ensure_dpi_awareness():
    # type: () -> None
    global _DPI_DONE
    if _DPI_DONE:
        return
    # 2 = PROCESS_PER_MONITOR_DPI_AWARE
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    _DPI_DONE = True


def position():
    # type: () -> tuple
    ensure_dpi_awareness()
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def move_to(x, y):
    # type: (int, int) -> None
    ensure_dpi_awareness()
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    time.sleep(0.03)


def _virtual_screen_metrics():
    # type: () -> tuple
    # SM_XVIRTUALSCREEN=76, SM_YVIRTUALSCREEN=77, SM_CXVIRTUALSCREEN=78, SM_CYVIRTUALSCREEN=79
    user32 = ctypes.windll.user32
    vx = user32.GetSystemMetrics(76)
    vy = user32.GetSystemMetrics(77)
    vw = user32.GetSystemMetrics(78)
    vh = user32.GetSystemMetrics(79)
    return vx, vy, vw, vh


def _to_absolute(x, y):
    # type: (int, int) -> tuple
    """Converte coordenada de tela (pode ser negativa) para SendInput 0..65535 no virtual desktop."""
    vx, vy, vw, vh = _virtual_screen_metrics()
    if vw <= 0 or vh <= 0:
        return 0, 0
    abs_x = int(round((int(x) - vx) * 65535 / (vw - 1)))
    abs_y = int(round((int(y) - vy) * 65535 / (vh - 1)))
    return abs_x, abs_y


def _send_mouse(flags, x=0, y=0):
    # type: (int, int, int) -> None
    extra = ctypes.c_ulong(0)
    mi = MOUSEINPUT(x, y, 0, flags, 0, ctypes.pointer(extra))
    inp = INPUT(type=INPUT_MOUSE, mi=mi)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def click(x, y, clicks=1, interval=0.08, wiggle_x=0):
    # type: (int, int, int, float, int) -> None
    """
    Move para (x,y) e clica com botão esquerdo (1=simples, 2=duplo).

    wiggle_x > 0: mexe o mouse para a direita/esquerda (mesmo Y) antes do clique,
    útil para “acordar” o foco de listas/dropdowns no SAP.

    Se existir calibration.json, (x,y) são mapeados automaticamente.
    Sem calibração, as coordenadas originais são usadas (máquina de referência).
    """
    ensure_dpi_awareness()
    from automation import calibration

    calibration.announce_if_active()
    x, y = calibration.map_xy(x, y)
    if wiggle_x:
        wiggle_x = calibration.map_dx(wiggle_x)

    move_to(x, y)
    if wiggle_x:
        px = abs(int(wiggle_x))
        move_to(x + px, y)
        time.sleep(0.08)
        move_to(x - px, y)
        time.sleep(0.08)
        move_to(x, y)
        time.sleep(0.1)
    abs_x, abs_y = _to_absolute(x, y)
    flags_move = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    _send_mouse(flags_move, abs_x, abs_y)
    time.sleep(0.02)
    for i in range(clicks):
        _send_mouse(MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, abs_x, abs_y)
        time.sleep(0.02)
        _send_mouse(MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, abs_x, abs_y)
        if i + 1 < clicks:
            time.sleep(interval)

def drag_select(x1, y1, x2, y2, steps=12):
    # type: (int, int, int, int, int) -> None
    """Segura o botao esquerdo de (x1,y1) ate (x2,y2) para selecionar texto."""
    ensure_dpi_awareness()
    from automation import calibration

    calibration.announce_if_active()
    x1, y1 = calibration.map_xy(x1, y1)
    x2, y2 = calibration.map_xy(x2, y2)

    move_to(x1, y1)
    time.sleep(0.08)
    abs1 = _to_absolute(x1, y1)
    _send_mouse(
        MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        abs1[0],
        abs1[1],
    )
    time.sleep(0.05)
    for i in range(1, steps + 1):
        t = float(i) / steps
        x = int(round(x1 + (x2 - x1) * t))
        y = int(round(y1 + (y2 - y1) * t))
        move_to(x, y)
        abs_xy = _to_absolute(x, y)
        _send_mouse(
            MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
            abs_xy[0],
            abs_xy[1],
        )
        time.sleep(0.015)
    move_to(x2, y2)
    time.sleep(0.05)
    abs2 = _to_absolute(x2, y2)
    _send_mouse(
        MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        abs2[0],
        abs2[1],
    )
    time.sleep(0.1)
