"""
Fluxo completo: Parte 1 → 2 → 3 → 4 (encadeadas).

Após a Parte 1:
  - espera carregar
  - copia ISSUER SAP, INVOICE e ISSUE_DATE da tela
  - pede material, quantidade, price, description, cfop,
    protocol, proc date/time, random no e digit
  - guarda tudo para as Partes 2, 3 e 4

Uso:
  python main.py              # partes 1 a 4
  python main.py --ate-2      # só partes 1 e 2
  python main.py --dry-run

Emergência: F10 para a automação a qualquer momento.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinter import messagebox

from automation import abort, win_mouse
from automation.capture import drag_copy
from automation.forms import ask_fields
from parts import parte1, parte2, parte3, parte4
import config

win_mouse.ensure_dpi_awareness()

ISSUER_SELECT_FROM = (-949, 222)
ISSUER_SELECT_TO = (-896, 222)

INVOICE_SELECT_FROM = (-1759, 176)
INVOICE_SELECT_TO = (-1703, 176)

ISSUE_DATE_SELECT_FROM = (-950, 176)
ISSUE_DATE_SELECT_TO = (-871, 178)

# Formulário único após Parte 1 (dados das Partes 3 e 4)
FORM_AFTER_P1 = [
    ("material", "Material"),
    ("quantidade", "Quantidade"),
    ("price", "Price"),
    ("description", "Description"),
    ("cfop", "CFOP"),
    ("protocol_no", "PROTOCOL NO"),
    ("proc_date", "PROC DATE (dd.mm.yyyy)"),
    ("proc_time", "PROC TIME (hh:mm:ss)"),
    ("random_no", "RANDOM NO"),
    ("digit", "DIGIT"),
]


def _wait(seconds):
    # type: (float) -> None
    try:
        from automation.runner import _sleep as sleep_abortable
        sleep_abortable(seconds)
    except Exception:
        time.sleep(seconds)


def _clean(value):
    # type: (str) -> str
    return (value or "").replace("\xa0", " ").strip()


def main(dry_run=False, stop_after=None):
    # type: (bool, object) -> None
    abort.start_listener()
    try:
        ok = parte1.main(dry_run=dry_run, show_done=False)
        if not ok:
            print("Fluxo interrompido na Parte 1.")
            return

        if abort.is_aborted():
            return

        print("\nAguardando {:.0f}s após Parte 1 (carregar tela)...".format(config.WAIT_AFTER_PART1))
        if not dry_run:
            _wait(config.WAIT_AFTER_PART1)

        issuer = drag_copy(
            ISSUER_SELECT_FROM[0], ISSUER_SELECT_FROM[1],
            ISSUER_SELECT_TO[0], ISSUER_SELECT_TO[1],
            label="ISSUER SAP",
            dry_run=dry_run,
        )

        doc_data = None
        part4_data = None
        if stop_after != 2:
            invoice = drag_copy(
                INVOICE_SELECT_FROM[0], INVOICE_SELECT_FROM[1],
                INVOICE_SELECT_TO[0], INVOICE_SELECT_TO[1],
                label="INVOICE",
                dry_run=dry_run,
            )
            issue_date = drag_copy(
                ISSUE_DATE_SELECT_FROM[0], ISSUE_DATE_SELECT_FROM[1],
                ISSUE_DATE_SELECT_TO[0], ISSUE_DATE_SELECT_TO[1],
                label="ISSUE_DATE",
                dry_run=dry_run,
            )

            form = ask_fields(
                title="Dados para Partes 3 e 4",
                fields=FORM_AFTER_P1,
                start_label="Continuar",
            )
            if form is None:
                print("Cancelado no formulário pós Parte 1.")
                return

            doc_data = {
                "invoice": _clean(invoice),
                "issue_date": _clean(issue_date),
                "material": _clean(form["material"]),
                "quantidade": _clean(form["quantidade"]),
                "price": _clean(form["price"]),
                "description": _clean(form["description"]),
                "cfop": _clean(form["cfop"]),
            }
            part4_data = {
                "protocol_no": _clean(form["protocol_no"]),
                "proc_date": _clean(form["proc_date"]),
                "proc_time": _clean(form["proc_time"]),
                "random_no": _clean(form["random_no"]),
                "digit": _clean(form["digit"]),
            }
            print("\nDados guardados:")
            for k, v in doc_data.items():
                print("  {}: {!r}".format(k, v))
            for k, v in part4_data.items():
                print("  {}: {!r}".format(k, v))

        print("\n--- Seguindo para a Parte 2 ---\n")
        ok2 = parte2.main(
            dry_run=dry_run,
            chained=True,
            show_done=False,
            issuer_sap=issuer,
        )
        if not ok2:
            print("Fluxo interrompido na Parte 2.")
            return

        if stop_after == 2:
            if not dry_run:
                messagebox.showinfo("Automação SAP", "Partes 1 e 2 concluídas.")
            print("\nFluxo Parte 1+2 finalizado.")
            return

        if abort.is_aborted():
            return

        print("\n--- Seguindo para a Parte 3 ---\n")
        ok3 = parte3.main(
            dry_run=dry_run,
            chained=True,
            show_done=False,
            prefill=doc_data,
        )
        if not ok3:
            print("Fluxo interrompido na Parte 3.")
            return

        if abort.is_aborted():
            return

        print(
            "\nAguardando {:.0f}s antes da Parte 4...\n".format(
                config.WAIT_BETWEEN_PART3_PART4
            )
        )
        if not dry_run:
            _wait(config.WAIT_BETWEEN_PART3_PART4)

        print("--- Seguindo para a Parte 4 ---\n")
        ok4 = parte4.main(
            dry_run=dry_run,
            chained=True,
            show_done=False,
            prefill=part4_data,
        )
        if not ok4:
            print("Fluxo interrompido na Parte 4.")
            return

        if not dry_run:
            messagebox.showinfo(
                "Automação SAP",
                "Partes 1 a 4 concluídas com sucesso.",
            )
        print("\nFluxo completo finalizado.")
    finally:
        abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    ate2 = "--ate-2" in sys.argv
    main(dry_run=dry, stop_after=2 if ate2 else None)
