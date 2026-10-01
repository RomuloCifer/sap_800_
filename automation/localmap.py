"""
Mapeamento local de cliques (modo --mapear).

Usa mapa_passos.json (nomes/obs documentados) como guia. A outra pessoa
posiciona o mouse e aperta F8; grava em pontos_local.json.

Sem pontos_local.json → coordenadas do código (máquina de referência).
Com o arquivo → cliques usam o XY local.

  python main.py --mapear         # refaz a parte atual do zero
  python main.py --mapear-resto   # continua só o que falta na parte
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
    global _catalog_passos, _announced
    args = list(argv if argv is not None else sys.argv[1:])
    if "--mapear" not in args and "--mapear-resto" not in args:
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
    _keep_existing = "--mapear-resto" in args
    _part = None
    _part_pontos = {}
    _seq = 0
    _catalog_passos = []
    _all_parts = _load()
    _rebuild_flat()
    print("Modo MAPEAR: posicione o mouse no campo indicado e aperte F8.")
    print("Guia: {}".format(catalog.MAP_FILE.name))
    print("Arquivo local: {}".format(LOCAL_FILE))
    if _keep_existing:
        print("(--mapear-resto: mantém pontos já gravados nesta parte)")
    return True


def begin_part(name):
    # type: (str) -> None
    global _part, _part_pontos, _seq, _all_parts, _catalog_passos
    if not _enabled:
        return

    _all_parts = _load()
    _part = name
    _seq = 0

    cat = catalog._load()
    _catalog_passos = list((cat.get(name) or {}).get("passos") or [])

    if _keep_existing:
        _part_pontos = dict(((_all_parts.get(name) or {}).get("pontos") or {}))
        print(
            "\n--- Mapeando: {} ({} já gravado(s), {} no catálogo) ---\n".format(
                name, len(_part_pontos), len(_catalog_passos)
            )
        )
    else:
        _part_pontos = {}
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


def _capture(key, ref_x, ref_y, label, kind):
    # type: (str, int, int, str, str) -> Tuple[int, int]
    global _seq
    if _part is None:
        begin_part("geral")

    _seq += 1
    info = _find_catalog(label, ref_x, ref_y) or {}
    nome = (info.get("nome") or label or kind).strip()
    obs = (info.get("obs") or "").strip()
    if info.get("_drag_end"):
        nome = "{} (fim da seleção)".format(nome)

    print("  [{} #{}] mapeie: {}".format(_part, _seq, nome))
    if obs:
        print("           obs: {}".format(obs))

    lx, ly = _ask_position(nome, obs, kind, _seq)
    entry = {
        "ordem": _seq,
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
    _all_parts[_part] = {"pontos": dict(_part_pontos)}
    _save()
    _rebuild_flat()
    print("  gravado: {} → ({}, {})".format(nome, lx, ly))
    return lx, ly


def _ask_position(nome, obs, kind, seq):
    # type: (str, str, str, int) -> Tuple[int, int]
    from automation import win_mouse

    confirmed = {"ok": False}
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
        text="Posicione o mouse no lugar certo nesta tela e aperte F8\n(não precisa clicar — a automação faz o clique).",
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
        text="F8 = confirmar    {} = parar".format(abort.ABORT_KEY_NAME),
        font=("Segoe UI", 9),
        fg="#8888aa",
        bg="#1a1a2e",
    ).pack(anchor="w", pady=(8, 0))

    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("+{}+{}".format(max(0, sw - w - 24), max(0, sh - h - 80)))

    def _tick():
        try:
            mx, my = win_mouse.position()
            coords.config(text="X: {:4d}   Y: {:4d}".format(mx, my))
            root.after(50, _tick)
        except tk.TclError:
            pass

    def _on_key(key):
        if key == keyboard.Key.f8:
            confirmed["ok"] = True

    listener = keyboard.Listener(on_press=_on_key)
    listener.daemon = True
    listener.start()
    _tick()

    root.protocol("WM_DELETE_WINDOW", abort.request_abort)

    while not confirmed["ok"]:
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

    if not confirmed["ok"]:
        raise RuntimeError("Mapeamento cancelado no passo {}.".format(seq))

    # Pequena pausa para soltar o F8 antes do clique da automação
    time.sleep(0.15)
    return win_mouse.position()


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
