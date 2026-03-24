import json
import os
import re

METAS_PATH = "data/metas_atual.json"
GOOGLE_PATH = "data/google_reviews.json"

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

    try:
        return int("".join(numeros))
    except Exception:
        return None

def formatar_inteiro(valor):
    if valor is None:
        return "-"
    return str(int(valor))

def formatar_percentual(valor):
    if valor is None:
        return "-"
    return f"{valor:.1f}%".replace(".", ",")

def main():
    metas = carregar_json(METAS_PATH, {})
    google = carregar_json(GOOGLE_PATH, [])

    google_map = {
        item["cidade"]: item
        for item in google
        if item.get("avaliacoes") is not None
    }

    for cidade, info in metas.items():
        indicadores = info.setdefault("indicadores", {})
        google_ind = indicadores.get("avaliacoes_google")

        if not google_ind:
            continue

        item_google = google_map.get(cidade)
        if not item_google:
            continue

        meta_atual = extrair_numero(google_ind.get("meta"))
        realizado_google = extrair_numero(item_google.get("avaliacoes"))

        if realizado_google is None:
            continue

        google_ind["ate_o_momento"] = formatar_inteiro(realizado_google)

        if meta_atual is not None:
            falta = max(meta_atual - realizado_google, 0)
            progresso = (realizado_google / meta_atual) * 100 if meta_atual > 0 else None

            google_ind["falta"] = formatar_inteiro(falta)
            google_ind["progresso"] = formatar_percentual(progresso)
        else:
            google_ind["falta"] = "-"
            google_ind["progresso"] = "-"

        indicadores["avaliacoes_google"] = google_ind

    salvar_json(METAS_PATH, metas)
    print("Avaliações do Google integradas ao metas_atual.json com sucesso.")

if __name__ == "__main__":
    main()
