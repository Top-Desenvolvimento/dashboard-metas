import json
import os
import re
from datetime import datetime

GOOGLE_MANUAL_FILE = "data/google_manual.json"
METAS_ATUAL_FILE = "data/metas_atual.json"
HISTORICO_DIR = "data/historico"

MESES_PT_REV = {
    "janeiro": "01",
    "fevereiro": "02",
    "março": "03",
    "marco": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12",
}


def normalizar_texto(texto):
    texto = str(texto or "").strip().lower()
    trocas = {
        "ã": "a", "á": "a", "à": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for a, b in trocas.items():
        texto = texto.replace(a, b)
    return re.sub(r"\s+", " ", texto)


def mes_env_para_json(valor):
    if valor and valor != "AUTO":
        valor = valor.strip()

        if re.match(r"^\d{4}-\d{2}$", valor):
            return valor

        mm_yyyy = re.match(r"^(\d{2})/(\d{4})$", valor)
        if mm_yyyy:
            return f"{mm_yyyy.group(2)}-{mm_yyyy.group(1)}"

        mes_nome = re.match(r"^([A-Za-zÀ-ÿçÇ]+)\s*/\s*(\d{4})$", valor)
        if mes_nome:
            nome = normalizar_texto(mes_nome.group(1))
            ano = mes_nome.group(2)
            mes = MESES_PT_REV.get(nome)
            if mes:
                return f"{ano}-{mes}"

    return datetime.now().strftime("%Y-%m")


def numero(valor):
    if valor is None:
        return 0.0

    texto = str(valor).strip()
    if not texto:
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


def montar_indicador_google(info):
    valor_atual = str(info.get("valor_atual", "-"))
    valor_meta = numero(info.get("valor_meta", 0))
    valor_atingido = numero(info.get("valor_atingido_mes", 0))

    falta = valor_meta - valor_atingido

    progresso = 0.0
    if valor_meta > 0:
        progresso = (valor_atingido / valor_meta) * 100

    return {
        "meta": br(valor_meta, 0),
        "ate_o_momento": br(valor_atingido, 0),
        "falta": br(falta, 0),
        "progresso": f"{progresso:.2f}%".replace(".", ","),
        "valor_atual": valor_atual
    }


def aplicar_google_em_base(base, google_mes, mes_ref):
    alterados = 0

    for cidade, info_cidade in base.items():
        if cidade not in google_mes:
            print(f"ℹ️ Sem Google manual para {cidade} em {mes_ref}")
            continue

        if "indicadores" not in info_cidade:
            info_cidade["indicadores"] = {}

        info_cidade["indicadores"]["avaliacoes_google"] = montar_indicador_google(
            google_mes[cidade]
        )

        alterados += 1
        print(f"✅ Google aplicado em {cidade}")

    return alterados


def main():
    mes_ref = mes_env_para_json(os.getenv("MES_REFERENCIA", "AUTO"))

    print("=" * 55)
    print("Aplicando Google manual")
    print(f"Mês referência: {mes_ref}")
    print(f"Arquivo Google: {GOOGLE_MANUAL_FILE}")
    print("=" * 55)

    google = carregar_json(GOOGLE_MANUAL_FILE)

    if not google:
        raise FileNotFoundError(f"Arquivo não encontrado ou vazio: {GOOGLE_MANUAL_FILE}")

    google_mes = google.get(mes_ref)

    if not google_mes:
        raise ValueError(
            f"Não encontrei o mês {mes_ref} dentro de {GOOGLE_MANUAL_FILE}. "
            f"Meses disponíveis: {list(google.keys())}"
        )

    caminho_historico = os.path.join(HISTORICO_DIR, f"metas_{mes_ref}.json")

    total_alterados = 0

    metas_atual = carregar_json(METAS_ATUAL_FILE)
    if metas_atual:
        total_alterados += aplicar_google_em_base(metas_atual, google_mes, mes_ref)
        salvar_json(METAS_ATUAL_FILE, metas_atual)
        print(f"📌 Atualizado: {METAS_ATUAL_FILE}")
    else:
        print(f"⚠️ Não encontrei {METAS_ATUAL_FILE}")

    historico = carregar_json(caminho_historico)
    if historico:
        total_alterados += aplicar_google_em_base(historico, google_mes, mes_ref)
        salvar_json(caminho_historico, historico)
        print(f"📌 Atualizado: {caminho_historico}")
    else:
        print(f"⚠️ Não encontrei {caminho_historico}")

    print(f"Finalizado. Blocos Google aplicados: {total_alterados}")


if __name__ == "__main__":
    main()
