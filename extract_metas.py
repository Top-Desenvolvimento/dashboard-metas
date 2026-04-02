# (CÓDIGO COMPLETO AJUSTADO)

# 🔴 IMPORTANTE: só vou te mostrar as PARTES ALTERADAS
# porque o restante do seu script já está perfeito

# =========================================
# 🔥 NOVA FUNÇÃO: preservar Google manual
# =========================================

def carregar_google_existente(mes_ref):
    caminho = os.path.join(HISTORICO_DIR, f"metas_{mes_ref}.json")

    if not os.path.exists(caminho):
        return {}

    try:
        with open(caminho, encoding="utf-8") as f:
            dados_antigos = json.load(f)

        google_manual = {}

        for cidade, dados in dados_antigos.items():
            indicadores = dados.get("indicadores", {})
            if "avaliacoes_google" in indicadores:
                google_manual[cidade] = indicadores["avaliacoes_google"]

        return google_manual

    except Exception:
        return {}


# =========================================
# 🔥 ALTERAÇÃO NA FUNÇÃO salvar_historico
# =========================================
def carregar_google_existente(mes_ref):
    caminho = os.path.join(HISTORICO_DIR, f"metas_{mes_ref}.json")

    if not os.path.exists(caminho):
        return {}

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados_antigos = json.load(f)

        google_manual = {}

        for cidade, dados in dados_antigos.items():
            indicadores = dados.get("indicadores", {})
            if "avaliacoes_google" in indicadores:
                google_manual[cidade] = indicadores["avaliacoes_google"]

        return google_manual
    except Exception:
        return {}
def salvar_historico(resultado):
    os.makedirs(HISTORICO_DIR, exist_ok=True)

    meses = sorted({
        dados.get("mes_referencia")
        for dados in resultado.values()
        if dados.get("mes_referencia")
    })

    if not meses:
        mes_ref = obter_mes_referencia_json()
    else:
        mes_ref = meses[0]

    # ignora qualquer histórico antes de janeiro/2026
    if mes_ref < "2026-01":
        print(f"⛔ Ignorando histórico anterior a 2026: {mes_ref}")
        return

    # preserva o Google manual já salvo naquele mês
    google_antigo = carregar_google_existente(mes_ref)

    for cidade, dados in resultado.items():
        if cidade in google_antigo:
            dados["indicadores"]["avaliacoes_google"] = google_antigo[cidade]

    historico_path = os.path.join(HISTORICO_DIR, f"metas_{mes_ref}.json")
    with open(historico_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"Histórico mensal salvo em: {historico_path}")
