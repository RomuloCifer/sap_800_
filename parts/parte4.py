"""
Parte 4 da automação SAP.

No fluxo completo, PROTOCOL/PROC DATE/TIME/RANDOM/DIGIT vêm do formulário
após a Parte 1. Passos 1–5 → captura VALUE → passos 6–20.
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
from automation.capture import drag_copy
from automation.forms import ask_fields, validate_random_no
from automation.runner import Step, run_steps
from automation.ui import countdown
from automation.utils import build_tax_steps, clean_value
import config

win_mouse.ensure_dpi_awareness()

WAIT_AFTER_STEP_14 = 2.0

VALUE_SELECT_FROM = (-1680, 288)
VALUE_SELECT_TO = (-1602, 288)

START_FIELDS = [
    ("protocol_no", "PROTOCOL NO"),
    ("proc_date", "PROC DATE (dd.mm.yyyy)"),
    ("proc_time", "PROC TIME (hh:mm:ss)"),
]


def capture_value_from_screen(dry_run=False):
    # type: (bool) -> str
    return drag_copy(
        VALUE_SELECT_FROM[0],
        VALUE_SELECT_FROM[1],
        VALUE_SELECT_TO[0],
        VALUE_SELECT_TO[1],
        label="VALUE",
        dry_run=dry_run,
    )


def build_steps_before_value():
    # type: () -> list
    steps = []
    steps.extend(build_tax_steps("1", -1855, 391, "ICOF", -1821, 432))
    steps.extend(build_tax_steps("2", -1855, 414, "ICM0", -1798, 452))
    steps.extend(build_tax_steps("3", -1855, 433, "IPI0", -1789, 474))
    steps.extend(build_tax_steps("4", -1855, 455, "IPIS", -1789, 494))
    steps.append(
        Step(
            "click_and_press",
            x=-1852,
            y=391,
            keys=["enter"],
            press_times=5,
            press_interval=0.3,
            label="5 — Clique e Enter x5",
        )
    )
    return steps


def build_steps_middle(value, start_data):
    # type: (str, dict) -> list
    """Passos 6–18 (até PROC TIME)."""
    return [
        Step(
            "click_and_type",
            x=-1315,
            y=395,
            text=value,
            label="6 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_type",
            x=-1333,
            y=413,
            text=value,
            label="7 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_type",
            x=-1333,
            y=437,
            text=value,
            label="8 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_type",
            x=-1333,
            y=458,
            text=value,
            label="9 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_press",
            x=-1321,
            y=393,
            keys=["enter"],
            press_times=1,
            label="10 — Clique e Enter",
        ),
        Step(
            "click",
            x=-1636,
            y=221,
            label="11 — Clique",
        ),
        Step(
            "click_and_type",
            x=-1521,
            y=289,
            text="403",
            label="12 — Clique e escrever 403",
        ),
        Step(
            "click",
            x=-1812,
            y=227,
            label="13 — Clique",
        ),
        Step(
            "click",
            x=-1871,
            y=119,
            wait_after=WAIT_AFTER_STEP_14,
            label="14 — Clique e esperar 2s",
        ),
        Step(
            "click",
            x=-1226,
            y=239,
            label="15 — Clique",
        ),
        Step(
            "click_and_type",
            x=-1715,
            y=304,
            text=start_data["protocol_no"],
            label="16 — Clique e escrever PROTOCOL NO",
        ),
        Step(
            "click_and_type",
            x=-1721,
            y=330,
            text=start_data["proc_date"],
            label="17 — Clique e escrever PROC DATE",
        ),
        Step(
            "click_and_type",
            x=-1733,
            y=350,
            text=start_data["proc_time"],
            delete_times=9,
            label="18 — Clique, Delete x9, escrever PROC TIME",
        ),
    ]


def build_steps_random_digit(random_no, digit):
    # type: (str, str) -> list
    return [
        Step(
            "click_and_type",
            x=-1446,
            y=522,
            text=random_no,
            label="19 — Clique e escrever RANDOM NO",
        ),
        Step(
            "click_and_type",
            x=-1470,
            y=545,
            text=digit,
            delete_times=1,
            label="20 — Clique, Delete x1, escrever DIGIT",
        ),
    ]


def main(dry_run=False, chained=False, show_done=True, prefill=None):
    # type: (bool, bool, bool, object) -> bool
    """
    prefill: dict com protocol_no, proc_date, proc_time, random_no, digit
             (vindo do formulário após a Parte 1).
    """
    prefill = dict(prefill) if prefill else {}

    if prefill:
        start_data = {
            "protocol_no": clean_value(prefill["protocol_no"]),
            "proc_date": clean_value(prefill["proc_date"]),
            "proc_time": clean_value(prefill["proc_time"]),
        }
        random_no = clean_value(prefill["random_no"])
        digit = clean_value(prefill["digit"])
    else:
        start = ask_fields(
            title="Parte 4 — Dados iniciais",
            fields=START_FIELDS
            + [
                ("random_no", "RANDOM NO (8 dígitos)"),
                ("digit", "DIGIT"),
            ],
            start_label="Continuar",
            validators={"random_no": validate_random_no},
        )
        if start is None:
            print("Cancelado no formulário inicial da Parte 4.")
            return False
        start_data = {k: clean_value(start[k]) for k, _ in START_FIELDS}
        random_no = clean_value(start["random_no"])
        digit = clean_value(start["digit"])

    print("Parte 4 — dados:")
    for key, val in start_data.items():
        print("  {}: {!r}".format(key, val))
    print("  random_no: {!r}".format(random_no))
    print("  digit: {!r}".format(digit))

    if not chained:
        abort.start_listener()

    try:
        if not dry_run:
            if chained:
                countdown(
                    config.COUNTDOWN_BETWEEN_PARTS,
                    "Iniciando Parte 4 em...",
                )
            else:
                countdown(
                    config.COUNTDOWN_START,
                    "Foque a tela do SAP!\nIniciando Parte 4 em...",
                )

        run_steps(build_steps_before_value(), dry_run=dry_run)

        value = capture_value_from_screen(dry_run=dry_run)

        run_steps(build_steps_middle(value, start_data), dry_run=dry_run)
        run_steps(build_steps_random_digit(random_no, digit), dry_run=dry_run)

        print("\nParte 4 concluída.")
        if show_done and not dry_run:
            messagebox.showinfo("Parte 4", "Parte 4 concluída com sucesso.")
        return True
    except abort.AbortedError:
        messagebox.showwarning(
            "Abortado",
            "Parte 4 interrompida ({}).".format(abort.ABORT_KEY_NAME),
        )
        return False
    except Exception as exc:
        print("ERRO:", exc)
        traceback.print_exc()
        messagebox.showerror(
            "Erro na Parte 4",
            "A automação falhou:\n\n{}".format(exc),
        )
        return False
    finally:
        if show_done or not chained:
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
