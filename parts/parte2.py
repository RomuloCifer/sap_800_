"""
Parte 2 da automação SAP.

Fluxo:
  1. Confirmação / contagem para focar o SAP (pulados se chained=True)
  2. Passos 1–6 (fixos)
  3. Formulário: ISSUER SAP
  4. Contagem de 3 s
  5. Passos 7–8

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


def build_steps_before_issuer():
    # type: () -> list
    return [
        Step(
            "click_and_type",
            x=-1834,
            y=50,
            text="/oj1b1n",
            wiggle_x=20,
            label="1 — Clique e escrever /oj1b1n",
        ),
        Step(
            "click",
            x=-1889,
            y=51,
            label="2 — Clique",
        ),
        Step(
            "click_and_type",
            x=-1713,
            y=200,
            text="X0",
            label="3 — Clique e escrever X0",
        ),
        Step(
            "click_and_type",
            x=-1727,
            y=266,
            text="1300",
            delete_times=4,
            label="4 — Clique, Delete x4, escrever 1300",
        ),
        Step(
            "click_and_type",
            x=-1707,
            y=286,
            text="0001",
            label="5 — Clique e escrever 0001",
        ),
        Step(
            "click",
            x=-1692,
            y=329,
            wait_after=1.5,
            label="6a — Clique (espera 1,5s)",
        ),
        Step(
            "click",
            x=-1701,
            y=444,
            wiggle_x=20,
            label="6b — Segundo clique (com mexida L/R)",
        ),
    ]


def build_steps_after_issuer(issuer_sap):
    # type: (str) -> list
    return [
        Step(
            "click_and_type",
            x=-1703,
            y=351,
            text=issuer_sap,
            label="7 — Clique e escrever ISSUER SAP",
        ),
        Step(
            "click",
            x=-1884,
            y=54,
            label="8 — Clique",
        ),
    ]


def main(dry_run=False, chained=False, show_done=True):
    # type: (bool, bool, bool) -> bool
    """
    chained=True: veio direto da Parte 1 — sem confirmação nem contagem inicial.
    """
    if not chained:
        if not messagebox.askokcancel(
            "Parte 2 — Automação SAP",
            "Iniciar a Parte 2?\n\nDeixe a tela do SAP visível no monitor da esquerda.\n\n{} = parar.".format(
                abort.ABORT_KEY_NAME
            ),
        ):
            print("Cancelado pelo usuário.")
            return False

    if not chained:
        abort.start_listener()

    try:
        if not dry_run:
            if chained:
                countdown(2, "Parte 1 ok.\nIniciando Parte 2 em...")
            else:
                countdown(5, "Foque a tela do SAP!\nIniciando Parte 2 em...")

        run_steps(build_steps_before_issuer(), dry_run=dry_run)

        data = ask_fields(
            title="Parte 2 — ISSUER SAP",
            fields=[("issuer_sap", "ISSUER SAP")],
            start_label="Continuar",
        )
        if data is None:
            print("Cancelado no formulário ISSUER SAP.")
            return False

        issuer = data["issuer_sap"]
        print("ISSUER SAP informado: {}".format(issuer))

        if not dry_run:
            countdown(3, "Volte para o SAP!\nContinuando em...")

        run_steps(build_steps_after_issuer(issuer), dry_run=dry_run)

        print("\nParte 2 concluída.")
        if show_done and not dry_run:
            messagebox.showinfo("Parte 2", "Parte 2 concluída com sucesso.")
        return True
    except abort.AbortedError:
        messagebox.showwarning("Abortado", "Parte 2 interrompida ({}).".format(abort.ABORT_KEY_NAME))
        return False
    except Exception as exc:
        print("ERRO:", exc)
        traceback.print_exc()
        messagebox.showerror(
            "Erro na Parte 2",
            "A automação falhou:\n\n{}".format(exc),
        )
        return False
    finally:
        if show_done or not chained:
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
