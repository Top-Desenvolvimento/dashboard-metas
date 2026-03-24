import json
import os
import re
from datetime import datetime

METAS_PATH = "data/metas_atual.json"
GOOGLE_PATH = "data/google_reviews.json"
GOOGLE_INICIAL_PATH = "data/google_inicial"
GOOGLE_META_PATH = "data/google_metamarço"

def carregar_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extrair_numero(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or texto == "-":
        return None
    numeros = re.findall(r"\d+", texto.replace(".", "").replace(",", ""))
    if not numeros:
        return None
    return int("".join(numeros))

def formatar_int(valor):
    if valor is None:
        return "-"
    return str(int(valor))

def formatar_percentual(valor):
    if valor is None:
        return "-"
    return f"{valor:.1f}%".replace(".", ",")

def descobrir_mes(base_metas):
    for _, info in base_metas.items():
        mes = info.get("mes_referencia")
        if mes:
            return mes
    return datetime.now().strftime("%Y-%m")

def main():
    metas = carregar_json(METAS_PATH, {})
    google_reviews = carregar_json(GOOGLE_PATH, [])
    google_inicial = carregar_json(GOOGLE_INICIAL_PATH, {})
    google_meta = carregar_json(GOOGLE_META_PATH, {})

    mes_ref = descobrir_mes(metas)

    base_inicial_mes = google_inicial.get(mes_ref, {})
    base_meta_mes = google_meta.get(mes_ref, {})

    reviews_map = {
        item["cidade"]: item
        for item in google_reviews
        if item.get("avaliacoes") is not None
    }

    for cidade, info in metas.items():
        indicadores = info.setdefault("indicadores", {})
        google_ind = indicadores.setdefault("avaliacoes_google", {
            "meta": "-",
            "ate_o_momento": "-",
            "falta": "-",
            "progresso": "-"
        })

        inicial = extrair_numero(base_inicial_mes.get(cidade))
        meta_mes = extrair_numero(base_meta_mes.get(cidade))
        review_item = reviews_map.get(cidade)
        atual_total = extrair_numero(review_item.get("avaliacoes")) if review_item else None

        if meta_mes is not None:
            google_ind["meta"] = formatar_int(meta_mes)

        if atual_total is None or inicial is None or meta_mes is None:
            google_ind["ate_o_momento"] = "-"
            google_ind["falta"] = formatar_int(meta_mes) if meta_mes is not None else "-"
            google_ind["progresso"] = "-"
            indicadores["avaliacoes_google"] = google_ind
            continue

        realizado_mes = max(atual_total - inicial, 0)
        falta = max(meta_mes - realizado_mes, 0)
        progresso = (realizado_mes / meta_mes) * 100 if meta_mes > 0 else None

        google_ind["ate_o_momento"] = formatar_int(realizado_mes)
        google_ind["falta"] = formatar_int(falta)
        google_ind["progresso"] = formatar_percentual(progresso)

        indicadores["avaliacoes_google"] = google_ind

    salvar_json(METAS_PATH, metas)
    print(f"Google integrado ao metas_atual.json com base em {mes_ref}.")

if __name__ == "__main__":
    main()
