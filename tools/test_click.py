"""
Testa um clique em coordenada específica.

Uso:
  python tools/test_click.py -1250 680
  python tools/test_click.py -1250 680 --double
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation import win_mouse


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    double = "--double" in sys.argv
    if len(args) < 2:
        print("Uso: python tools/test_click.py X Y [--double]")
        return
    x, y = int(args[0]), int(args[1])
    clicks = 2 if double else 1
    print("Clique em ({}, {}) em 3 segundos...".format(x, y))
    for n in range(3, 0, -1):
        print(n)
        time.sleep(1)
    win_mouse.click(x, y, clicks=clicks)
    rx, ry = win_mouse.position()
    print("Feito. Cursor agora em ({}, {})".format(rx, ry))


if __name__ == "__main__":
    main()
