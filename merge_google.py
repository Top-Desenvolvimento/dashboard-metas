import json
import os
import re
from datetime import datetime

METAS_PATH = "data/metas_atual.json"
GOOGLE_INICIAL_PATH = "data/google_inicial"
GOOGLE_META_PATH = "data/google_metamarço"
GOOGLE_ATUAL_PATH = "data/google_atual.json"


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
    return f"{valor:.2f}%".replace(".", ",")


def descobrir_mes(base_metas):
    for _, info in base_metas.items():
        mes = info.get("mes_referencia")
        if mes:
            return mes

    return datetime.now().strftime("%Y-%m")


def normalizar_nome(nome):
    return str(nome).strip().lower()


def buscar_por_cidade(base, cidade):
    """
    Busca a cidade ignorando diferença de maiúsculas/minúsculas e espaços.
    Exemplo: 'SS do Cai' encontra 'SS do Caí' somente se estiver igual sem acento.
    """
    cidade_norm = normalizar_nome(cidade)

    for chave, valor in base.items():
        if normalizar_nome(chave) == cidade_norm:
            return valor

    return None


def main():
    metas = carregar_json(METAS_PATH, {})
    google_inicial = carregar_json(GOOGLE_INICIAL_PATH, {})
    google_meta = carregar_json(GOOGLE_META_PATH, {})
    google_atual = carregar_json(GOOGLE_ATUAL_PATH, {})

    mes_ref = descobrir_mes(metas)

    # Pega o mês correto. Se não existir, usa vazio.
    base_inicial_mes = google_inicial.get(mes_ref, {})

    # Pega meta do arquivo google_metamarço se existir.
    # Se não existir, usa a meta que já está dentro do metas_atual.json.
    base_meta_mes = google_meta.get(mes_ref, {})

    for cidade, info in metas.items():
        indicadores = info.setdefault("indicadores", {})

        google_ind = indicadores.setdefault("avaliacoes_google", {
            "meta": "-",
            "ate_o_momento": "-",
            "falta": "-",
            "progresso": "-"
        })

        inicial = extrair_numero(buscar_por_cidade(base_inicial_mes, cidade))
        atual_total = extrair_numero(buscar_por_cidade(google_atual, cidade))

        # Primeiro tenta pegar meta no google_metamarço
        meta_mes = extrair_numero(buscar_por_cidade(base_meta_mes, cidade))

        # Se não tiver meta no google_metamarço, usa a meta já existente no metas_atual.json
        if meta_mes is None:
            meta_mes = extrair_numero(google_ind.get("meta"))

        if meta_mes is not None:
            google_ind["meta"] = formatar_int(meta_mes)

        # Se não tiver valor inicial ou atual, não calcula
        if atual_total is None or inicial is None:
            google_ind["ate_o_momento"] = "0"
            google_ind["falta"] = formatar_int(meta_mes) if meta_mes is not None else "-"
            google_ind["progresso"] = "0,00%"
            indicadores["avaliacoes_google"] = google_ind
            continue

        realizado_mes = max(atual_total - inicial, 0)

        if meta_mes is None or meta_mes <= 0:
            falta = "-"
            progresso = "-"
        else:
            falta = max(meta_mes - realizado_mes, 0)
            progresso = (realizado_mes / meta_mes) * 100

        google_ind["ate_o_momento"] = formatar_int(realizado_mes)
        google_ind["falta"] = formatar_int(falta) if falta != "-" else "-"
        google_ind["progresso"] = formatar_percentual(progresso) if progresso != "-" else "-"

        indicadores["avaliacoes_google"] = google_ind

    salvar_json(METAS_PATH, metas)

    print(f"Google integrado ao metas_atual.json com base em {mes_ref}.")


if __name__ == "__main__":
    main()
