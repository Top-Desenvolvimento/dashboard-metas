import json
import os

METAS_PATH = "data/metas_atual.json"
GOOGLE_PATH = "data/google_reviews.json"

def carregar_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    metas = carregar_json(METAS_PATH)
    google = carregar_json(GOOGLE_PATH)

    # transforma em dict por cidade
    google_map = {
        item["cidade"]: item
        for item in google
        if item.get("avaliacoes") is not None
    }

    for cidade, info in metas.items():
        indicadores = info.setdefault("indicadores", {})

        google_data = google_map.get(cidade)

        if google_data:
            total = google_data["avaliacoes"]

            indicadores["avaliacoes_google"] = {
                "meta": "-",  # você pode ajustar depois
                "ate_o_momento": str(total),
                "falta": "-",
                "progresso": "100%"  # ou calcular depois
            }

    salvar_json(METAS_PATH, metas)

    print("Google integrado ao metas_atual.json com sucesso.")

if __name__ == "__main__":
    main()
