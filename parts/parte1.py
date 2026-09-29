"""
Parte 1 da automação SAP.

Fluxo:
  1. Formulário pede o Batch
  2. Contagem regressiva visual (tempo para focar a tela do SAP)
  3. Executa a sequência de cliques/digitação

Retorna True se concluiu com sucesso, False se cancelou/erro.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinter import messagebox

from automation import abort, win_mouse
from automation.forms import ask_fields
from automation.runner import Step, run_steps
from automation.ui import countdown

win_mouse.ensure_dpi_awareness()

COUNTDOWN_SECONDS = 5


def build_steps(batch):
    # type: (str) -> list
    return [
        Step(
            "double_click",
            x=-1150,
            y=530,
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


def main(dry_run=False, show_done=True):
    # type: (bool, bool) -> bool
    data = ask_fields(
        title="Parte 1 — Automação SAP",
        fields=[("batch", "Batch number")],
        start_label="Iniciar Parte 1",
    )
    if data is None:
        print("Cancelado pelo usuário.")
        return False

    batch = data["batch"]
    print("Batch informado: {}".format(batch))
    steps = build_steps(batch)

    abort.start_listener()
    try:
        if not dry_run:
            countdown(COUNTDOWN_SECONDS, "Foque a tela do SAP!\nIniciando em...")
        run_steps(steps, dry_run=dry_run)
        print("\nParte 1 concluída.")
        if show_done and not dry_run:
            messagebox.showinfo("Parte 1", "Parte 1 concluída com sucesso.")
        return True
    except abort.AbortedError:
        messagebox.showwarning("Abortado", "Parte 1 interrompida ({}).".format(abort.ABORT_KEY_NAME))
        return False
    except Exception as exc:
        print("ERRO:", exc)
        traceback.print_exc()
        messagebox.showerror(
            "Erro na Parte 1",
            "A automação falhou:\n\n{}".format(exc),
        )
        return False
    finally:
        if show_done:
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
