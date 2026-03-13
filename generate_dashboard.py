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
        return 0
    valor = str(valor).replace("%", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0


def gerar_ranking(cidades, indicador):
    ranking = []

    for cidade, dados in cidades.items():
        ind = dados["indicadores"].get(indicador, {})
        p = percentual(ind.get("progresso"))
        ranking.append((cidade, p, ind))

    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking


def metas_batidas(cidades):

    resultado = []

    for cidade, dados in cidades.items():
        for nome, ind in dados["indicadores"].items():
            p = percentual(ind.get("progresso"))

            if p >= 100:
                resultado.append({
                    "cidade": cidade,
                    "indicador": nome,
                    "progresso": ind.get("progresso")
                })

    return resultado


def card_servico(nome, dados):

    progresso = dados.get("progresso", "0%")
    meta = dados.get("meta", "-")
    realizado = dados.get("ate_o_momento", "-")
    falta = dados.get("falta", "-")

    p = percentual(progresso)
    largura = min(p, 100)

    return f"""
    <div class="service-card">

        <div class="service-header">
            <span>{nome}</span>
            <span>{progresso}</span>
        </div>

        <div class="bar">
            <div class="fill" style="width:{largura}%"></div>
        </div>

        <div class="numbers">
            Meta: {meta} |
            Realizado: {realizado} |
            Falta: {falta}
        </div>

    </div>
    """


def card_financeiro(nome, dados):

    progresso = dados.get("progresso", "0%")
    meta = dados.get("meta", "-")
    realizado = dados.get("ate_o_momento", "-")
    falta = dados.get("falta", "-")

    return f"""
    <div class="finance-card">

        <h3>{nome}</h3>

        <div class="big">{progresso}</div>

        <div>Meta: {meta}</div>
        <div>Realizado: {realizado}</div>
        <div>Falta: {falta}</div>

    </div>
    """


def gerar_dashboard():

    dados = carregar_dados()

    cidades = list(dados.keys())

    ranking_orto = gerar_ranking(dados, "ortodontia")
    ranking_clinico = gerar_ranking(dados, "clinico_geral")

    metas = metas_batidas(dados)

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">
<title>Dashboard de Metas</title>

<style>

body {{
    font-family: Arial;
    background:#081421;
    color:white;
    margin:0;
}}

.header {{
    padding:20px;
    background:#06101c;
}}

.container {{
    padding:20px;
}}

.cards {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:20px;
}}

.finance-card {{
    background:#0e1f33;
    padding:20px;
    border-radius:10px;
}}

.service-card {{
    background:#0e1f33;
    padding:20px;
    border-radius:10px;
}}

.bar {{
    background:#111;
    height:10px;
    border-radius:10px;
}}

.fill {{
    background:#00e0a4;
    height:10px;
    border-radius:10px;
}}

.rank-item {{
    padding:10px;
    border-bottom:1px solid #1c2d44;
}}

.big {{
    font-size:28px;
    color:#00e0a4;
}}

.city {{
    margin-top:40px;
}}

</style>

</head>

<body>

<div class="header">

<h1>Dashboard de Metas</h1>

Atualizado: {agora}

</div>

<div class="container">


<h2>Metas Batidas</h2>

"""

    for m in metas:

        html += f"""
<div class="rank-item">
{m["cidade"]} - {m["indicador"]} - {m["progresso"]}
</div>
"""

    html += """
<h2>Ranking Ortodontia</h2>
"""

    for pos, item in enumerate(ranking_orto, start=1):

        cidade, p, dados = item

        html += f"""
<div class="rank-item">
{pos} - {cidade} - {dados.get("progresso")}
</div>
"""

    html += """
<h2>Ranking Clínico Geral</h2>
"""

    for pos, item in enumerate(ranking_clinico, start=1):

        cidade, p, dados = item

        html += f"""
<div class="rank-item">
{pos} - {cidade} - {dados.get("progresso")}
</div>
"""

    for cidade, dados in dados.items():

        ind = dados["indicadores"]

        html += f"""
<div class="city">

<h2>{cidade}</h2>

<div class="cards">

{card_financeiro("Ortodontia", ind.get("ortodontia", {}))}
{card_financeiro("Clínico Geral", ind.get("clinico_geral", {}))}

</div>

<div class="cards">

{card_servico("Avaliações Google", ind.get("avaliacoes_google", {}))}
{card_servico("Meta Avaliação", ind.get("meta_avaliacao", {}))}
{card_servico("Meta Profilaxia", ind.get("meta_profilaxia", {}))}
{card_servico("Meta Restauração", ind.get("meta_restauracao", {}))}

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
