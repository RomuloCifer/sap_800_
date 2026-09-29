"""
Parte 3 da automação SAP.

No fluxo completo (main.py), invoice/issue_date vêm da tela após a Parte 1
e material/quantidade/price/description/cfop do formulário pós Parte 1.
Aqui só pede Plant (ou o formulário completo se rodar sozinha).
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
import config

win_mouse.ensure_dpi_awareness()

WAIT_TAX_OPTION = 1.2
CHAR_INTERVAL_TAX = 0.2

FORM_FIELDS = [
    ("invoice", "Invoice (sem os 000)"),
    ("issue_date", "Issue date (dd.mm.yyyy)"),
    ("material", "Material"),
    ("quantidade", "Quantidade"),
    ("price", "Price"),
    ("description", "Description"),
    ("cfop", "CFOP"),
    ("plant", "Plant"),
]


def _clean(value):
    # type: (str) -> str
    return value.replace("\xa0", " ").strip()


def _tax_row(label, x_type, y_type, code, x_pick, y_pick):
    # type: (str, int, int, str, int, int) -> list
    """Digita letra a letra, espera opção, clique com mexida L/R."""
    return [
        Step(
            "click_and_type",
            x=x_type,
            y=y_type,
            text=code,
            type_slowly=True,
            char_interval=CHAR_INTERVAL_TAX,
            wait_after=WAIT_TAX_OPTION,
            label="{} — Digitar {} (letra a letra)".format(label, code),
        ),
        Step(
            "click",
            x=x_pick,
            y=y_pick,
            wiggle_x=20,
            label="{} — Clique na opção {}".format(label, code),
        ),
    ]


def build_steps(data):
    # type: (dict) -> list
    invoice_raw = _clean(data["invoice"])
    if invoice_raw.startswith("000"):
        invoice = invoice_raw
    else:
        invoice = "000" + invoice_raw
    issue_date = _clean(data["issue_date"])
    material = _clean(data["material"])
    quantidade = _clean(data["quantidade"])
    price = _clean(data["price"])
    description = _clean(data["description"])
    cfop = _clean(data["cfop"])
    plant = _clean(data["plant"])

    steps = [
        Step(
            "click_and_type",
            x=-1741,
            y=178,
            text=invoice,
            label="1 — Clique e escrever 000+INVOICE",
        ),
        Step(
            "click_and_type",
            x=-1668,
            y=176,
            text="001",
            label="2 — Clique e escrever 001",
        ),
        Step(
            "click_and_type",
            x=-1723,
            y=196,
            text=issue_date,
            label="3 — Clique e escrever ISSUE_DATE",
        ),
        Step(
            "click_and_type",
            x=-1784,
            y=393,
            text="1",
            label="4 — Clique e escrever 1",
        ),
        Step(
            "click_and_type",
            x=-1705,
            y=396,
            text=material,
            label="5 — Clique e escrever Material",
        ),
        Step(
            "click_and_type",
            x=-1584,
            y=396,
            text=description,
            label="6 — Clique e escrever Description",
        ),
        Step(
            "click_and_type",
            x=-1390,
            y=396,
            text=quantidade,
            label="7 — Clique e escrever Quantidade",
        ),
        Step(
            "click_and_type",
            x=-1291,
            y=396,
            text=price,
            label="8 — Clique e escrever Price",
        ),
        Step(
            "click_and_type",
            x=-1149,
            y=396,
            text=cfop,
            label="9 — Clique e escrever CFOP",
        ),
    ]

    steps.extend(_tax_row("10 ICMS", -1074, 396, "IC9", -1023, 434))
    steps.extend(_tax_row("11 IPI", -1005, 396, "I49", -977, 434))
    steps.extend(_tax_row("12 COFINS", -957, 396, "C70", -921, 434))
    steps.extend(_tax_row("13 PIS", -906, 393, "P70", -879, 434))

    steps.extend(
        [
            Step(
                "click_and_type",
                x=-848,
                y=392,
                text=plant,
                label="14 — Clique e escrever PLANT",
            ),
            Step(
                "click_and_press",
                x=-1788,
                y=396,
                keys=["enter"],
                press_times=2,
                press_interval=0.3,
                label="15 — Clique e Enter x2",
            ),
            Step(
                "click",
                x=-1886,
                y=392,
                label="16 — Clique",
            ),
            Step(
                "click",
                x=-1624,
                y=958,
                label="17 — Clique (fim Parte 3)",
            ),
        ]
    )
    return steps


def main(dry_run=False, chained=False, show_done=True, prefill=None):
    # type: (bool, bool, bool, object) -> bool
    prefill = dict(prefill) if prefill else {}

    if prefill:
        plant_form = ask_fields(
            title="Parte 3 — Plant",
            fields=[("plant", "Plant")],
            start_label="Iniciar Parte 3",
        )
        if plant_form is None:
            print("Cancelado pelo usuário.")
            return False
        data = {k: _clean(v) for k, v in prefill.items()}
        data["plant"] = _clean(plant_form["plant"])
    else:
        data = ask_fields(
            title="Parte 3 — Dados do documento",
            fields=FORM_FIELDS,
            start_label="Iniciar Parte 3",
        )
        if data is None:
            print("Cancelado pelo usuário.")
            return False
        data = {k: _clean(v) for k, v in data.items()}

    print("Parte 3 — dados:")
    for key, _label in FORM_FIELDS:
        shown = data.get(key, "")
        if key == "invoice":
            inv = _clean(shown)
            shown = inv if inv.startswith("000") else "000" + inv
        print("  {}: {!r}".format(key, shown))

    if not chained:
        abort.start_listener()

    try:
        if not dry_run:
            if chained:
                countdown(config.COUNTDOWN_PART3, "Dados da Parte 3 ok.\nVolte ao SAP — iniciando em...")
            else:
                countdown(config.COUNTDOWN_PART3_SOLO, "Foque a tela do SAP!\nIniciando Parte 3 em...")

        run_steps(build_steps(data), dry_run=dry_run)

        print("\nParte 3 concluída.")
        if show_done and not dry_run:
            messagebox.showinfo("Parte 3", "Parte 3 concluída com sucesso.")
        return True
    except abort.AbortedError:
        messagebox.showwarning(
            "Abortado",
            "Parte 3 interrompida ({}).".format(abort.ABORT_KEY_NAME),
        )
        return False
    except Exception as exc:
        print("ERRO:", exc)
        traceback.print_exc()
        messagebox.showerror(
            "Erro na Parte 3",
            "A automação falhou:\n\n{}".format(exc),
        )
        return False
    finally:
        if show_done or not chained:
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
