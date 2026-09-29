"""
Assistente de calibração para outra máquina.

A outra pessoa clica nos mesmos lugares da UI que você mapeou.
O programa grava calibration.json com escala + deslocamento.

Uso:
  python tools\\calibrate.py           # guiar pelos 3 pontos
  python tools\\calibrate.py --status  # ver se há calibração
  python tools\\calibrate.py --clear   # remover calibração (volta ao mapa original)

Nesta máquina (referência): NÃO rode a calibração — sem o arquivo, nada muda.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import tkinter as tk
from pynput import keyboard
from tkinter import messagebox

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation import calibration, win_mouse

win_mouse.ensure_dpi_awareness()


class CalibrateApp:
    def __init__(self):
        self.points = list(calibration.REFERENCE_POINTS)
        self.index = 0
        self.captured = []  # type: List[Tuple[int, int]]
        self._listener = None

        self.root = tk.Tk()
        self.root.title("Calibração SAP 800")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1a1a2e", padx=20, pady=16)
        self.root.resizable(False, False)

        self.title = tk.Label(
            self.root,
            text="Calibração de coordenadas",
            font=("Segoe UI", 14, "bold"),
            fg="#e0e0e0",
            bg="#1a1a2e",
        )
        self.title.pack(anchor="w")

        self.progress = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 10),
            fg="#88aaff",
            bg="#1a1a2e",
        )
        self.progress.pack(anchor="w", pady=(8, 0))

        self.label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#1a1a2e",
            wraplength=420,
            justify="left",
        )
        self.label.pack(anchor="w", pady=(10, 0))

        self.hint = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 9),
            fg="#aaaaaa",
            bg="#1a1a2e",
            wraplength=420,
            justify="left",
        )
        self.hint.pack(anchor="w", pady=(6, 0))

        self.coords = tk.Label(
            self.root,
            text="X: ----   Y: ----",
            font=("Consolas", 12, "bold"),
            fg="#7CFC00",
            bg="#1a1a2e",
        )
        self.coords.pack(anchor="w", pady=(12, 0))

        self.keys_hint = tk.Label(
            self.root,
            text="F8 = capturar este ponto    ESC = cancelar",
            font=("Segoe UI", 9),
            fg="#8888aa",
            bg="#1a1a2e",
        )
        self.keys_hint.pack(anchor="w", pady=(10, 0))

        self.log = tk.Label(
            self.root,
            text="",
            font=("Consolas", 9),
            fg="#cccccc",
            bg="#1a1a2e",
            justify="left",
            wraplength=420,
        )
        self.log.pack(anchor="w", pady=(12, 0))

        self._show_current()
        self._listener = keyboard.Listener(on_press=self._on_key)
        self._listener.daemon = True
        self._listener.start()
        self._tick()

        self.root.protocol("WM_DELETE_WINDOW", self._cancel)

    def _tick(self):
        x, y = win_mouse.position()
        self.coords.config(text="X: {:4d}   Y: {:4d}".format(x, y))
        self.root.after(50, self._tick)

    def _show_current(self):
        total = len(self.points)
        if self.index >= total:
            return
        pt = self.points[self.index]
        self.progress.config(
            text="Ponto {}/{}  (ref original: {}, {})".format(
                self.index + 1, total, pt["x"], pt["y"]
            )
        )
        self.label.config(text=pt["label"])
        self.hint.config(text=pt.get("hint") or "")

    def _on_key(self, key):
        try:
            if key == keyboard.Key.f8:
                self.root.after(0, self._capture)
            elif key == keyboard.Key.esc:
                self.root.after(0, self._cancel)
        except Exception:
            pass

    def _capture(self):
        if self.index >= len(self.points):
            return
        x, y = win_mouse.position()
        self.captured.append((x, y))
        pt = self.points[self.index]
        lines = []
        for i, (cx, cy) in enumerate(self.captured):
            ref = self.points[i]
            lines.append(
                "{}: ref({},{}) → local({},{})".format(
                    ref["id"], ref["x"], ref["y"], cx, cy
                )
            )
        self.log.config(text="\n".join(lines))
        self.index += 1

        if self.index >= len(self.points):
            self._finish()
        else:
            self._show_current()

    def _finish(self):
        pairs = []
        for i, local in enumerate(self.captured):
            ref = self.points[i]
            pairs.append(((ref["x"], ref["y"]), local))

        transform = calibration.fit_transform(pairs)
        pairs_payload = [
            {
                "id": self.points[i]["id"],
                "ref": [self.points[i]["x"], self.points[i]["y"]],
                "local": [local[0], local[1]],
            }
            for i, local in enumerate(self.captured)
        ]
        path = calibration.save_transform(transform, pairs=pairs_payload)

        # Preview: primeiro e último ponto mapeados
        samples = []
        for ref_xy, local_xy in pairs:
            mapped = transform.map_xy(ref_xy[0], ref_xy[1])
            samples.append(
                "  ref{} → map{} (você clicou {})".format(ref_xy, mapped, local_xy)
            )

        msg = (
            "Calibração salva em:\n{}\n\n"
            "sx={:.4f}  sy={:.4f}\n"
            "ox={:.1f}  oy={:.1f}\n\n"
            "{}\n\n"
            "Agora rode python main.py nesta máquina."
        ).format(
            path,
            transform.sx,
            transform.sy,
            transform.ox,
            transform.oy,
            "\n".join(samples),
        )
        messagebox.showinfo("Calibração concluída", msg)
        self._stop()

    def _cancel(self):
        self._stop()

    def _stop(self):
        try:
            if self._listener is not None:
                self._listener.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def show_status():
    path = calibration.CALIBRATION_FILE
    if not path.exists():
        print("Sem calibração ({} não existe).".format(path.name))
        print("Esta máquina usa as coordenadas originais — ok para a referência.")
        return
    t = calibration.load_transform()
    print("Arquivo: {}".format(path))
    print("sx={:.4f} sy={:.4f} ox={:.1f} oy={:.1f}".format(t.sx, t.sy, t.ox, t.oy))
    if t.is_identity():
        print("(equivalente à identidade — não altera cliques)")


def main():
    if "--status" in sys.argv:
        show_status()
        return
    if "--clear" in sys.argv:
        if calibration.clear_calibration():
            print("Calibração removida. Coordenadas originais restauradas.")
        else:
            print("Não havia calibration.json.")
        return

    print("Assistente de calibração")
    print("1. Abra o SAP na mesma tela usada na Parte 1 (campos visíveis).")
    print("2. Posicione o mouse em cada ponto pedido e pressione F8.")
    print("3. Ao terminar, calibration.json será gerado nesta pasta.")
    print("")
    if calibration.CALIBRATION_FILE.exists():
        print("Atenção: já existe calibration.json — será sobrescrito.")
    CalibrateApp().run()


if __name__ == "__main__":
    main()
