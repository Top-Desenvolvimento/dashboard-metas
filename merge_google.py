import json
import os
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

METAS_PATH = "data/metas_atual.json"
GOOGLE_INICIAL_PATH = "data/google_inicial.json"
GOOGLE_ATUAL_PATH = "data/google_atual.json"
HISTORICO_DIR = "data/historico"


def carregar_json(path, default):
    if not os.path.exists(path):
        print(f"Arquivo não encontrado: {path}")
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
        return 0
    if isinstance(valor, dict):
        for chave in ["valor_atual", "atual", "valor", "avaliacoes", "total", "inicial"]:
            if chave in valor:
                return extrair_numero(valor.get(chave))
        return 0
    texto = str(valor).strip()
    if texto == "" or texto == "-":
        return 0
    numeros = re.findall(r"\d+", texto)
    if not numeros:
        return 0
    return int("".join(numeros))


def formatar_percentual(valor):
    return f"{valor:.2f}%".replace(".", ",")


def descobrir_mes(metas):
    for _, info in metas.items():
        mes = info.get("mes_referencia")
        if mes:
            return mes
    mes_env = os.getenv("MES_REFERENCIA", "").strip()
    if mes_env and mes_env != "AUTO":
        return mes_env
    return datetime.now(TZ).strftime("%Y-%m")


def calcular_google(meta, inicial, atual):
    realizado = atual - inicial
    if realizado < 0:
        realizado = 0
    falta = meta - realizado
    if falta < 0:
        falta = 0
    progresso = 0
    if meta > 0:
        progresso = (realizado / meta) * 100
    return {
        "meta": str(meta),
        "ate_o_momento": str(realizado),
        "falta": str(falta),
        "progresso": formatar_percentual(progresso),
        "valor_inicial": str(inicial),
        "valor_atual": str(atual)
    }


def atualizar_historico(mes_ref, metas):
    """
    generate_dashboard.py lê os arquivos de data/historico/metas_AAAA-MM.json
    como fonte principal (inclusive para o mês atual) - não o metas_atual.json.
    Por isso o merge_google.py precisa gravar o resultado recalculado também
    no histórico do mês corrente, ou o site nunca vê a correção.
    """
    historico_path = os.path.join(HISTORICO_DIR, f"metas_{mes_ref}.json")
    if not os.path.exists(historico_path):
        print(f"⚠️ Histórico de {mes_ref} não encontrado em {historico_path} — nada a atualizar lá.")
        return
    salvar_json(historico_path, metas)
    print(f"📦 Histórico do mês {mes_ref} atualizado com os dados do Google em: {historico_path}")


def main():
    metas = carregar_json(METAS_PATH, {})
    google_inicial = carregar_json(GOOGLE_INICIAL_PATH, {})
    google_atual = carregar_json(GOOGLE_ATUAL_PATH, {})

    mes_ref = descobrir_mes(metas)
    base_inicial = google_inicial.get(mes_ref, {})

    print("=" * 60)
    print("MERGE GOOGLE")
    print(f"Mês referência: {mes_ref}")
    print(f"Meses disponíveis no google_inicial: {list(google_inicial.keys())}")
    print("=" * 60)

    for cidade, info in metas.items():
        indicadores = info.setdefault("indicadores", {})
        google_existente = indicadores.setdefault("avaliacoes_google", {
            "meta": "0",
            "ate_o_momento": "0",
            "falta": "0",
            "progresso": "0,00%",
            "valor_inicial": "0",
            "valor_atual": "0"
        })

        meta = extrair_numero(google_existente.get("meta"))
        inicial = extrair_numero(buscar_por_cidade(base_inicial, cidade))
        atual = extrair_numero(buscar_por_cidade(google_atual, cidade))

        if inicial <= 0 or atual <= 0:
            google_existente["ate_o_momento"] = "0"
            google_existente["falta"] = str(meta) if meta else "0"
            google_existente["progresso"] = "0,00%"
            google_existente["valor_inicial"] = str(inicial)
            google_existente["valor_atual"] = str(atual)
            print(f"{cidade}: NÃO CALCULADO | inicial={inicial} | atual={atual} | meta={meta}")
            continue

        indicadores["avaliacoes_google"] = calcular_google(meta, inicial, atual)
        print(
            f"{cidade}: inicial={inicial} | atual={atual} | "
            f"realizado={atual - inicial} | meta={meta}"
        )

    salvar_json(METAS_PATH, metas)
    atualizar_historico(mes_ref, metas)

    print("=" * 60)
    print("Google integrado ao metas_atual.json (e ao histórico do mês) com sucesso.")
    print("=" * 60)


if __name__ == "__main__":
    main()
