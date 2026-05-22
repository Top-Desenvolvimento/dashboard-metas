import json
import os
from datetime import datetime

GOOGLE_ATUAL_PATH = "data/google_atual.json"
GOOGLE_INICIAL_PATH = "data/google_inicial"


def carregar_json(path, default):
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    mes_ref = os.getenv("MES_REFERENCIA", "").strip()

    if not mes_ref or mes_ref == "AUTO":
        mes_ref = datetime.now().strftime("%Y-%m")

    google_atual = carregar_json(GOOGLE_ATUAL_PATH, {})
    google_inicial = carregar_json(GOOGLE_INICIAL_PATH, {})

    if mes_ref in google_inicial:
        print(f"O mês {mes_ref} já existe em google_inicial.")
        return

    google_inicial[mes_ref] = google_atual

    salvar_json(GOOGLE_INICIAL_PATH, google_inicial)

    print(f"Mês {mes_ref} criado em google_inicial com sucesso.")
    print("Valores iniciais salvos:")
    print(json.dumps(google_atual, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
