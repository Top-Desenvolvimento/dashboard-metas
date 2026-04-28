import json
import os
import re
from datetime import datetime

GOOGLE_MANUAL_FILE = "data/google_manual.json"
METAS_ATUAL_FILE = "data/metas_atual.json"
HISTORICO_DIR = "data/historico"


def numero(valor):
    if valor is None:
        return 0.0
    texto = str(valor).strip().replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except Exception:
        return 0.0


def br(valor, casas=0):
    if casas == 0:
        return str(int(round(valor)))
    return f"{valor:.{casas}f}".replace(".", ",")


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def mes_ref():
    valor = os.getenv("MES_REFERENCIA", "AUTO")
    if valor and valor != "AUTO" and re.match(r"^\d{4}-\d{2}$", valor):
        return valor
    return datetime.now().strftime("%Y-%m")


def montar_google(info):
    inicial = numero(info.get("inicial"))
    atual = numero(info.get("valor_atual"))
    meta = numero(info.get("valor_meta"))

    realizado = atual - inicial
    falta = meta - realizado
    progresso = (realizado / meta * 100) if meta > 0 else 0

    return {
        "meta": br(meta, 0),
        "ate_o_momento": br(realizado, 0),
        "falta": br(falta, 0),
        "progresso": f"{progresso:.2f}%".replace(".", ","),
        "valor_inicial": br(inicial, 0),
        "valor_atual": br(atual, 0)
    }


def aplicar(base, google_mes):
    for cidade, valores in google_mes.items():
        if cidade not in base:
            print(f"⚠️ Cidade não encontrada no metas: {cidade}")
            continue

        base[cidade].setdefault("indicadores", {})
        base[cidade]["indicadores"]["avaliacoes_google"] = montar_google(valores)

        print(
            f"✅ {cidade}: inicial={valores.get('inicial')} | "
            f"atual={valores.get('valor_atual')} | "
            f"meta={valores.get('valor_meta')} | "
            f"realizado={base[cidade]['indicadores']['avaliacoes_google']['ate_o_momento']}"
        )

    return base


def main():
    mes = mes_ref()
    print("=== APLICAR GOOGLE MANUAL V2 ===")
    print(f"Mês: {mes}")

    google = carregar_json(GOOGLE_MANUAL_FILE)

    if mes not in google:
        raise Exception(f"Mês {mes} não existe em {GOOGLE_MANUAL_FILE}")

    google_mes = google[mes]

    if os.path.exists(METAS_ATUAL_FILE):
        metas_atual = carregar_json(METAS_ATUAL_FILE)
        metas_atual = aplicar(metas_atual, google_mes)
        salvar_json(METAS_ATUAL_FILE, metas_atual)
        print("✅ data/metas_atual.json atualizado")

    historico_path = f"{HISTORICO_DIR}/metas_{mes}.json"
    if os.path.exists(historico_path):
        historico = carregar_json(historico_path)
        historico = aplicar(historico, google_mes)
        salvar_json(historico_path, historico)
        print(f"✅ {historico_path} atualizado")
    else:
        print(f"⚠️ Histórico não encontrado: {historico_path}")


if __name__ == "__main__":
    main()
