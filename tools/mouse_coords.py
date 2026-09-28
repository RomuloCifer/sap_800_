"""
Capturador de coordenadas do mouse.

Usa a mesma API Win32 da automação (GetCursorPos + DPI awareness).
Atalhos globais:
  F8  — copia a coordenada atual para a área de transferência
  F9  — anota a coordenada no arquivo coordenadas.txt
  ESC — fecha o programa
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import tkinter as tk
import pyperclip
from pynput import keyboard

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation import win_mouse

win_mouse.ensure_dpi_awareness()

COORD_FILE = Path(__file__).resolve().parent / "coordenadas.txt"
UPDATE_MS = 50


class MouseCoordBar:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Coords")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg="#1a1a2e")
        try:
            self.root.attributes("-toolwindow", True)
        except tk.TclError:
            pass

        screen_w = self.root.winfo_screenwidth()
        bar_w, bar_h = 460, 36
        x = (screen_w - bar_w) // 2
        self.root.geometry("{}x{}+{}+8".format(bar_w, bar_h, x))

        self.label = tk.Label(
            self.root,
            text="X: ----  Y: ----",
            font=("Consolas", 14, "bold"),
            fg="#e0e0e0",
            bg="#1a1a2e",
            padx=12,
        )
        self.label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hint = tk.Label(
            self.root,
            text="F8=copiar  F9=anotar  ESC=sair",
            font=("Segoe UI", 8),
            fg="#8888aa",
            bg="#1a1a2e",
            padx=8,
        )
        self.hint.pack(side=tk.RIGHT)

        self._flash_job = None  # type: Optional[str]
        self._listener = keyboard.Listener(on_press=self._on_key)
        self._listener.daemon = True
        self._listener.start()

        self._tick()

    def _pos(self):
        # type: () -> tuple
        return win_mouse.position()

    def _tick(self) -> None:
        x, y = self._pos()
        self.label.config(text="X: {:4d}   Y: {:4d}".format(x, y))
        self.root.after(UPDATE_MS, self._tick)

    def _flash(self, msg, color="#7CFC00"):
        # type: (str, str) -> None
        self.hint.config(text=msg, fg=color)
        if self._flash_job is not None:
            self.root.after_cancel(self._flash_job)

        def _restore():
            self.hint.config(text="F8=copiar  F9=anotar  ESC=sair", fg="#8888aa")

        self._flash_job = self.root.after(1500, _restore)

    def _on_key(self, key) -> None:
        try:
            if key == keyboard.Key.f8:
                self.root.after(0, self._on_copy)
            elif key == keyboard.Key.f9:
                self.root.after(0, self._on_save)
            elif key == keyboard.Key.esc:
                self.root.after(0, self._on_quit)
        except Exception:
            pass

    def _on_copy(self) -> None:
        x, y = self._pos()
        text = "{}, {}".format(x, y)
        pyperclip.copy(text)
        self._flash("copiado {}".format(text))

    def _on_save(self) -> None:
        x, y = self._pos()
        ts = datetime.now().strftime("%H:%M:%S")
        line = "{}  X={}  Y={}\n".format(ts, x, y)
        with COORD_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
        self._flash("salvo {},{}".format(x, y), "#66ccff")

    def _on_quit(self) -> None:
        try:
            self._listener.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    print("Capturador de coordenadas iniciado (Win32 + DPI).")
    print("  F8  — copia X,Y para a área de transferência")
    print("  F9  — anota no arquivo coordenadas.txt")
    print("  ESC — sai")
    print("Arquivo de anotações: {}".format(COORD_FILE))
    MouseCoordBar().run()


if __name__ == "__main__":
    main()
