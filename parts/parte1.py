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

from automation import abort, docmap, localmap, win_mouse
from automation.forms import ask_fields
from automation.runner import Step, run_steps
from automation.ui import countdown
from automation.utils import clean_value
import config

win_mouse.ensure_dpi_awareness()


def build_steps(batch):
    # type: (str) -> list
    return [
        Step(
            "double_click",
            x=-1150,
            y=530,
            wait_after=config.WAIT_AFTER_OPEN_SAP,
            label="1 — Duplo clique (abrir/focar)",
        ),
        Step(
            "click_and_type",
            x=-1827,
            y=58,
            text="/n/lkmt/ardfe",
            wiggle_x=20,
            label="2 — Clique e escrever /n/lkmt/ardfe",
        ),
        Step(
            "click",
            x=-1895,
            y=53,
            seconds=config.WAIT_AFTER_EXECUTE,
            label="4 — Clique e esperar (executar)",
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
            "click_and_type",
            x=-1629,
            y=373,
            text="01.02.2025",
            delete_times=11,
            label="8b — Clique, Delete x11, escrever 01.02.2025",
        ),
        Step(
            "click",
            x=-1506,
            y=766,
            label="8c — Clique",
        ),
        Step(
            "click",
            x=-1627,
            y=787,
            label="8d — Clique",
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
            wait_after=2.0,
            label="10 — Clique e esperar 2s",
        ),
    ]


def main(dry_run=False, show_done=True, batch=None, chained=False, skip_countdown=False):
    # type: (bool, bool, object, bool, bool) -> bool
    """
    batch: se informado (fluxo da planilha), não pede Batch no formulário.
    chained: não gerencia abort/docmap finish (quem chama é o main).
    """
    docmap.enable_from_argv()
    localmap.enable_from_argv()
    docmap.begin_part("parte1")
    localmap.begin_part("parte1")

    if batch is not None:
        batch = clean_value(str(batch))
        if not batch:
            messagebox.showerror("Batch inválido", "Batch vazio na planilha.")
            return False
        # Tempo de espera já deve ter sido aplicado pelo orquestrador
        print("Batch (planilha): {}".format(batch))
    else:
        data = ask_fields(
            title="Parte 1 — Automação SAP",
            fields=[
                ("batch", "Batch number"),
                ("tempo_espera", "Tempo de espera (segundos)"),
            ],
            start_label="Iniciar Parte 1",
            defaults={"tempo_espera": "3"},
        )
        if data is None:
            print("Cancelado pelo usuário.")
            return False

        batch = data["batch"]
        try:
            config.apply_user_wait(config.parse_wait(data["tempo_espera"]))
        except ValueError:
            messagebox.showerror(
                "Tempo inválido",
                "Informe um número válido para o tempo de espera (ex.: 3 ou 1,5).",
            )
            return False
        print("Batch informado: {}".format(batch))

    steps = build_steps(batch)

    if not chained:
        abort.start_listener()
    try:
        if not dry_run and not skip_countdown:
            if chained:
                countdown(
                    config.COUNTDOWN_BETWEEN_PARTS,
                    "Próximo batch.\nIniciando Parte 1 em...",
                )
            else:
                countdown(
                    config.COUNTDOWN_START,
                    "Foque a tela do SAP!\nIniciando em...",
                )
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
        if show_done or not chained:
            docmap.finish()
            localmap.finish()
            abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
