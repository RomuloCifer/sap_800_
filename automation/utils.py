"""Utilitários compartilhados entre as partes da automação."""

from __future__ import annotations

from automation.runner import Step


def clean_value(value):
    # type: (str) -> str
    return (value or "").replace("\xa0", " ").strip()


def build_tax_steps(label, x_type, y_type, code, x_pick, y_pick, wait_after=1.2, char_interval=0.2):
    # type: (str, int, int, str, int, int, float, float) -> list
    """Retorna dois Steps: digitar código letra a letra e clicar na opção."""
    return [
        Step(
            "click_and_type",
            x=x_type,
            y=y_type,
            text=code,
            type_slowly=True,
            char_interval=char_interval,
            wait_after=wait_after,
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
