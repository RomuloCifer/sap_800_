"""
Parte 2 da automação SAP.

Quando vem da Parte 1 com issuer_sap já capturado, não pede formulário.
Business place vem da tela (após Issue Date); se ausente, mantém 0001.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinter import messagebox

from automation import abort, docmap, localmap, win_mouse
from automation.forms import ask_fields
from automation.runner import Step, run_steps
from automation.ui import countdown
from automation.utils import clean_value
import config

win_mouse.ensure_dpi_awareness()

DEFAULT_BUSINESS_PLACE = "0001"


def _normalize_business_place(value):
    # type: (object) -> str
    """Mantém dígitos; completa com zeros à esquerda até 4 (ex.: 15 → 0015)."""
    text = clean_value(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return DEFAULT_BUSINESS_PLACE
    if len(digits) >= 4:
        return digits
    return digits.zfill(4)


def build_steps_before_issuer(business_place=DEFAULT_BUSINESS_PLACE):
    # type: (str) -> list
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
            text=business_place,
            label="5 — Clique e escrever BUSINESS PLACE ({})".format(business_place),
        ),
        Step(
            "click",
            x=-1692,
            y=329,
            wait_after=config.WAIT_BETWEEN_DROPDOWN,
            label="6a — Clique (espera dropdown)",
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


def main(
    dry_run=False,
    chained=False,
    show_done=True,
    issuer_sap=None,
    business_place=None,
):
    # type: (bool, bool, bool, object, object) -> bool
    """
    chained=True: veio da Parte 1.
    issuer_sap: se informado, não abre formulário (capturado da tela).
    business_place: capturado após Issue Date; default 0001.
    """
    docmap.enable_from_argv()
    localmap.enable_from_argv()
    docmap.begin_part("parte2")
    localmap.begin_part("parte2")
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
                countdown(config.COUNTDOWN_BETWEEN_PARTS, "Parte 1 ok.\nIniciando Parte 2 em...")
            else:
                countdown(config.COUNTDOWN_START, "Foque a tela do SAP!\nIniciando Parte 2 em...")

        bp = _normalize_business_place(business_place)
        print("BUSINESS PLACE: {!r}".format(bp))
        run_steps(build_steps_before_issuer(bp), dry_run=dry_run)

        if issuer_sap:
            issuer = issuer_sap.strip()
            print("ISSUER SAP (capturado): {!r}".format(issuer))
        else:
            data = ask_fields(
                title="Parte 2 — ISSUER SAP",
                fields=[("issuer_sap", "ISSUER SAP")],
                start_label="Continuar",
            )
            if data is None:
                print("Cancelado no formulário ISSUER SAP.")
                return False
            issuer = data["issuer_sap"].strip()
            print("ISSUER SAP informado: {}".format(issuer))
            if not dry_run:
                countdown(config.COUNTDOWN_AFTER_ISSUER, "Volte para o SAP!\nContinuando em...")

        run_steps(build_steps_after_issuer(issuer), dry_run=dry_run)

        print("\nParte 2 concluída.")
        if show_done and not dry_run:
            messagebox.showinfo("Parte 2", "Parte 2 concluída com sucesso.")
        return True
    except abort.AbortedError:
        messagebox.showwarning(
            "Abortado",
            "Parte 2 interrompida ({}).".format(abort.ABORT_KEY_NAME),
        )
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
            docmap.finish()
            localmap.finish()
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
