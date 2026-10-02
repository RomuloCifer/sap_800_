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

from automation import abort, docmap, localmap, win_mouse
from automation.capture import drag_copy
from automation.forms import ask_fields, validate_random_no
from automation.runner import Step, run_steps
from automation.ui import countdown
from automation.utils import clean_value
from automation.value_ocr import (
    capture_print_b,
    compare_total_values,
    normalize_money,
)
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


# Células de imposto (clique + colar código + Enter x2)
_TAX_CELLS_LEGACY = (
    ("1", -1855, 391, "ICOF"),
    ("2", -1855, 414, "ICM0"),
    ("3", -1855, 433, "IPI0"),
    ("4", -1855, 455, "IPIS"),
)
_TAX_CELLS_2026_EXTRA = (
    ("5", -1864, 480, "CBS1"),
    ("6", -1863, 498, "IB2S"),
)

# Pastas de VALUE (Other base) — coordenadas por regra de Issue Date
_VALUE_PASTE_LEGACY = (
    (-1315, 395),
    (-1333, 413),
    (-1333, 437),
    (-1333, 458),
)
_VALUE_PASTE_2026 = (
    (-1312, 412),
    (-1312, 455),
    (-1312, 477),
    (-1312, 498),
)


def _tax_click_type_enter(label, x, y, code):
    # type: (str, int, int, str) -> list
    """Clique na célula, cola o código (Ctrl+V) e Enter x2 — sem dropdown."""
    return [
        Step(
            "click_and_type",
            x=x,
            y=y,
            text=code,
            label="{} — Clique e escrever {}".format(label, code),
        ),
        Step(
            "press",
            keys=["enter"],
            press_times=2,
            press_interval=0.3,
            label="{} — Enter x2 ({})".format(label, code),
        ),
    ]


def build_steps_before_value(taxes_2026_plus=False):
    # type: (bool) -> list
    """
    Impostos iniciais: clique + código + Enter x2 em cada taxa.
    Antes de 2026: ICOF/ICM0/IPI0/IPIS (4).
    2026+: + CBS1 e IB2S (6) e 2 cliques extras antes do VALUE.
    """
    steps = []
    for label, x, y, code in _TAX_CELLS_LEGACY:
        steps.extend(_tax_click_type_enter(label, x, y, code))
    if taxes_2026_plus:
        for label, x, y, code in _TAX_CELLS_2026_EXTRA:
            steps.extend(_tax_click_type_enter(label, x, y, code))
        steps.append(
            Step("click", x=-1151, y=393, label="6b — Clique após IB2S")
        )
        steps.append(
            Step("click", x=-1151, y=435, label="6c — Clique após IB2S")
        )
    return steps


def build_steps_middle(value, start_data, taxes_2026_plus=False):
    # type: (str, dict, bool) -> list
    """Passos de colar VALUE + restante até PROC TIME."""
    paste_pts = _VALUE_PASTE_2026 if taxes_2026_plus else _VALUE_PASTE_LEGACY
    steps = [
        Step(
            "click_and_type",
            x=paste_pts[0][0],
            y=paste_pts[0][1],
            text=value,
            label="6 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_type",
            x=paste_pts[1][0],
            y=paste_pts[1][1],
            text=value,
            label="7 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_type",
            x=paste_pts[2][0],
            y=paste_pts[2][1],
            text=value,
            label="8 — Clique e escrever VALUE",
        ),
        Step(
            "click_and_type",
            x=paste_pts[3][0],
            y=paste_pts[3][1],
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
    ]
    steps.extend(
        [
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
    )
    return steps


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
    docmap.enable_from_argv()
    localmap.enable_from_argv()
    docmap.begin_part("parte4")
    localmap.begin_part("parte4")
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

    taxes_2026_plus = bool(prefill.get("taxes_2026_plus"))

    print("Parte 4 — dados:")
    for key, val in start_data.items():
        print("  {}: {!r}".format(key, val))
    print("  random_no: {!r}".format(random_no))
    print("  digit: {!r}".format(digit))
    print(
        "  taxes_2026_plus: {} ({})".format(
            taxes_2026_plus,
            "CBS1+IB2S (Enter x2/taxa)" if taxes_2026_plus else "4 impostos (Enter x2/taxa)",
        )
    )

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

        run_steps(
            build_steps_before_value(taxes_2026_plus=taxes_2026_plus),
            dry_run=dry_run,
        )

        value = capture_value_from_screen(dry_run=dry_run)

        run_steps(
            build_steps_middle(
                value, start_data, taxes_2026_plus=taxes_2026_plus
            ),
            dry_run=dry_run,
        )
        run_steps(build_steps_random_digit(random_no, digit), dry_run=dry_run)

        # Total Value: print B + comparação A ↔ B ↔ planilha
        value_a = normalize_money(prefill.get("total_value_a")) if prefill else None
        value_sheet = normalize_money(prefill.get("total_value_sheet")) if prefill else None
        run_dir = prefill.get("total_value_run_dir") if prefill else None
        run_path = Path(run_dir) if run_dir else None
        print_b = capture_print_b(run_dir=run_path, dry_run=dry_run)
        print(
            "TOTAL VALUE B: {} (método {}, png={!r})".format(
                print_b["value"], print_b["method"], print_b["path"]
            )
        )
        if value_sheet is not None:
            print("TOTAL VALUE planilha: {}".format(value_sheet))
        if value_a is not None:
            cmp = compare_total_values(
                value_a, print_b["value"], value_sheet=value_sheet
            )
            if not cmp["ok"]:
                raise RuntimeError(
                    "Total Value não confere: {}".format(cmp["detail"])
                )
            print("Total Value (telas" + (" + planilha" if value_sheet is not None else "") + "): OK")
        else:
            print(
                "Aviso: sem total_value_a no prefill — print B capturado, "
                "comparação adiada."
            )

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
            docmap.finish()
            localmap.finish()
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
