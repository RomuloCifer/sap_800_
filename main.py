"""
Fluxo completo: Parte 1 → Parte 2 → Parte 3 (encadeadas).

Uso:
  python main.py
  python main.py --dry-run

Emergência: F10 para a automação a qualquer momento.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinter import messagebox

from automation import abort, win_mouse
from parts import parte1, parte2, parte3

win_mouse.ensure_dpi_awareness()


def main(dry_run=False):
    # type: (bool) -> None
    abort.start_listener()
    try:
        ok = parte1.main(dry_run=dry_run, show_done=False)
        if not ok:
            print("Fluxo interrompido na Parte 1.")
            return

        if abort.is_aborted():
            return

        print("\n--- Seguindo para a Parte 2 ---\n")
        ok2 = parte2.main(dry_run=dry_run, chained=True, show_done=False)
        if not ok2:
            print("Fluxo interrompido na Parte 2.")
            return

        if abort.is_aborted():
            return

        print("\n--- Seguindo para a Parte 3 ---\n")
        ok3 = parte3.main(dry_run=dry_run, chained=True, show_done=False)
        if not ok3:
            print("Fluxo interrompido na Parte 3.")
            return

        if not dry_run:
            messagebox.showinfo(
                "Automação SAP",
                "Partes 1, 2 e 3 (trecho atual) concluídas.",
            )
        print("\nFluxo completo finalizado.")
    finally:
        abort.stop_listener()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
