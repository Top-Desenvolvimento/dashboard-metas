#!/usr/bin/env python3
"""
Wrapper para evitar rodar versão duplicada/antiga.

Executa o `generate_dashboard.py` da raiz do projeto (fonte de verdade).
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    root_script = Path(__file__).resolve().parents[1] / "generate_dashboard.py"
    runpy.run_path(str(root_script), run_name="__main__")


if __name__ == "__main__":
    main()
