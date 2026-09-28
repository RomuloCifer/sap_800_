"""
Parte 1 da automação SAP.

Fluxo:
  1. Formulário pede o Batch
  2. Contagem regressiva visual (tempo para focar a tela do SAP)
  3. Executa a sequência de cliques/digitação
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tkinter as tk
from tkinter import messagebox

from automation import win_mouse
from automation.forms import ask_fields
from automation.runner import Step, run_steps

win_mouse.ensure_dpi_awareness()

COUNTDOWN_SECONDS = 5


def build_steps(batch):
    # type: (str) -> list
    return [
        Step(
            "double_click",
            x=-1150,
            y=544,
            label="1 — Duplo clique (abrir/focar)",
        ),
        Step(
            "click_and_type",
            x=-1827,
            y=58,
            text="/n/lkmt/ardfe",
            label="2 — Clique e escrever /n/lkmt/ardfe",
        ),
        Step(
            "click",
            x=-1895,
            y=53,
            seconds=3.0,
            label="4 — Clique e esperar 3 segundos",
        ),
        Step(
            "click",
            x=-1109,
            y=344,
            label="5 — Clique",
        ),
        Step(
            "click_and_type",
            x=-1616,
            y=267,
            text="1300",
            label="6 — Clique e escrever 1300 (FIXO)",
        ),
        Step(
            "click_and_type",
            x=-1617,
            y=290,
            text="*",
            label="7 — Clique e escrever * (FIXO)",
        ),
        Step(
            "click_and_type",
            x=-1617,
            y=309,
            text=batch,
            label="8 — Clique e escrever BATCH",
        ),
        Step(
            "click",
            x=-1891,
            y=123,
            label="9 — Clique",
        ),
        Step(
            "click",
            x=-1869,
            y=123,
            label="10 — Clique",
        ),
    ]


def countdown(seconds=COUNTDOWN_SECONDS):
    # type: (int) -> None
    root = tk.Tk()
    root.title("Aguarde")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#1a1a2e", padx=24, pady=20)

    tk.Label(
        root,
        text="Foque a tela do SAP!\nIniciando em...",
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

    root.update_idletasks()
    w = root.winfo_width()
    sw = root.winfo_screenwidth()
    root.geometry("+{}+40".format((sw - w) // 2))

    for n in range(seconds, 0, -1):
        number.config(text=str(n))
        root.update()
        time.sleep(1)

    root.destroy()


def main(dry_run=False):
    # type: (bool) -> None
    data = ask_fields(
        title="Parte 1 — Automação SAP",
        fields=[("batch", "Batch number")],
        start_label="Iniciar Parte 1",
    )
    if data is None:
        print("Cancelado pelo usuário.")
        return

    batch = data["batch"]
    print("Batch informado: {}".format(batch))
    steps = build_steps(batch)

    try:
        if not dry_run:
            countdown()
        run_steps(steps, dry_run=dry_run)
        print("\nParte 1 concluída.")
        if not dry_run:
            messagebox.showinfo("Parte 1", "Parte 1 concluída com sucesso.")
    except Exception as exc:
        print("ERRO:", exc)
        traceback.print_exc()
        messagebox.showerror(
            "Erro na Parte 1",
            "A automação falhou:\n\n{}".format(exc),
        )


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
