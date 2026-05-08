import json
import os
import re
import unicodedata
from datetime import datetime

METAS_PATH = "data/metas_atual.json"
GOOGLE_INICIAL_PATH = "data/google_inicial"
GOOGLE_ATUAL_PATH = "data/google_atual.json"


def carregar_json(path, default):
    if not os.path.exists(path):
        print(f"Arquivo não encontrado: {path}")
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remover_acentos(texto):
    texto = str(texto)
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def normalizar_nome(nome):
    return remover_acentos(nome).strip().lower()


def buscar_por_cidade(base, cidade):
    cidade_norm = normalizar_nome(cidade)

    for chave, valor in base.items():
        if normalizar_nome(chave) == cidade_norm:
            return valor

    return None


def extrair_numero(valor):
    if valor is None:
        return None

    texto = str(valor).strip()

    if texto == "" or texto == "-":
        return None

    numeros = re.findall(r"\d+", texto)

    if not numeros:
        return None

    return int("".join(numeros))


def formatar_percentual(valor):
    return f"{valor:.2f}%".replace(".", ",")


def descobrir_mes(metas):
    for _, info in metas.items():
        mes = info.get("mes_referencia")
        if mes:
            return mes

    return datetime.now().strftime("%Y-%m")


def main():
    metas = carregar_json(METAS_PATH, {})
    google_inicial = carregar_json(GOOGLE_INICIAL_PATH, {})
    google_atual = carregar_json(GOOGLE_ATUAL_PATH, {})

    mes_ref = descobrir_mes(metas)
    base_inicial = google_inicial.get(mes_ref, {})

    print(f"Mês referência: {mes_ref}")
    print(f"Meses disponíveis no google_inicial: {list(google_inicial.keys())}")

    for cidade, info in metas.items():
        indicadores = info.setdefault("indicadores", {})

        google = indicadores.setdefault("avaliacoes_google", {
            "meta": "-",
            "ate_o_momento": "0",
            "falta": "-",
            "progresso": "0,00%"
        })

        meta = extrair_numero(google.get("meta"))
        inicial = extrair_numero(buscar_por_cidade(base_inicial, cidade))
        atual = extrair_numero(buscar_por_cidade(google_atual, cidade))

        if atual is None or inicial is None:
            google["ate_o_momento"] = "0"
            google["falta"] = str(meta) if meta else "-"
            google["progresso"] = "0,00%"
            print(f"{cidade}: não calculado. Inicial={inicial}, Atual={atual}")
            continue

        realizado = max(atual - inicial, 0)

        google["ate_o_momento"] = str(realizado)

        if meta and meta > 0:
            falta = max(meta - realizado, 0)
            progresso = (realizado / meta) * 100

            google["falta"] = str(falta)
            google["progresso"] = formatar_percentual(progresso)
        else:
            google["falta"] = "-"
            google["progresso"] = "0,00%"

        print(
            f"{cidade}: inicial={inicial}, atual={atual}, "
            f"realizado={realizado}, meta={meta}"
        )

    salvar_json(METAS_PATH, metas)
    print("Google integrado ao metas_atual.json com sucesso.")


if __name__ == "__main__":
    main()
