"""
Assistente de calibração para outra máquina.

A outra pessoa clica nos mesmos lugares da UI que você mapeou.
O programa grava calibration.json com escala + deslocamento.

Uso:
  python tools\\calibrate.py           # guiar pelos pontos
  python tools\\calibrate.py --status  # ver se há calibração
  python tools\\calibrate.py --clear   # remover calibração (volta ao mapa original)

Nesta máquina (referência): NÃO rode a calibração — sem o arquivo, nada muda.
"""

from __future__ import annotations

import math
import sys
import time
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

WARN_RESIDUAL_PX = 35


class CalibrateApp:
    def __init__(self):
        self.points = list(calibration.REFERENCE_POINTS)
        self.index = 0
        self.captured = []  # type: List[Tuple[int, int]]
        self._listener = None
        self._phase = "capture"  # capture | verify
        self._pending_transform = None
        self._pending_pairs = None
        self._pending_payload = None

        self.root = tk.Tk()
        self.root.title("Calibração SAP 800")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1a1a2e", padx=20, pady=16)
        self.root.resizable(False, False)

        # Threshold dinâmico: 20% da altura da tela (mínimo 150 px).
        self._min_y_gap = max(150, int(self.root.winfo_screenheight() * 0.20))

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
            wraplength=460,
            justify="left",
        )
        self.label.pack(anchor="w", pady=(10, 0))

        self.hint = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 9),
            fg="#aaaaaa",
            bg="#1a1a2e",
            wraplength=460,
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
            wraplength=460,
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
            text="Ponto {}/{} — posicione o mouse e aperte F8".format(
                self.index + 1, total
            )
        )
        self.label.config(text=pt.label)
        self.hint.config(text=pt.hint)

    def _refresh_log(self):
        lines = []
        for i, (cx, cy) in enumerate(self.captured):
            ref = self.points[i]
            lines.append(
                "{}. {} → local ({}, {})".format(i + 1, ref.id, cx, cy)
            )
        self.log.config(text="\n".join(lines))

    def _on_key(self, key):
        try:
            if key == keyboard.Key.f8:
                self.root.after(0, self._on_f8)
            elif key == keyboard.Key.esc:
                self.root.after(0, self._cancel)
            else:
                name = getattr(key, "char", None)
                if name and name.lower() == "r" and self._phase == "verify":
                    self.root.after(0, self._restart)
        except Exception:
            pass

    def _on_f8(self):
        if self._phase == "capture":
            self._capture()
        elif self._phase == "verify":
            self._save_and_exit()

    def _capture(self):
        if self.index >= len(self.points):
            return
        x, y = win_mouse.position()
        self.captured.append((x, y))
        self._refresh_log()

        if self.points[self.index].id == "rodape":
            data_idx = next(
                (i for i, p in enumerate(self.points) if p.id == "data"), None
            )
            if data_idx is not None and data_idx < len(self.captured) - 1:
                y_data = self.captured[data_idx][1]
                gap = y - y_data
                if gap < self._min_y_gap:
                    self.captured.pop()
                    messagebox.showwarning(
                        "Ponto 4 muito alto",
                        "Esse clique ficou perto demais do campo da data "
                        "(diferença em Y: {} px; mínimo: {} px).\n\n"
                        "Desça o mouse até o RODAPÉ da janela do SAP "
                        "(bem embaixo, ainda dentro do SAP) e tente de novo com F8.".format(
                            gap, self._min_y_gap
                        ),
                    )
                    self._refresh_log()
                    return

        self.index += 1
        if self.index >= len(self.points):
            self._prepare_verify()
        else:
            self._show_current()

    def _prepare_verify(self):
        pairs = []
        for i, local in enumerate(self.captured):
            ref = self.points[i]
            pairs.append(((ref.x, ref.y), local))

        transform = calibration.fit_transform(pairs)
        payload = [
            {
                "id": self.points[i].id,
                "ref": [self.points[i].x, self.points[i].y],
                "local": [local[0], local[1]],
            }
            for i, local in enumerate(self.captured)
        ]

        residuals = []
        warn_ids = []
        for i, (ref_xy, local_xy) in enumerate(pairs):
            mapped = transform.map_xy(ref_xy[0], ref_xy[1])
            err = math.hypot(mapped[0] - local_xy[0], mapped[1] - local_xy[1])
            residuals.append((self.points[i].id, mapped, local_xy, err))
            if err > WARN_RESIDUAL_PX:
                warn_ids.append(self.points[i].id)

        lines = [
            "Verificação — o mouse vai passar pelos pontos mapeados.",
            "sx={:.4f} sy={:.4f} ox={:.1f} oy={:.1f}".format(
                transform.sx, transform.sy, transform.ox, transform.oy
            ),
        ]
        for pid, mapped, local_xy, err in residuals:
            flag = " ⚠" if err > WARN_RESIDUAL_PX else " ok"
            lines.append(
                "{}: map{} vs clique{}  err={:.0f}px{}".format(
                    pid, mapped, local_xy, err, flag
                )
            )
        self.log.config(text="\n".join(lines))

        if warn_ids:
            messagebox.showwarning(
                "Calibração imprecisa",
                "Os pontos {} ficaram com erro alto (>{} px).\n"
                "Provavelmente algum clique foi no lugar errado.\n\n"
                "Vou mover o mouse para você conferir.\n"
                "Depois: F8 = salvar mesmo assim  |  R = refazer  |  ESC = cancelar".format(
                    ", ".join(warn_ids), WARN_RESIDUAL_PX
                ),
            )
        else:
            messagebox.showinfo(
                "Conferir pontos",
                "Vou mover o mouse pelos {} pontos mapeados.\n"
                "Olhe se o cursor cai no lugar certo de cada um.\n\n"
                "Depois: F8 = salvar  |  R = refazer  |  ESC = cancelar".format(
                    len(self.points)
                ),
            )

        self._pending_transform = transform
        self._pending_pairs = pairs
        self._pending_payload = payload
        self._phase = "verify"
        self.progress.config(text="Verificação — olhe o cursor na tela")
        self.label.config(text="Conferindo pontos mapeados…")
        self.hint.config(
            text="F8 = salvar calibração    R = refazer do zero    ESC = cancelar"
        )
        self.keys_hint.config(
            text="F8 = salvar    R = refazer    ESC = cancelar"
        )

        self.root.after(300, self._run_preview)

    def _in_virtual_screen(self, x, y):
        # type: (int, int) -> bool
        """Retorna True se (x, y) está dentro do desktop virtual (com margem)."""
        vx, vy, vw, vh = win_mouse._virtual_screen_metrics()
        margin = 200
        return (
            vx - margin <= x <= vx + vw + margin
            and vy - margin <= y <= vy + vh + margin
        )

    def _run_preview(self):
        if self._pending_transform is None:
            return
        transform = self._pending_transform
        for i, pt in enumerate(self.points):
            mapped = transform.map_xy(pt.x, pt.y)
            if not self._in_virtual_screen(mapped[0], mapped[1]):
                self.label.config(
                    text="⚠ Ponto {} ({}) mapeado fora da tela {} — calibração pode estar errada!".format(
                        i + 1, pt.id, mapped
                    )
                )
                self.root.update_idletasks()
                time.sleep(1.1)
                continue
            self.label.config(
                text="Cursor → ponto {} ({}) em {}".format(i + 1, pt.id, mapped)
            )
            self.root.update_idletasks()
            win_mouse.move_to(mapped[0], mapped[1])
            time.sleep(1.1)
        self.label.config(
            text="Pronto. F8 para salvar, R para refazer, ESC para cancelar."
        )

    def _save_and_exit(self):
        if self._pending_transform is None:
            return
        path = calibration.save_transform(
            self._pending_transform, pairs=self._pending_payload
        )
        t = self._pending_transform
        messagebox.showinfo(
            "Calibração salva",
            "Arquivo:\n{}\n\n"
            "sx={:.4f}  sy={:.4f}\n"
            "ox={:.1f}  oy={:.1f}\n\n"
            "Agora rode: python main.py".format(
                path, t.sx, t.sy, t.ox, t.oy
            ),
        )
        self._stop()

    def _restart(self):
        self.index = 0
        self.captured = []
        self._phase = "capture"
        self._pending_transform = None
        self._pending_pairs = None
        self._pending_payload = None
        self.keys_hint.config(text="F8 = capturar este ponto    ESC = cancelar")
        self.log.config(text="")
        self._show_current()

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

    print("Assistente de calibração (4 pontos)")
    print("1. Barra de comando SAP")
    print("2. Campo Empresa (1300)")
    print("3. Campo da DATA (01.02.2025) — NÃO o rodapé")
    print("4. Rodapé da janela SAP (bem embaixo, ainda dentro do SAP)")
    print("")
    print("No fim o mouse passa pelos pontos para você conferir.")
    print("F8 salva | R refaz | ESC cancela")
    print("")
    if calibration.clear_calibration():
        print("Calibração anterior removida — começando do zero.")
    CalibrateApp().run()


if __name__ == "__main__":
    main()
