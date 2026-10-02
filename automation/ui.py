"""Contagem regressiva visual (para focar o SAP)."""

from __future__ import annotations

import time

import tkinter as tk

from automation import abort


def place_window_left_screen(root, margin_x=24, margin_y=80, anchor="bottom"):
    # type: (tk.Misc, int, int, str) -> None
    """
    Posiciona a janela no monitor da esquerda (área virtual).

    Neste setup o SAP fica à esquerda (coords negativas); o tkinter
    costuma abrir no monitor primário da direita.
    """
    root.update_idletasks()
    w = max(root.winfo_width(), 1)
    h = max(root.winfo_height(), 1)
    try:
        import ctypes

        user32 = ctypes.windll.user32
        vx = int(user32.GetSystemMetrics(76))  # SM_XVIRTUALSCREEN
        vy = int(user32.GetSystemMetrics(77))  # SM_YVIRTUALSCREEN
        vh = int(user32.GetSystemMetrics(79))  # SM_CYVIRTUALSCREEN
    except Exception:
        vx, vy, vh = 0, 0, root.winfo_screenheight()

    x = vx + margin_x
    if anchor == "top":
        y = vy + margin_y
    else:
        y = vy + max(margin_y, vh - h - margin_y)
    root.geometry("+{}+{}".format(int(x), int(y)))


def countdown(seconds, message="Foque a tela do SAP!\nContinuando em..."):
    # type: (int, str) -> None
    root = tk.Tk()
    root.title("Aguarde")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#1a1a2e", padx=24, pady=20)

    tk.Label(
        root,
        text=message,
        font=("Segoe UI", 12),
        fg="#e0e0e0",
        bg="#1a1a2e",
        justify="center",
    ).pack()

    number = tk.Label(
        root,
        text=str(seconds),
        font=("Consolas", 28, "bold"),
        fg="#7CFC00",
        bg="#1a1a2e",
    )
    number.pack(pady=(8, 0))

    hint = tk.Label(
        root,
        text="{} = parar".format(abort.ABORT_KEY_NAME),
        font=("Segoe UI", 9),
        fg="#8888aa",
        bg="#1a1a2e",
    )
    hint.pack(pady=(6, 0))

    place_window_left_screen(root, margin_y=40, anchor="top")

    try:
        for n in range(seconds, 0, -1):
            abort.check()
            number.config(text=str(n))
            root.update()
            # sleep em fatias para reagir ao F10
            remaining = 1.0
            while remaining > 0:
                abort.check()
                chunk = min(0.1, remaining)
                time.sleep(chunk)
                remaining -= chunk
                root.update()
    finally:
        try:
            root.destroy()
        except Exception:
            pass
