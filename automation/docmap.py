"""
Documentação dos passos com clique (modo --documentar).

Antes de cada ação de mouse sem legenda, pergunta nome + observação e grava
em mapa_passos.json, separado por parte (parte1, parte2, …).

  python main.py --documentar       # só o que ainda não tem nome
  python main.py --documentar-tudo  # zera a parte atual e documenta do zero

Se der erro no meio, o que já estava salvo permanece.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from automation.forms import ask_fields

ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = ROOT / "mapa_passos.json"

MOUSE_KINDS = frozenset({"click", "double_click", "click_and_type", "click_and_press"})

_enabled = False
_keep_existing = True
_part = None  # type: Optional[str]
_entries = []  # type: List[dict]
_seq = 0
_all_parts = {}  # type: Dict[str, dict]


def is_enabled():
    # type: () -> bool
    return _enabled


def enable_from_argv(argv=None):
    # type: (Optional[list]) -> bool
    """Liga o modo se --documentar / --documentar-tudo estiver nos args."""
    global _enabled, _keep_existing, _entries, _seq, _part, _all_parts
    args = list(argv if argv is not None else sys.argv[1:])
    if "--documentar" not in args and "--documentar-tudo" not in args:
        return False
    _enabled = True
    _keep_existing = "--documentar-tudo" not in args
    _entries = []
    _seq = 0
    _part = None
    _all_parts = _load()
    print("Modo DOCUMENTAR: nome/obs nos cliques ainda sem legenda.")
    print("Arquivo: {}".format(MAP_FILE))
    if _keep_existing:
        print("(mantém o já documentado; use --documentar-tudo para refazer do zero)")
    else:
        print("(--documentar-tudo: apaga a parte atual e documenta de novo)")
    ja = sorted(_all_parts.keys())
    if ja:
        print("Partes já no arquivo: {}.".format(", ".join(ja)))
    return True


def begin_part(name):
    # type: (str) -> None
    """
    Inicia a documentação de uma parte.
    Com --documentar: mantém passos já salvos.
    Com --documentar-tudo: limpa só essa parte.
    """
    global _part, _entries, _seq, _all_parts
    if not _enabled:
        return
    _all_parts = _load()
    _part = name
    _seq = 0

    if _keep_existing:
        _entries = list(((_all_parts.get(name) or {}).get("passos") or []))
        print(
            "\n--- Documentando: {} ({} já no catálogo; só pede o que faltar) ---\n".format(
                name, len(_entries)
            )
        )
    else:
        _entries = []
        _all_parts[name] = {"passos": []}
        _save()
        print(
            "\n--- Documentando: {} do zero (passos anteriores desta parte limpos) ---\n".format(
                name
            )
        )


def _coords_match(step, x, y, x2, y2):
    # type: (dict, Optional[int], Optional[int], Optional[int], Optional[int]) -> bool
    if x is not None:
        if step.get("x") is None or int(step["x"]) != int(x):
            return False
    if y is not None:
        if step.get("y") is None or int(step["y"]) != int(y):
            return False
    if x2 is not None:
        if step.get("x2") is None or int(step["x2"]) != int(x2):
            return False
    if y2 is not None:
        if step.get("y2") is None or int(step["y2"]) != int(y2):
            return False
    return True


def _find_entry(kind, label, x, y, x2, y2):
    # type: (str, str, Optional[int], Optional[int], Optional[int], Optional[int]) -> Tuple[Optional[int], Optional[dict]]
    hint = label or kind
    for i, step in enumerate(_entries):
        if (step.get("kind") or "") != kind:
            continue
        if (step.get("label_codigo") or "") != hint:
            continue
        if not _coords_match(step, x, y, x2, y2):
            continue
        return i, step
    return None, None


def maybe_ask_step(kind, label, x=None, y=None, x2=None, y2=None, extra=None):
    # type: (str, str, Optional[int], Optional[int], Optional[int], Optional[int], Optional[dict]) -> None
    """
    Se o modo estiver ativo e for ação com mouse: se já tem nome no catálogo,
    pula; senão pergunta e grava.
    """
    global _seq
    if not _enabled:
        return
    if kind not in MOUSE_KINDS and kind != "drag_copy":
        return
    if _part is None:
        begin_part("geral")

    from automation import win_mouse

    hint = label or kind
    idx, existing = _find_entry(kind, hint, x, y, x2, y2)
    if (
        _keep_existing
        and existing is not None
        and (existing.get("nome") or "").strip()
    ):
        print(
            "  [{}] já documentado: {!r}".format(
                _part, (existing.get("nome") or "").strip()
            )
        )
        return

    _seq += 1
    ordem = _seq if not _entries else max(
        int(e.get("ordem") or 0) for e in _entries
    ) + 1
    print("  [{} #{}] (label código: {})".format(_part, ordem, hint))

    if x is not None and y is not None:
        win_mouse.move_to(int(x), int(y))

    form = ask_fields(
        title="{} — passo {} ({})".format(_part, ordem, kind),
        fields=[
            ("nome", "Nome do campo / clique"),
            ("obs", "Observação (opcional)"),
        ],
        start_label="Continuar",
        optional=["obs"],
        defaults={
            "nome": (existing.get("nome") or "") if existing else "",
            "obs": (existing.get("obs") or "") if existing else "",
        },
    )
    if form is None:
        raise RuntimeError(
            "Documentação cancelada em {} passo {}.".format(_part, ordem)
        )

    nome = (form.get("nome") or "").strip()
    obs = (form.get("obs") or "").strip()

    entry = {
        "ordem": int(existing["ordem"]) if existing and existing.get("ordem") else ordem,
        "kind": kind,
        "label_codigo": hint,
        "nome": nome,
        "obs": obs,
    }
    if x is not None and y is not None:
        entry["x"] = int(x)
        entry["y"] = int(y)
    if x2 is not None and y2 is not None:
        entry["x2"] = int(x2)
        entry["y2"] = int(y2)
    if existing:
        for key in ("text", "keys"):
            if key in existing and key not in entry:
                entry[key] = existing[key]
    if extra:
        entry.update(extra)

    if idx is not None:
        _entries[idx] = entry
    else:
        _entries.append(entry)
    _all_parts[_part] = {"passos": list(_entries)}
    _save()
    print("  documentado: {!r}".format(nome))


def _load():
    # type: () -> Dict[str, dict]
    if not MAP_FILE.exists():
        return {}
    try:
        data = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    # Formato antigo (lista plana) → migra para parte1
    if isinstance(data, dict) and "passos" in data and "partes" not in data:
        return {"parte1": {"passos": list(data.get("passos") or [])}}
    partes = data.get("partes") if isinstance(data, dict) else None
    if isinstance(partes, dict):
        return dict(partes)
    return {}


def _save():
    # type: () -> None
    payload = {
        "versao": 2,
        "descricao": (
            "Catálogo de cliques por parte. "
            "xy é da máquina de referência; mapeamento por outra tela vem depois."
        ),
        "partes": _all_parts,
    }
    MAP_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def finish():
    # type: () -> None
    if not _enabled:
        return
    _save()
    print("\nDocumentação em {}:".format(MAP_FILE))
    for name in sorted(_all_parts.keys()):
        n = len((_all_parts[name] or {}).get("passos") or [])
        print("  {}: {} passo(s)".format(name, n))
