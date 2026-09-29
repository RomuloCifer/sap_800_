"""Contagem regressiva visual (para focar o SAP)."""

from __future__ import annotations

import time

import tkinter as tk

from automation import abort


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

    root.update_idletasks()
    w = root.winfo_width()
    sw = root.winfo_screenwidth()
    root.geometry("+{}+40".format((sw - w) // 2))

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
