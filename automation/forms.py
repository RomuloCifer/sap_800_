"""Formulários visuais para coletar dados antes de cada parte."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import messagebox

Validator = Callable[[str], Optional[str]]  # retorna mensagem de erro ou None


def validate_random_no(value):
    # type: (str) -> Optional[str]
    """RANDOM NO: exatamente 8 dígitos numéricos."""
    cleaned = (value or "").strip()
    if not cleaned.isdigit():
        return "RANDOM NO deve conter apenas dígitos (0-9)."
    if len(cleaned) != 8:
        return "RANDOM NO deve ter exatamente 8 dígitos (você digitou {}).".format(
            len(cleaned)
        )
    return None


def ask_fields(
    title,
    fields,
    start_label="Iniciar",
    defaults=None,
    validators=None,
):
    # type: (str, List[Tuple[str, str]], str, Optional[Dict[str, str]], Optional[Dict[str, Validator]]) -> Optional[Dict[str, str]]
    """
    Abre um formulário simples.

    fields: lista de (chave, rótulo), ex.: [("batch", "Batch number")]
    defaults: valores iniciais opcionais por chave
    validators: opcional, chave → função(valor) → mensagem de erro ou None
    Retorna dict com os valores, ou None se cancelar.
    """
    result = {}  # type: Dict[str, str]
    cancelled = {"value": True}
    defaults = defaults or {}
    validators = validators or {}

    root = tk.Tk()
    root.title(title)
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#f4f4f4", padx=16, pady=16)

    tk.Label(
        root,
        text=title,
        font=("Segoe UI", 12, "bold"),
        bg="#f4f4f4",
        fg="#222",
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

    entries = {}  # type: Dict[str, tk.Entry]
    for row, (key, label) in enumerate(fields, start=1):
        tk.Label(
            root,
            text=label,
            font=("Segoe UI", 10),
            bg="#f4f4f4",
        ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
        entry = tk.Entry(root, font=("Consolas", 11), width=28)
        entry.grid(row=row, column=1, sticky="ew", pady=4)
        if key in defaults and defaults[key]:
            entry.insert(0, defaults[key])
        entries[key] = entry

    if fields:
        entries[fields[0][0]].focus_set()

    def _submit(_event=None):
        values = {}
        for key, _label in fields:
            value = entries[key].get().strip()
            if not value:
                messagebox.showwarning(
                    "Campo obrigatório",
                    "Preencha: {}".format(_label),
                    parent=root,
                )
                entries[key].focus_set()
                return
            if key in validators:
                error = validators[key](value)
                if error:
                    messagebox.showwarning(
                        "Valor inválido",
                        error,
                        parent=root,
                    )
                    entries[key].focus_set()
                    return
            values[key] = value
        result.clear()
        result.update(values)
        cancelled["value"] = False
        root.destroy()

    def _cancel():
        cancelled["value"] = True
        root.destroy()

    btn_row = len(fields) + 1
    btn_frame = tk.Frame(root, bg="#f4f4f4")
    btn_frame.grid(row=btn_row, column=0, columnspan=2, pady=(14, 0), sticky="e")

    tk.Button(
        btn_frame,
        text="Cancelar",
        font=("Segoe UI", 9),
        command=_cancel,
        width=10,
    ).pack(side=tk.RIGHT, padx=(8, 0))
    tk.Button(
        btn_frame,
        text=start_label,
        font=("Segoe UI", 9, "bold"),
        command=_submit,
        width=12,
    ).pack(side=tk.RIGHT)

    root.bind("<Return>", _submit)
    root.bind("<Escape>", lambda e: _cancel())

    # Centraliza na tela
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("+{}+{}".format((sw - w) // 2, (sh - h) // 3))

    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()

    if cancelled["value"]:
        return None
    return dict(result)
