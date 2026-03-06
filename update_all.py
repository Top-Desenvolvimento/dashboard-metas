#!/usr/bin/env python3
"""
Pipeline completa:
1) Coleta metas + avaliações (extract_metas.py)
2) Exporta PPTX do mês (export_pptx.py)
3) Gera dashboard HTML e copia data/ -> docs/ (generate_dashboard.py)

Uso:
  python update_all.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime


def run(cmd: list[str]) -> None:
    print("\n$ " + " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    print("=" * 60)
    print("Atualização completa do Dashboard de Metas")
    print("Início:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("=" * 60)

    py = sys.executable
    run([py, "extract_metas.py"])
    run([py, "export_pptx.py"])
    run([py, "generate_dashboard.py"])

    print("\n✓ Finalizado:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


if __name__ == "__main__":
    main()

