import json
import os
import re
import unicodedata
from datetime import datetime

GOOGLE_MANUAL_FILE = "data/google_manual.json"
METAS_ATUAL_FILE = "data/metas_atual.json"
HISTORICO_DIR = "data/historico"


def numero(valor):
    if valor is None:
        return 0.0
    texto = str(valor).strip()
    if texto == "" or texto == "-":
        return 0.0
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except Exception:
        return 0.0


def br(valor, casas=0):
    if casas == 0:
        return str(int(round(valor)))
    return f"{valor:.{casas}f}".replace(".", ",")


def normalizar_nome(nome):
    nome = unicodedata.normalize("NFD", str(nome))
    return nome.encode("ascii", "ignore").decode("utf-8").strip().lower()


def carregar_json(caminho):
    if not os.path.exists(caminho):
        return None
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho
