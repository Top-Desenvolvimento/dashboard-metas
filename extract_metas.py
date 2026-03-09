#!/usr/bin/env python3
"""
Wrapper para evitar rodar versão duplicada/antiga.

Este arquivo existe porque há uma cópia do projeto dentro de `dashboard-metas/`.
Ele simplesmente executa o `extract_metas.py` da raiz do projeto (fonte de verdade).
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    root_script = Path(__file__).resolve().parents[1] / "extract_metas.py"
    runpy.run_path(str(root_script), run_name="__main__")


if __name__ == "__main__":
    main()
