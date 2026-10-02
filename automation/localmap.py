"""
Mapeamento local de cliques (modo --mapear).

Usa mapa_passos.json (nomes/obs documentados) como guia. A automação
roda normalmente; só pede F12 nos pontos ainda sem coordenada local.
F11 desfaz o último ponto e permite remapear.

Sem pontos_local.json e sem --mapear → coordenadas do código (referência).
Com o arquivo (uso normal) → cliques usam o XY local.

  python main.py --mapear         # roda o fluxo; pede só o que faltar
  python main.py --mapear-resto   # alias de --mapear (compatibilidade)
  python main.py --mapear-tudo    # apaga a parte atual e remapeia do zero
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from pynput import keyboard

from automation import abort
from automation import docmap as catalog
from automation.ui import place_window_left_screen

ROOT = Path(__file__).resolve().parent.parent
LOCAL_FILE = ROOT / "pontos_local.json"

MOUSE_KINDS = catalog.MOUSE_KINDS

_enabled = False
_keep_existing = False
_part = None  # type: Optional[str]
_part_pontos = {}  # type: Dict[str, dict]  # key -> {x,y,nome,...}
_all_parts = {}  # type: Dict[str, dict]
_flat = {}  # type: Dict[str, dict]  # key -> ponto (todas as partes)
_seq = 0
_catalog_passos = []  # type: List[dict]
_history = []  # type: List[dict]  # ordem de captura nesta parte
_announced = False


def point_key(x, y, label):
    # type: (int, int, str) -> str
    return "{},{}|{}".format(int(x), int(y), label or "")


def is_enabled():
    # type: () -> bool
    return _enabled


def enable_from_argv(argv=None):
    # type: (Optional[list]) -> bool
    global _enabled, _keep_existing, _part, _part_pontos, _all_parts, _flat, _seq
    global _catalog_passos, _history, _announced
    args = list(argv if argv is not None else sys.argv[1:])
    map_flags = ("--mapear", "--mapear-resto", "--mapear-tudo")
    if not any(f in args for f in map_flags):
        # Modo normal: só carrega mapa local se existir (para resolve)
        _enabled = False
        _all_parts = _load()
        _rebuild_flat()
        if _flat and not _announced:
            _announced = True
            print(
                "Usando pontos locais desta máquina ({} — {} ponto(s)).".format(
                    LOCAL_FILE.name, len(_flat)
                )
            )
        return False

    if "--documentar" in args:
        print("Aviso: --documentar e --mapear juntos; usando só --mapear.")

    _enabled = True
    # Padrão: mantém o que já existe e só pede o que faltar.
    # --mapear-tudo: zera a parte atual e remapeia tudo.
    _keep_existing = "--mapear-tudo" not in args
    _part = None
    _part_pontos = {}
    _history = []
    _seq = 0
    _catalog_passos = []
    _all_parts = _load()
    _rebuild_flat()
    print("Modo MAPEAR: a automação roda normalmente.")
    print("  Só pede marcações nos pontos ainda sem coordenada nesta máquina.")
    print("  F12 = gravar    F11 = voltar    F10 = parar")
    print("Guia: {}".format(catalog.MAP_FILE.name))
    print("Arquivo local: {}".format(LOCAL_FILE))
    if _keep_existing:
        print("(mantém pontos já gravados; use --mapear-tudo para refazer do zero)")
    else:
        print("(--mapear-tudo: apaga os pontos da parte atual e remapeia)")
    return True


def begin_part(name):
    # type: (str) -> None
    global _part, _part_pontos, _seq, _all_parts, _catalog_passos, _history
    if not _enabled:
        return

    _all_parts = _load()
    _part = name
    _seq = 0

    cat = catalog._load()
    _catalog_passos = list((cat.get(name) or {}).get("passos") or [])

    if _keep_existing:
        _part_pontos = dict(((_all_parts.get(name) or {}).get("pontos") or {}))
        _history = _history_from_pontos(_part_pontos)
        print(
            "\n--- Mapeando: {} ({} já gravado(s), {} no catálogo) ---\n".format(
                name, len(_part_pontos), len(_catalog_passos)
            )
        )
    else:
        _part_pontos = {}
        _history = []
        _all_parts[name] = {"pontos": {}}
        _save()
        _rebuild_flat()
        print(
            "\n--- Mapeando: {} do zero ({} passos no catálogo) ---\n".format(
                name, len(_catalog_passos)
            )
        )
        if not _catalog_passos:
            print(
                "Aviso: não há passos documentados para '{}'. "
                "Rode --documentar nessa parte antes.".format(name)
            )


def _history_from_pontos(pontos):
    # type: (Dict[str, dict]) -> List[dict]
    items = sorted(
        (pontos or {}).items(),
        key=lambda kv: int((kv[1] or {}).get("ordem") or 0),
    )
    out = []
    for key, p in items:
        p = p or {}
        out.append(
            {
                "key": key,
                "ref_x": int(p.get("ref_x") or 0),
                "ref_y": int(p.get("ref_y") or 0),
                "label": p.get("label_codigo") or "",
                "kind": p.get("kind") or "click",
                "nome": p.get("nome") or "",
            }
        )
    return out


def resolve(x, y, label, kind="click"):
    # type: (int, int, str, str) -> Tuple[int, int]
    """Devolve (x,y) a usar nesta máquina para o ponto de referência."""
    if x is None or y is None:
        return x, y  # type: ignore[return-value]

    key = point_key(x, y, label)

    if _enabled:
        if _keep_existing and key in _part_pontos:
            p = _part_pontos[key]
            print("  [já mapeado] {} → ({}, {})".format(p.get("nome") or label, p["x"], p["y"]))
            return int(p["x"]), int(p["y"])
        return _capture(key, int(x), int(y), label, kind)

    hit = _flat.get(key)
    if hit is not None:
        return int(hit["x"]), int(hit["y"])
    return int(x), int(y)


def _find_catalog(label, ref_x, ref_y):
    # type: (str, int, int) -> Optional[dict]
    # Coordenadas primeiro (importante em drag_copy início/fim)
    for step in _catalog_passos:
        if step.get("kind") == "drag_copy":
            if (
                step.get("x2") is not None
                and int(step["x2"]) == ref_x
                and int(step["y2"]) == ref_y
            ):
                return dict(step, _drag_end=True)
            if (
                step.get("x") is not None
                and int(step["x"]) == ref_x
                and int(step["y"]) == ref_y
            ):
                return step
    for step in _catalog_passos:
        if (step.get("label_codigo") or "") == label:
            return step
    for step in _catalog_passos:
        if (
            step.get("x") is not None
            and int(step["x"]) == ref_x
            and int(step["y"]) == ref_y
        ):
            return step
    return None


def resolve_drag(x1, y1, x2, y2, label):
    # type: (int, int, int, int, str) -> Tuple[int, int, int, int]
    """Mapeia início e fim de uma seleção (drag_copy)."""
    ax, ay = resolve(x1, y1, label, kind="drag_copy")
    bx, by = resolve(x2, y2, label, kind="drag_copy")
    return ax, ay, bx, by


def _drag_point_hint(step, is_end):
    # type: (dict, bool) -> str
    """
    Regra: se o X vai para << (mais negativo), 1o=final >> e 2o=inicio <<.
    Se o X vai para >> (maior), 1o=inicio << e 2o=final >>.
    """
    try:
        x = int(step["x"])
        x2 = int(step["x2"])
    except Exception:
        return "fim da seleção" if is_end else ""
    if x2 < x:
        return "inicio do numero <<" if is_end else "final do numero >>"
    if x2 > x:
        return "final do numero >>" if is_end else "inicio do numero <<"
    return "fim da seleção" if is_end else ""


def _capture(key, ref_x, ref_y, label, kind):
    # type: (str, int, int, str, str) -> Tuple[int, int]
    global _seq
    if _part is None:
        begin_part("geral")

    while True:
        info = _find_catalog(label, ref_x, ref_y) or {}
        nome = (info.get("nome") or label or kind).strip()
        obs = (info.get("obs") or "").strip()
        if info.get("kind") == "drag_copy" or kind == "drag_copy":
            hint = _drag_point_hint(info, is_end=bool(info.get("_drag_end")))
            if hint:
                nome = "{} — {}".format(nome, hint)

        seq = len(_history) + 1
        print("  [{} #{}] mapeie: {}".format(_part, seq, nome))
        if obs:
            print("           obs: {}".format(obs))

        action = _ask_position(nome, obs, kind, seq)
        if action[0] == "undo":
            if not _history:
                print("  (nada para voltar)")
                continue
            prev = _history.pop()
            _part_pontos.pop(prev["key"], None)
            _all_parts[_part] = {"pontos": dict(_part_pontos)}
            _save()
            _rebuild_flat()
            print(
                "  voltou: desfez {!r}".format(prev.get("nome") or prev.get("label"))
            )
            # Remapeia o anterior (atualiza o JSON; o clique no SAP já ocorreu)
            _capture(
                prev["key"],
                int(prev["ref_x"]),
                int(prev["ref_y"]),
                prev["label"],
                prev["kind"],
            )
            continue

        lx, ly = int(action[1]), int(action[2])
        entry = {
            "ordem": seq,
            "kind": kind,
            "label_codigo": label,
            "nome": nome,
            "obs": obs,
            "ref_x": ref_x,
            "ref_y": ref_y,
            "x": lx,
            "y": ly,
        }
        _part_pontos[key] = entry
        _history.append(
            {
                "key": key,
                "ref_x": ref_x,
                "ref_y": ref_y,
                "label": label,
                "kind": kind,
                "nome": nome,
            }
        )
        _all_parts[_part] = {"pontos": dict(_part_pontos)}
        _save()
        _rebuild_flat()
        _seq = seq
        print("  gravado: {} → ({}, {})".format(nome, lx, ly))
        return lx, ly


def _ask_position(nome, obs, kind, seq):
    # type: (str, str, str, int) -> Tuple
    from automation import win_mouse

    result = {"action": None}  # type: dict
    root = tk.Tk()
    root.title("Mapear — {}".format(_part or ""))
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#1a1a2e", padx=18, pady=14)

    tk.Label(
        root,
        text="Passo {} — {}".format(seq, kind),
        font=("Segoe UI", 10),
        fg="#88aaff",
        bg="#1a1a2e",
    ).pack(anchor="w")
    tk.Label(
        root,
        text=nome,
        font=("Segoe UI", 14, "bold"),
        fg="#ffffff",
        bg="#1a1a2e",
        wraplength=420,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))
    if obs:
        tk.Label(
            root,
            text="Obs: {}".format(obs),
            font=("Segoe UI", 10),
            fg="#ffd479",
            bg="#1a1a2e",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

    tk.Label(
        root,
        text=(
            "Posicione o mouse no lugar certo e aperte F12 para gravar\n"
            "(não precisa clicar — a automação faz o clique).\n"
            "F11 volta o último ponto (não desfaz o clique já feito no SAP)."
        ),
        font=("Segoe UI", 10),
        fg="#cccccc",
        bg="#1a1a2e",
        justify="left",
    ).pack(anchor="w", pady=(12, 0))

    coords = tk.Label(
        root,
        text="X: ----   Y: ----",
        font=("Consolas", 12, "bold"),
        fg="#7CFC00",
        bg="#1a1a2e",
    )
    coords.pack(anchor="w", pady=(10, 0))

    tk.Label(
        root,
        text="F12 = gravar    F11 = voltar    {} = parar".format(
            abort.ABORT_KEY_NAME
        ),
        font=("Segoe UI", 9),
        fg="#8888aa",
        bg="#1a1a2e",
    ).pack(anchor="w", pady=(8, 0))

    # Tela da esquerda (SAP), canto inferior — não cobrir o monitor da direita
    place_window_left_screen(root, margin_x=24, margin_y=80, anchor="bottom")

    def _tick():
        try:
            mx, my = win_mouse.position()
            coords.config(text="X: {:4d}   Y: {:4d}".format(mx, my))
            root.after(50, _tick)
        except tk.TclError:
            pass

    def _on_key(key):
        if key == keyboard.Key.f12:
            result["action"] = "ok"
        elif key == keyboard.Key.f11:
            result["action"] = "undo"

    listener = keyboard.Listener(on_press=_on_key)
    listener.daemon = True
    listener.start()
    _tick()

    root.protocol("WM_DELETE_WINDOW", abort.request_abort)

    while result["action"] is None:
        abort.check()
        try:
            root.update()
        except tk.TclError:
            break
        time.sleep(0.02)

    try:
        listener.stop()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass

    if result["action"] == "undo":
        time.sleep(0.1)
        return ("undo",)

    if result["action"] != "ok":
        raise RuntimeError("Mapeamento cancelado no passo {}.".format(seq))

    # Pausa para soltar o F12 antes do clique da automação
    time.sleep(0.15)
    x, y = win_mouse.position()
    return ("ok", x, y)


def _load():
    # type: () -> Dict[str, dict]
    if not LOCAL_FILE.exists():
        return {}
    try:
        data = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    partes = data.get("partes") if isinstance(data, dict) else None
    if isinstance(partes, dict):
        return dict(partes)
    return {}


def _rebuild_flat():
    # type: () -> None
    global _flat
    flat = {}
    for _name, part in (_all_parts or {}).items():
        pontos = (part or {}).get("pontos") or {}
        for key, val in pontos.items():
            flat[key] = val
    _flat = flat


def _save():
    # type: () -> None
    payload = {
        "versao": 1,
        "descricao": (
            "XY desta máquina, por parte. "
            "Sem este arquivo, o bot usa as coordenadas do código (referência)."
        ),
        "partes": _all_parts,
    }
    LOCAL_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def finish():
    # type: () -> None
    if not _enabled:
        return
    _save()
    print("\nPontos locais em {}:".format(LOCAL_FILE))
    for name in sorted(_all_parts.keys()):
        n = len((_all_parts[name] or {}).get("pontos") or {})
        print("  {}: {} ponto(s)".format(name, n))
