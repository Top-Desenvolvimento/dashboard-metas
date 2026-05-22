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


def carregar_json(caminho):
    if not os.path.exists(caminho):
        return None

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def mes_env_para_json(valor):
    if valor and valor != "AUTO":
        valor = valor.strip()

        if re.match(r"^\d{4}-\d{2}$", valor):
            return valor

    return datetime.now().strftime("%Y-%m")


def montar_indicador_google(info):
    inicial = numero(info.get("valor_inicial", info.get("inicial", 0)))
    valor_meta = numero(info.get("valor_meta", info.get("meta", 0)))
    valor_atual = numero(info.get("valor_atual", info.get("atual", 0)))

    realizado = valor_atual - inicial

    if realizado < 0:
        realizado = 0

    falta = valor_meta - realizado

    if falta < 0:
        falta = 0

    progresso = 0.0

    if valor_meta > 0:
        progresso = (realizado / valor_meta) * 100

    return {
        "meta": br(valor_meta, 0),
        "ate_o_momento": br(realizado, 0),
        "falta": br(falta, 0),
        "progresso": f"{progresso:.2f}%".replace(".", ","),
        "valor_inicial": br(inicial, 0),
        "valor_atual": br(valor_atual, 0)
    }


def aplicar_google_em_base(base, google_mes, mes_ref):
    alterados = 0

    for cidade, info_cidade in base.items():
        if cidade not in google_mes:
            print(f"Sem Google manual para {cidade}")
            continue

        indicadores = info_cidade.setdefault("indicadores", {})

        indicador = montar_indicador_google(google_mes[cidade])
        indicadores["avaliacoes_google"] = indicador

        print(
            f"Google aplicado em {cidade}: "
            f"inicial={indicador['valor_inicial']} | "
            f"atual={indicador['valor_atual']} | "
            f"realizado={indicador['ate_o_momento']} | "
            f"meta={indicador['meta']} | "
            f"progresso={indicador['progresso']}"
        )

        alterados += 1

    return alterados


def main():
    mes_ref = mes_env_para_json(os.getenv("MES_REFERENCIA", "AUTO"))

    print("=" * 55)
    print("Aplicando Google manual")
    print(f"Mês referência: {mes_ref}")
    print("=" * 55)

    google = carregar_json(GOOGLE_MANUAL_FILE)

    if not google:
        raise FileNotFoundError(f"Arquivo não encontrado: {GOOGLE_MANUAL_FILE}")

    google_mes = google.get(mes_ref)

    if not google_mes:
        raise ValueError(f"Mês {mes_ref} não encontrado em {GOOGLE_MANUAL_FILE}")

    total = 0

    metas_atual = carregar_json(METAS_ATUAL_FILE)

    if metas_atual:
        total += aplicar_google_em_base(metas_atual, google_mes, mes_ref)
        salvar_json(METAS_ATUAL_FILE, metas_atual)

    caminho_historico = os.path.join(HISTORICO_DIR, f"metas_{mes_ref}.json")
    historico = carregar_json(caminho_historico)

    if historico:
        total += aplicar_google_em_base(historico, google_mes, mes_ref)
        salvar_json(caminho_historico, historico)

    print(f"Finalizado. Total aplicado: {total}")


if __name__ == "__main__":
    main()
