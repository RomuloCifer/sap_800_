"""
Documentação dos passos com clique (modo --documentar).

Antes de cada ação de mouse, pergunta nome + observação e grava em
mapa_passos.json, separado por parte (parte1, parte2, …).

Se der erro no meio, as partes já documentadas ficam salvas. Para refazer
só uma parte: rode de novo com --documentar (no main ou na parte isolada);
só a parte atual é sobrescrita.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from automation.forms import ask_fields

ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = ROOT / "mapa_passos.json"

MOUSE_KINDS = frozenset({"click", "double_click", "click_and_type", "click_and_press"})

_enabled = False
_part = None  # type: Optional[str]
_entries = []  # type: List[dict]
_seq = 0
_all_parts = {}  # type: Dict[str, dict]


def is_enabled():
    # type: () -> bool
    return _enabled


def enable_from_argv(argv=None):
    # type: (Optional[list]) -> bool
    """Liga o modo se --documentar estiver nos args. Retorna True se ativo."""
    global _enabled, _entries, _seq, _part, _all_parts
    args = list(argv if argv is not None else sys.argv[1:])
    if "--documentar" not in args:
        return False
    _enabled = True
    _entries = []
    _seq = 0
    _part = None
    _all_parts = _load()
    print("Modo DOCUMENTAR: nome/obs antes de cada clique (salvo por parte).")
    print("Arquivo: {}".format(MAP_FILE))
    ja = sorted(_all_parts.keys())
    if ja:
        print(
            "Partes já no arquivo: {} (só a parte atual será sobrescrita).".format(
                ", ".join(ja)
            )
        )
    return True


def begin_part(name):
    # type: (str) -> None
    """
    Inicia (ou reinicia) a documentação de uma parte.
    Apaga só essa parte no mapa; as outras permanecem.
    """
    global _part, _entries, _seq, _all_parts
    if not _enabled:
        return
    _all_parts = _load()
    _part = name
    _entries = []
    _seq = 0
    _all_parts[name] = {"passos": []}
    _save()
    print("\n--- Documentando: {} (passos anteriores desta parte limpos) ---\n".format(name))


def maybe_ask_step(kind, label, x=None, y=None, x2=None, y2=None, extra=None):
    # type: (str, str, Optional[int], Optional[int], Optional[int], Optional[int], Optional[dict]) -> None
    """
    Se o modo estiver ativo e for ação com mouse, posiciona o cursor no
    ponto do clique, abre o formulário (campos vazios) e grava a entrada.
    """
    global _seq
    if not _enabled:
        return
    if kind not in MOUSE_KINDS and kind != "drag_copy":
        return
    if _part is None:
        begin_part("geral")

    from automation import win_mouse

    _seq += 1
    hint = label or kind
    print("  [{} #{}] (label código: {})".format(_part, _seq, hint))

    if x is not None and y is not None:
        win_mouse.move_to(int(x), int(y))

    form = ask_fields(
        title="{} — passo {} ({})".format(_part, _seq, kind),
        fields=[
            ("nome", "Nome do campo / clique"),
            ("obs", "Observação (opcional)"),
        ],
        start_label="Continuar",
        optional=["obs"],
    )
    if form is None:
        raise RuntimeError(
            "Documentação cancelada em {} passo {}.".format(_part, _seq)
        )

    nome = (form.get("nome") or "").strip()
    obs = (form.get("obs") or "").strip()

    entry = {
        "ordem": _seq,
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
    if extra:
        entry.update(extra)

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
