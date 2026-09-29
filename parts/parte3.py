"""
Parte 3 da automação SAP (trecho inicial — passos 1–14).

Formulário no início:
  invoice, issue_date, material, quantidade, price, description, cfop, plant

Invoice no SAP: "000" + valor informado.
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
    """Remove espaços no início/fim (inclui NBSP colado de planilha)."""
    return value.replace("\xa0", " ").strip()


def build_steps(data):
    # type: (dict) -> list
    invoice = "000" + _clean(data["invoice"])
    issue_date = _clean(data["issue_date"])
    material = _clean(data["material"])
    quantidade = _clean(data["quantidade"])
    price = _clean(data["price"])
    description = _clean(data["description"])
    cfop = _clean(data["cfop"])
    plant = _clean(data["plant"])

    return [
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
            x=-1706,
            y=393,
            text=material,
            label="5 — Clique e escrever Material",
        ),
        Step(
            "click_and_type",
            x=-1636,
            y=393,
            text=quantidade,
            label="6 — Clique e escrever Quantidade",
        ),
        Step(
            "click_and_type",
            x=-1551,
            y=392,
            text=price,
            label="7 — Clique e escrever Price",
        ),
        Step(
            "click_and_type",
            x=-1348,
            y=393,
            text=description,
            label="8 — Clique e escrever Description",
        ),
        Step(
            "click_and_type",
            x=-1136,
            y=392,
            text=cfop,
            label="9 — Clique e escrever CFOP",
        ),
        Step(
            "click_and_type",
            x=-1051,
            y=392,
            text="IC9",
            tab_after=True,
            label="10 — Clique, escrever IC9 e TAB",
        ),
        Step(
            "click_and_type",
            x=-1022,
            y=394,
            text="I49",
            tab_after=True,
            label="11 — Clique, escrever I49 e TAB",
        ),
        Step(
            "click_and_type",
            x=-994,
            y=392,
            text="C70",
            tab_after=True,
            label="12 — Clique, escrever C70 e TAB",
        ),
        Step(
            "click_and_type",
            x=-966,
            y=394,
            text="P70",
            tab_after=True,
            label="13 — Clique, escrever P70 e TAB",
        ),
        Step(
            "click_and_type",
            x=-861,
            y=393,
            text=plant,
            label="14 — Clique e escrever PLANT",
        ),
    ]


def main(dry_run=False, chained=False, show_done=True):
    # type: (bool, bool, bool) -> bool
    data = ask_fields(
        title="Parte 3 — Dados do documento",
        fields=FORM_FIELDS,
        start_label="Iniciar Parte 3",
    )
    if data is None:
        print("Cancelado pelo usuário.")
        return False

    # Limpa espaços (ex.: " 5000.00", " 0.26")
    data = {k: _clean(v) for k, v in data.items()}

    print("Parte 3 — dados:")
    for key, _label in FORM_FIELDS:
        shown = data[key]
        if key == "invoice":
            shown = "000" + data[key]
        print("  {}: {!r}".format(key, shown))

    if not chained:
        abort.start_listener()

    try:
        if not dry_run:
            if chained:
                countdown(6, "Dados da Parte 3 ok.\nVolte ao SAP — iniciando em...")
            else:
                countdown(7, "Foque a tela do SAP!\nIniciando Parte 3 em...")

        run_steps(build_steps(data), dry_run=dry_run)

        print("\nParte 3 (trecho atual) concluída.")
        if show_done and not dry_run:
            messagebox.showinfo(
                "Parte 3",
                "Parte 3 (passos 1–14) concluída.\nQuando tiver o restante, seguimos.",
            )
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
