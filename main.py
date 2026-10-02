"""
Fluxo completo: Parte 1 → 2 → 3 → 4 (encadeadas).

Lê Batch e Total Value de entrada/lancamentos.xlsx.
Total Value da planilha é comparado com os prints A e B (OCR).

Uso:
  python main.py              # partes 1 a 4 (planilha)
  python main.py --ate-2      # só partes 1 e 2
  python main.py --dry-run
  python main.py --planilha caminho\\arquivo.xlsx
  python main.py --documentar
  python main.py --mapear
  python main.py --mapear-resto

Emergência: F10 para a automação a qualquer momento.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinter import messagebox

from automation import abort, docmap, localmap, win_mouse
from automation.capture import drag_copy
from automation.forms import ask_fields
from automation.lancamentos import load_lancamentos, resolve_planilha_from_argv
from automation.part34_capture import capture_part34_fields
from automation.ui import countdown
from automation.utils import clean_value
from parts import parte1, parte2, parte3, parte4
import config

win_mouse.ensure_dpi_awareness()

ISSUER_SELECT_FROM = (-949, 222)
ISSUER_SELECT_TO = (-870, 222)

INVOICE_SELECT_FROM = (-1759, 176)
INVOICE_SELECT_TO = (-1703, 176)

INVOICE_SERIES_FROM = (-1694, 179)
INVOICE_SERIES_TO = (-1669, 179)

ISSUE_DATE_SELECT_FROM = (-950, 176)
ISSUE_DATE_SELECT_TO = (-871, 178)


def _wait(seconds):
    # type: (float) -> None
    abort.sleep(seconds)


def run_one_batch(
    batch,
    total_value_sheet=None,
    dry_run=False,
    stop_after=None,
    skip_countdown=False,
):
    # type: (str, object, bool, object, bool) -> bool
    """
    Executa o fluxo completo para um Batch.
    total_value_sheet: Decimal da planilha para comparar no fim (A ↔ B ↔ planilha).
    """
    ok = parte1.main(
        dry_run=dry_run,
        show_done=False,
        batch=batch,
        chained=True,
        skip_countdown=skip_countdown,
    )
    if not ok:
        print("Fluxo interrompido na Parte 1 (batch {}).".format(batch))
        return False

    if abort.is_aborted():
        return False

    print(
        "\nAguardando {:.0f}s após Parte 1 (carregar tela)...".format(
            config.WAIT_AFTER_PART1
        )
    )
    if not dry_run:
        _wait(config.WAIT_AFTER_PART1)

    docmap.begin_part("apos_parte1")
    localmap.begin_part("apos_parte1")
    issuer = drag_copy(
        ISSUER_SELECT_FROM[0],
        ISSUER_SELECT_FROM[1],
        ISSUER_SELECT_TO[0],
        ISSUER_SELECT_TO[1],
        label="ISSUER SAP",
        dry_run=dry_run,
    )

    doc_data = None
    part4_data = None
    if stop_after != 2:
        invoice = drag_copy(
            INVOICE_SELECT_FROM[0],
            INVOICE_SELECT_FROM[1],
            INVOICE_SELECT_TO[0],
            INVOICE_SELECT_TO[1],
            label="INVOICE",
            dry_run=dry_run,
        )
        invoice_series = drag_copy(
            INVOICE_SERIES_FROM[0],
            INVOICE_SERIES_FROM[1],
            INVOICE_SERIES_TO[0],
            INVOICE_SERIES_TO[1],
            label="INVOICE SERIES",
            dry_run=dry_run,
        )
        issue_date = drag_copy(
            ISSUE_DATE_SELECT_FROM[0],
            ISSUE_DATE_SELECT_FROM[1],
            ISSUE_DATE_SELECT_TO[0],
            ISSUE_DATE_SELECT_TO[1],
            label="ISSUE_DATE",
            dry_run=dry_run,
        )

        docmap.begin_part("dados_parte34")
        localmap.begin_part("dados_parte34")
        screen_doc, screen_p4 = capture_part34_fields(dry_run=dry_run)

        doc_data = {
            "invoice": clean_value(invoice),
            "invoice_series": clean_value(invoice_series),
            "issue_date": clean_value(issue_date),
            "material": screen_doc["material"],
            "quantidade": screen_doc["quantidade"],
            "price": screen_doc["price"],
            "description": screen_doc["description"],
            "cfop": screen_doc["cfop"],
        }
        part4_data = dict(screen_p4)
        if total_value_sheet is not None:
            part4_data["total_value_sheet"] = str(total_value_sheet)

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
        print("Fluxo interrompido na Parte 2 (batch {}).".format(batch))
        return False

    if stop_after == 2:
        print("\nFluxo Parte 1+2 finalizado (batch {}).".format(batch))
        return True

    if abort.is_aborted():
        return False

    print("\n--- Seguindo para a Parte 3 ---\n")
    ok3 = parte3.main(
        dry_run=dry_run,
        chained=True,
        show_done=False,
        prefill=doc_data,
    )
    if not ok3:
        print("Fluxo interrompido na Parte 3 (batch {}).".format(batch))
        return False

    if abort.is_aborted():
        return False

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
        print("Fluxo interrompido na Parte 4 (batch {}).".format(batch))
        return False

    print("\nBatch {} finalizado com sucesso.".format(batch))
    return True


def main(dry_run=False, stop_after=None, planilha=None):
    # type: (bool, object, object) -> None
    docmap.enable_from_argv()
    localmap.enable_from_argv()

    try:
        path = Path(planilha) if planilha else resolve_planilha_from_argv(sys.argv[1:])
        rows = load_lancamentos(path)
    except Exception as exc:
        messagebox.showerror("Planilha", str(exc))
        print("ERRO planilha:", exc)
        return

    wait_form = ask_fields(
        title="Automação SAP — planilha",
        fields=[("tempo_espera", "Tempo de espera (segundos)")],
        start_label="Iniciar ({} lançamento(s))".format(len(rows)),
        defaults={"tempo_espera": "3"},
    )
    if wait_form is None:
        print("Cancelado pelo usuário.")
        return
    try:
        config.apply_user_wait(config.parse_wait(wait_form["tempo_espera"]))
    except ValueError:
        messagebox.showerror(
            "Tempo inválido",
            "Informe um número válido para o tempo de espera (ex.: 3 ou 1,5).",
        )
        return

    abort.start_listener()
    ok_count = 0
    fail_count = 0
    try:
        if not dry_run:
            countdown(
                config.COUNTDOWN_START,
                "Planilha: {} batch(es).\nFoque o SAP!\nIniciando em...".format(
                    len(rows)
                ),
            )

        for i, item in enumerate(rows):
            if abort.is_aborted():
                break
            batch = item["batch"]
            total = item["total_value"]
            print(
                "\n========== Lançamento {}/{}  batch={}  total_value={} ==========\n".format(
                    i + 1, len(rows), batch, total
                )
            )

            try:
                ok = run_one_batch(
                    batch,
                    total_value_sheet=total,
                    dry_run=dry_run,
                    stop_after=stop_after,
                    skip_countdown=(i == 0),
                )
            except abort.AbortedError:
                raise
            except Exception as exc:
                print("ERRO no batch {}: {}".format(batch, exc))
                fail_count += 1
                continue

            if ok:
                ok_count += 1
            else:
                fail_count += 1
                if abort.is_aborted():
                    break

        if stop_after == 2 and not dry_run and fail_count == 0:
            messagebox.showinfo("Automação SAP", "Partes 1 e 2 concluídas.")
        elif not dry_run:
            messagebox.showinfo(
                "Automação SAP",
                "Finalizado.\nOK: {}\nFalhas: {}\nTotal: {}".format(
                    ok_count, fail_count, len(rows)
                ),
            )
        print(
            "\nResumo: ok={} falha={} total={}".format(
                ok_count, fail_count, len(rows)
            )
        )
    except abort.AbortedError:
        messagebox.showwarning(
            "Abortado",
            "Automação interrompida ({}).".format(abort.ABORT_KEY_NAME),
        )
        print("Fluxo abortado com {}.".format(abort.ABORT_KEY_NAME))
    finally:
        docmap.finish()
        localmap.finish()
        abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    ate2 = "--ate-2" in sys.argv
    main(dry_run=dry, stop_after=2 if ate2 else None)
