import json
import os
from datetime import datetime

INPUT_JSON = "data/metas_atual.json"
OUTPUT_HTML = "docs/index.html"


def carregar_dados():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def percentual(valor):
    if not valor:
        return 0.0
    texto = str(valor).replace("%", "").replace(",", ".").strip()
    try:
        return float(texto)
    except Exception:
        return 0.0


def texto_seguro(valor, padrao="—"):
    if valor is None:
        return padrao
    texto = str(valor).strip()
    return texto if texto else padrao


def gerar_ranking(base, indicador):
    ranking = []

    for cidade, info_cidade in base.items():
        ind = info_cidade.get("indicadores", {}).get(indicador, {})
        p = percentual(ind.get("progresso"))
        ranking.append((cidade, p, ind))

    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking


def metas_batidas(base):
    resultado = []

    for cidade, info_cidade in base.items():
        indicadores = info_cidade.get("indicadores", {})
        for nome, ind in indicadores.items():
            p = percentual(ind.get("progresso"))
            if p >= 100:
                resultado.append({
                    "cidade": cidade,
                    "indicador": nome,
                    "progresso": ind.get("progresso", "0%"),
                })

    return resultado


def nome_indicador(chave):
    mapa = {
        "ortodontia": "Ortodontia",
        "clinico_geral": "Clínico Geral",
        "avaliacoes_google": "Avaliações Google",
        "meta_avaliacao": "Meta de Avaliação",
        "meta_profilaxia": "Meta de Profilaxia",
        "meta_restauracao": "Meta de Restauração",
    }
    return mapa.get(chave, chave)


def card_servico(nome, dados_indicador):
    progresso = texto_seguro(dados_indicador.get("progresso"), "0%")
    meta = texto_seguro(dados_indicador.get("meta"))
    realizado = texto_seguro(dados_indicador.get("ate_o_momento"))
    falta = texto_seguro(dados_indicador.get("falta"))

    p = percentual(progresso)
    largura = min(max(p, 0), 100)

    cor = "#00e0a4"
    if p < 70:
        cor = "#ff4d7a"
    elif p < 100:
        cor = "#f3b51b"

    return f"""
    <div class="service-card">
        <div class="service-header">
            <span>{nome}</span>
            <span style="color:{cor};font-weight:bold;">{progresso}</span>
        </div>

        <div class="bar">
            <div class="fill" style="width:{largura}%; background:{cor};"></div>
        </div>

        <div class="numbers">
            Meta: {meta} |
            Realizado: {realizado} |
            Falta: {falta}
        </div>
    </div>
    """


def card_financeiro(nome, dados_indicador):
    progresso = texto_seguro(dados_indicador.get("progresso"), "0%")
    meta = texto_seguro(dados_indicador.get("meta"))
    realizado = texto_seguro(dados_indicador.get("ate_o_momento"))
    falta = texto_seguro(dados_indicador.get("falta"))

    p = percentual(progresso)
    cor = "#00e0a4"
    if p < 70:
        cor = "#ff4d7a"
    elif p < 100:
        cor = "#f3b51b"

    return f"""
    <div class="finance-card">
        <h3>{nome}</h3>
        <div class="big" style="color:{cor};">{progresso}</div>
        <div>Meta: {meta}</div>
        <div>Realizado: {realizado}</div>
        <div>Falta: {falta}</div>
    </div>
    """


def gerar_dashboard():
    base = carregar_dados()

    ranking_orto = gerar_ranking(base, "ortodontia")
    ranking_clinico = gerar_ranking(base, "clinico_geral")
    ranking_google = gerar_ranking(base, "avaliacoes_google")
    ranking_avaliacao = gerar_ranking(base, "meta_avaliacao")
    ranking_profilaxia = gerar_ranking(base, "meta_profilaxia")
    ranking_restauracao = gerar_ranking(base, "meta_restauracao")

    metas = metas_batidas(base)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard de Metas</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #081421;
    color: white;
    margin: 0;
}}

.header {{
    padding: 20px;
    background: #06101c;
}}

.container {{
    padding: 20px;
}}

.cards {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}}

.finance-card {{
    background: #0e1f33;
    padding: 20px;
    border-radius: 12px;
}}

.service-card {{
    background: #0e1f33;
    padding: 20px;
    border-radius: 12px;
}}

.bar {{
    background: #111;
    height: 10px;
    border-radius: 10px;
    margin: 10px 0;
}}

.fill {{
    height: 10px;
    border-radius: 10px;
}}

.rank-item {{
    padding: 10px;
    border-bottom: 1px solid #1c2d44;
}}

.big {{
    font-size: 28px;
    font-weight: bold;
}}

.city {{
    margin-top: 40px;
}}

.section-title {{
    margin-top: 30px;
    margin-bottom: 10px;
}}
</style>
</head>
<body>

<div class="header">
    <h1>Dashboard de Metas</h1>
    <div>Atualizado: {agora}</div>
</div>

<div class="container">
    <h2>Metas Batidas</h2>
"""

    if metas:
        for meta in metas:
            html += f"""
<div class="rank-item">
    {meta["cidade"]} - {nome_indicador(meta["indicador"])} - {meta["progresso"]}
</div>
"""
    else:
        html += """
<div class="rank-item">Nenhuma meta acima de 100%.</div>
"""

    def render_ranking(titulo, ranking):
        bloco = f"<h2 class='section-title'>{titulo}</h2>"
        for pos, item in enumerate(ranking, start=1):
            cidade, _, dados_ind = item
            bloco += f"""
<div class="rank-item">
    {pos} - {cidade} - {texto_seguro(dados_ind.get("progresso"))}
</div>
"""
        return bloco

    html += render_ranking("Ranking Ortodontia", ranking_orto)
    html += render_ranking("Ranking Clínico Geral", ranking_clinico)
    html += render_ranking("Ranking Avaliações Google", ranking_google)
    html += render_ranking("Ranking Meta de Avaliação", ranking_avaliacao)
    html += render_ranking("Ranking Meta de Profilaxia", ranking_profilaxia)
    html += render_ranking("Ranking Meta de Restauração", ranking_restauracao)

    for cidade, info_cidade in base.items():
        indicadores = info_cidade.get("indicadores", {})

        html += f"""
<div class="city">
    <h2>{cidade}</h2>

    <div class="cards">
        {card_financeiro("Ortodontia", indicadores.get("ortodontia", {}))}
        {card_financeiro("Clínico Geral", indicadores.get("clinico_geral", {}))}
    </div>

    <div class="cards">
        {card_servico("Avaliações Google", indicadores.get("avaliacoes_google", {}))}
        {card_servico("Meta de Avaliação", indicadores.get("meta_avaliacao", {}))}
        {card_servico("Meta de Profilaxia", indicadores.get("meta_profilaxia", {}))}
        {card_servico("Meta de Restauração", indicadores.get("meta_restauracao", {}))}
    </div>
</div>
"""

    html += """
</div>
</body>
</html>
"""

    os.makedirs("docs", exist_ok=True)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("Dashboard gerado com sucesso.")


if __name__ == "__main__":
    gerar_dashboard()
