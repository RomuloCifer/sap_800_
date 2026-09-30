"""
Calibração de coordenadas entre máquinas.

Sem arquivo calibration.json → identidade (cliques desta máquina não mudam).
Com calibração → mapeia (x, y) originais para a tela da outra pessoa.

Transformação: x' = sx * x + ox ; y' = sy * y + oy
(calculada por regressão linear a partir de pontos de referência).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
CALIBRATION_FILE = ROOT / "calibration.json"


@dataclass
class ReferencePoint:
    id: str
    label: str
    x: int
    y: int
    hint: str = ""


# Pontos âncora na máquina de referência (suas coordenadas atuais).
# A outra pessoa clica nos MESMOS lugares da UI, na mesma ordem.
# Os pontos devem ter boa dispersão em X e Y para estabilizar a regressão.
REFERENCE_POINTS = [
    ReferencePoint(
        id="cmd",
        label="1) Barra de comando (campo branco onde digita /n/...)",
        hint=(
            "Janela do SAP aberta. Clique no meio do campo de comando "
            "(barra superior, onde se digita a transação)."
        ),
        x=-1827,
        y=58,
    ),
    ReferencePoint(
        id="empresa",
        label="2) Campo Empresa (onde a automação digita 1300)",
        hint=(
            "Entre em /n/lkmt/ardfe e deixe a tela de seleção aberta. "
            "Clique no meio do campo Empresa (primeiro campo numérico da lista)."
        ),
        x=-1616,
        y=267,
    ),
    ReferencePoint(
        id="data",
        label="3) Campo da DATA (onde digita 01.02.2025)",
        hint=(
            "Na MESMA tela de seleção. Clique no meio do campo de data "
            "(abaixo de Empresa / Batch — NÃO clique embaixo da janela)."
        ),
        x=-1629,
        y=373,
    ),
    ReferencePoint(
        id="rodape",
        label="4) Bem EMBAIXO da janela do SAP (rodapé da tela de seleção)",
        hint=(
            "Ainda na mesma tela. Desça o mouse até a parte inferior da "
            "janela do SAP (região de botões/checkboxes de baixo). "
            "NÃO use a barra de tarefas do Windows. "
            "O Y precisa ficar bem mais baixo que o campo da data."
        ),
        x=-1506,
        y=766,
    ),
]


@dataclass
class Transform:
    sx: float = 1.0
    sy: float = 1.0
    ox: float = 0.0
    oy: float = 0.0

    def is_identity(self, tol=1e-6):
        # type: (float) -> bool
        return (
            abs(self.sx - 1.0) < tol
            and abs(self.sy - 1.0) < tol
            and abs(self.ox) < tol
            and abs(self.oy) < tol
        )

    def map_xy(self, x, y):
        # type: (int, int) -> Tuple[int, int]
        return (
            int(round(self.sx * float(x) + self.ox)),
            int(round(self.sy * float(y) + self.oy)),
        )

    def map_dx(self, dx):
        # type: (int) -> int
        """Escala um deslocamento horizontal (ex.: wiggle_x)."""
        return int(round(self.sx * float(dx)))


@dataclass
class _CalibrationState:
    transform: Optional[Transform] = None
    loaded: bool = False
    announced: bool = False


_state = _CalibrationState()


def _fit_1d(src, dst):
    # type: (List[float], List[float]) -> Tuple[float, float]
    """Ajusta dst = s * src + o por mínimos quadrados."""
    n = len(src)
    if n == 0:
        return 1.0, 0.0
    if n == 1:
        return 1.0, float(dst[0] - src[0])

    mean_s = sum(src) / float(n)
    mean_d = sum(dst) / float(n)
    var = sum((s - mean_s) ** 2 for s in src)
    if var < 1e-9:
        return 1.0, mean_d - mean_s
    cov = sum((s - mean_s) * (d - mean_d) for s, d in zip(src, dst))
    s = cov / var
    o = mean_d - s * mean_s
    return float(s), float(o)


def fit_transform(pairs):
    # type: (List[Tuple[Tuple[int, int], Tuple[int, int]]]) -> Transform
    """
    pairs: lista de ((x_ref, y_ref), (x_local, y_local)).
    Com 1 ponto → só deslocamento. Com 2+ → escala + deslocamento por eixo.
    """
    if not pairs:
        return Transform()

    xs = [float(a[0]) for a, _ in pairs]
    ys = [float(a[1]) for a, _ in pairs]
    Xs = [float(b[0]) for _, b in pairs]
    Ys = [float(b[1]) for _, b in pairs]

    sx, ox = _fit_1d(xs, Xs)
    sy, oy = _fit_1d(ys, Ys)
    return Transform(sx=sx, sy=sy, ox=ox, oy=oy)


def save_transform(transform, pairs=None, path=None):
    # type: (Transform, Optional[list], Optional[Path]) -> Path
    path = path or CALIBRATION_FILE
    payload = {
        "sx": transform.sx,
        "sy": transform.sy,
        "ox": transform.ox,
        "oy": transform.oy,
        "pairs": pairs or [],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    clear_cache()
    return path


def clear_calibration(path=None):
    # type: (Optional[Path]) -> bool
    path = path or CALIBRATION_FILE
    clear_cache()
    if path.exists():
        path.unlink()
        return True
    return False


def load_transform(path=None):
    # type: (Optional[Path]) -> Transform
    path = path or CALIBRATION_FILE
    if not path.exists():
        return Transform()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        print("Aviso: calibration.json corrompido — usando coordenadas originais.")
        return Transform()
    return Transform(
        sx=float(data.get("sx", 1.0)),
        sy=float(data.get("sy", 1.0)),
        ox=float(data.get("ox", 0.0)),
        oy=float(data.get("oy", 0.0)),
    )


def clear_cache():
    # type: () -> None
    global _state
    _state = _CalibrationState()


def get_transform():
    # type: () -> Transform
    if not _state.loaded:
        _state.transform = load_transform()
        _state.loaded = True
    return _state.transform or Transform()


def has_calibration():
    # type: () -> bool
    return CALIBRATION_FILE.exists() and not get_transform().is_identity()


def map_xy(x, y):
    # type: (int, int) -> Tuple[int, int]
    return get_transform().map_xy(x, y)


def map_dx(dx):
    # type: (int) -> int
    return get_transform().map_dx(dx)


def announce_if_active():
    # type: () -> None
    """Avisa uma vez no console se a calibração estiver ativa."""
    if _state.announced:
        return
    _state.announced = True
    t = get_transform()
    if not CALIBRATION_FILE.exists() or t.is_identity():
        return
    print(
        "Calibração ativa: sx={:.4f} sy={:.4f} ox={:.1f} oy={:.1f} ({})".format(
            t.sx, t.sy, t.ox, t.oy, CALIBRATION_FILE.name
        )
    )
