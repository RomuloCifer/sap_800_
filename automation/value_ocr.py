"""
Print de região + leitura de valor monetário (OCR, com fallback clipboard).

Usado para comparar Total Value entre dois momentos do fluxo
(antes de fechar a janela pós-RANDOM e ao final da Parte 4).
A comparação com a planilha entra depois (Fase 1).
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageOps

from automation import localmap, win_mouse
from automation.capture import click_point, drag_copy
from automation.utils import clean_value

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"

# Locais comuns do Tesseract no Windows (winget UB-Mannheim)
_TESSERACT_CANDIDATES = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]

_tesseract_ready = False


def _configure_tesseract():
    # type: () -> None
    """Garante que pytesseract ache o exe mesmo se o PATH não foi atualizado."""
    global _tesseract_ready
    if _tesseract_ready:
        return
    import shutil

    import pytesseract

    which = shutil.which("tesseract")
    if which:
        pytesseract.pytesseract.tesseract_cmd = which
        _tesseract_ready = True
        return
    for candidate in _TESSERACT_CANDIDATES:
        if candidate.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            print("Tesseract: usando {}".format(candidate))
            _tesseract_ready = True
            return
    # Deixa o pytesseract tentar o PATH; o erro virá claro depois
    _tesseract_ready = True


# PRINT A — após RANDOM+DIGIT, antes do clique que fecha a janela
# Cantos informados: IE (-1144,772) e SD (-1080,750)
PRINT_A_LEFT = -1144
PRINT_A_TOP = 750
PRINT_A_RIGHT = -1080
PRINT_A_BOTTOM = 772

# PRINT B — fim da Parte 4, após DIGIT
PRINT_B_CLICK = (-1772, 243)
PRINT_B_LEFT = -1322
PRINT_B_TOP = 922
PRINT_B_RIGHT = -1231
PRINT_B_BOTTOM = 944

_MONEY_RE = re.compile(
    r"("
    r"\d{1,3}(?:\.\d{3})+,\d{2}"  # BR: 15.039,50
    r"|"
    r"\d{1,3}(?:,\d{3})+\.\d{2}"  # US: 15,039.50
    r"|"
    r"\d{1,3}(?:\.\d{3})+\.\d{2}"  # 15.039.50 (ponto milhar + decimal)
    r"|"
    r"\d+,\d{2}"  # 15039,50
    r"|"
    r"\d+\.\d{2}"  # 15039.50
    r"|"
    r"\d+"
    r")"
)


def normalize_money(text):
    # type: (object) -> Optional[Decimal]
    """
    Normaliza '15.039,50' / '15,039.50' / '15.039.50' / '15039,50' → Decimal.
    Retorna None se não achar número.
    """
    if text is None:
        return None
    raw = clean_value(str(text))
    if not raw:
        return None

    compact = raw.replace(" ", "")
    m = _MONEY_RE.search(compact)
    if not m:
        return None
    token = m.group(1)

    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            # BR: 15.039,50
            token = token.replace(".", "").replace(",", ".")
        else:
            # US: 15,039.50
            token = token.replace(",", "")
    elif "," in token:
        left, right = token.split(",", 1)
        if len(right) == 2 and right.isdigit():
            token = left.replace(".", "") + "." + right
        else:
            token = token.replace(",", ".")
    elif token.count(".") > 1:
        # 15.039.50 → milhares + decimal no último ponto
        parts = token.split(".")
        token = "".join(parts[:-1]) + "." + parts[-1]
    elif token.count(".") == 1:
        left, right = token.split(".")
        if len(right) == 3 and right.isdigit():
            # 15.039 milhar sem centavos
            token = left + right

    try:
        return Decimal(token)
    except InvalidOperation:
        return None


def money_equal(a, b, places=2):
    # type: (Optional[Decimal], Optional[Decimal], int) -> bool
    if a is None or b is None:
        return False
    q = Decimal("1").scaleb(-places)
    return a.quantize(q) == b.quantize(q)


def _ensure_run_dir(run_dir=None, batch=None):
    # type: (Optional[Path], Optional[object]) -> Path
    if run_dir is not None:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    date_part = datetime.now().strftime("%Y%m%d")
    if batch is not None and str(batch).strip():
        safe_batch = re.sub(r"[^\w\-]+", "_", str(batch).strip())
        base = "{}_{}".format(date_part, safe_batch)
    else:
        base = "{}_{}".format(date_part, datetime.now().strftime("%H%M%S"))

    path = RUNS_DIR / base
    if path.exists():
        n = 1
        while True:
            candidate = RUNS_DIR / "{} ({})".format(base, n)
            if not candidate.exists():
                path = candidate
                break
            n += 1
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_box(x1, y1, x2, y2):
    # type: (int, int, int, int) -> Tuple[int, int, int, int]
    left = min(int(x1), int(x2))
    right = max(int(x1), int(x2))
    top = min(int(y1), int(y2))
    bottom = max(int(y1), int(y2))
    if right <= left:
        right = left + 1
    if bottom <= top:
        bottom = top + 1
    return left, top, right, bottom


def grab_region(x1, y1, x2, y2, save_path=None):
    # type: (int, int, int, int, Optional[Path]) -> Image.Image
    """Captura retângulo em coords de tela (mesmo sistema do mouse)."""
    import mss
    import mss.tools

    win_mouse.ensure_dpi_awareness()
    left, top, right, bottom = _normalize_box(x1, y1, x2, y2)
    width = right - left
    height = bottom - top
    region = {"left": left, "top": top, "width": width, "height": height}
    with mss.mss() as sct:
        shot = sct.grab(region)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path)
        print("Screenshot salvo: {}".format(save_path))
    return img


def _ocr_image(img):
    # type: (Image.Image) -> str
    import pytesseract

    _configure_tesseract()

    # Amplia e aumenta contraste — SAP costuma ter fonte pequena
    big = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(big)
    gray = ImageOps.autocontrast(gray)
    config = (
        "--psm 7 "
        "-c tessedit_char_whitelist=0123456789., "
    )
    try:
        return pytesseract.image_to_string(gray, config=config) or ""
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR não está instalado ou não está no PATH. "
            "Instale com: winget install UB-Mannheim.TesseractOCR "
            "(ou use o fallback clipboard se a região permitir)."
        )


def _read_via_ocr(img):
    # type: (Image.Image) -> Tuple[Optional[Decimal], str]
    raw = _ocr_image(img)
    value = normalize_money(raw)
    return value, raw.strip()


def _read_via_clipboard(x1, y1, x2, y2, label, dry_run=False):
    # type: (int, int, int, int, str, bool) -> Tuple[Optional[Decimal], str]
    left, top, right, bottom = _normalize_box(x1, y1, x2, y2)
    mid_y = (top + bottom) // 2
    # Arrasta na horizontal no meio da faixa (padrão do projeto)
    raw = drag_copy(left, mid_y, right, mid_y, label=label + " (clipboard)", dry_run=dry_run)
    raw = clean_value(raw)
    return normalize_money(raw), raw


def read_money_region(
    x1,
    y1,
    x2,
    y2,
    label,
    run_dir=None,
    dry_run=False,
    prefer_ocr=True,
):
    # type: (int, int, int, int, str, Optional[Path], bool, bool) -> dict
    """
    Resolve coords locais, tira print, lê valor (OCR → fallback clipboard).

    Retorna dict: value (Decimal|None), raw, path, method, label
    """
    ax, ay = localmap.resolve(x1, y1, label + " SE", kind="click")
    bx, by = localmap.resolve(x2, y2, label + " ID", kind="click")
    left, top, right, bottom = _normalize_box(ax, ay, bx, by)

    if dry_run:
        print("[dry-run] {} região ({},{}) -> ({},{})".format(label, left, top, right, bottom))
        return {
            "label": label,
            "value": Decimal("15039.50"),
            "raw": "15.039,50",
            "path": None,
            "method": "dry_run",
        }

    out_dir = _ensure_run_dir(run_dir)
    safe = re.sub(r"[^\w\-]+", "_", label.strip()) or "valor"
    png_path = out_dir / "{}.png".format(safe)

    print(
        "Capturando {} em ({},{}) -> ({},{})...".format(label, left, top, right, bottom)
    )
    img = grab_region(left, top, right, bottom, save_path=png_path)

    value = None  # type: Optional[Decimal]
    raw = ""
    method = "none"

    if prefer_ocr:
        try:
            value, raw = _read_via_ocr(img)
            method = "ocr"
            print("{} OCR bruto: {!r} → {}".format(label, raw, value))
        except Exception as exc:
            print("OCR falhou ({}): {}".format(label, exc))
            value = None

    if value is None:
        value, raw = _read_via_clipboard(left, top, right, bottom, label, dry_run=False)
        method = "clipboard"
        print("{} clipboard: {!r} → {}".format(label, raw, value))

    if value is None:
        raise RuntimeError(
            "Não foi possível ler valor monetário em {!r} (OCR/clipboard). "
            "Bruto: {!r}".format(label, raw)
        )

    return {
        "label": label,
        "value": value,
        "raw": raw,
        "path": str(png_path),
        "method": method,
    }


def capture_print_a(run_dir=None, dry_run=False):
    # type: (Optional[Path], bool) -> dict
    """Total Value na tela do ARDFE, antes de fechar a janela."""
    return read_money_region(
        PRINT_A_LEFT,
        PRINT_A_TOP,
        PRINT_A_RIGHT,
        PRINT_A_BOTTOM,
        label="TOTAL_VALUE_A",
        run_dir=run_dir,
        dry_run=dry_run,
    )


def capture_print_b(run_dir=None, dry_run=False, wait_after_click=1.0):
    # type: (Optional[Path], bool, float) -> dict
    """Clica na aba/campo e lê Total Value no fim da Parte 4."""
    click_point(
        PRINT_B_CLICK[0],
        PRINT_B_CLICK[1],
        label="TOTAL_VALUE_B — clique",
        dry_run=dry_run,
        wait_after=wait_after_click,
    )
    return read_money_region(
        PRINT_B_LEFT,
        PRINT_B_TOP,
        PRINT_B_RIGHT,
        PRINT_B_BOTTOM,
        label="TOTAL_VALUE_B",
        run_dir=run_dir,
        dry_run=dry_run,
    )


def compare_total_values(value_a, value_b, value_sheet=None):
    # type: (Optional[Decimal], Optional[Decimal], Optional[Decimal]) -> dict
    """
    Compara A vs B (e planilha se informada).
    Retorna {ok, detail, values}.
    """
    parts = []
    ok = money_equal(value_a, value_b)
    parts.append(
        "A={} B={} → {}".format(
            value_a, value_b, "OK" if ok else "DIFERENTE"
        )
    )
    if value_sheet is not None:
        ok_sheet = money_equal(value_a, value_sheet) and money_equal(value_b, value_sheet)
        parts.append(
            "planilha={} → {}".format(
                value_sheet, "OK" if ok_sheet else "DIFERENTE"
            )
        )
        ok = ok and ok_sheet

    detail = "; ".join(parts)
    print("Comparação Total Value: {}".format(detail))
    return {
        "ok": ok,
        "detail": detail,
        "values": {"a": value_a, "b": value_b, "sheet": value_sheet},
    }


def new_run_dir(batch=None):
    # type: (Optional[object]) -> Path
    """Pasta runs/YYYYMMDD_<batch>/ (sem batch: usa hora como fallback)."""
    return _ensure_run_dir(None, batch=batch)
