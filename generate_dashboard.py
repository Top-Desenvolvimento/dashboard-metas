import json
import os
from datetime import datetime

INPUT_JSON = "data/metas_atual.json"
OUTPUT_HTML = "docs/index.html"


MAPA_INDICADORES = {
    "ortodontia": "Ortodontia",
    "clinico_geral": "Clínico Geral",
    "avaliacoes_google": "Avaliações Google",
    "meta_avaliacao": "Meta de Avaliação",
    "meta_profilaxia": "Meta de Profilaxia",
    "meta_restauracao": "Meta de Restauração"
}


INDICADORES = [
    "ortodontia",
    "clinico_geral",
    "avaliacoes_google",
    "meta_avaliacao",
    "meta_profilaxia",
    "meta_restauracao"
]


def carregar_dados():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def percentual(valor):
    if not valor:
        return None

    texto = str(valor).replace("%", "").replace(",", ".").strip()

    try:
        return float(texto)
    except:
        return None


def classe_percentual(p):

    if p is None:
        return "empty"

    if p >= 100:
        return "ok"      # verde

    if p >= 50:
        return "warn"    # amarelo

    return "bad"         # vermelho


def gerar_ranking(dados, indicador):

    ranking = []

    for cidade, info in dados.items():

        ind = info["indicadores"].get(indicador, {})

        p = percentual(ind.get("progresso"))

        ranking.append((cidade, p, ind))

    ranking.sort(key=lambda x: (x[1] is None, -(x[1] or 0)))

    return ranking


def metas_batidas(dados):

    lista = []

    for cidade, info in dados.items():

        for chave, ind in info["indicadores"].items():

            p = percentual(ind.get("progresso"))

            if p and p >= 100:

                lista.append(
                    f"{cidade} — {MAPA_INDICADORES[chave]} {ind.get('progresso')}"
                )

    return lista


def render_ranking(nome, ranking):

    linhas = []

    for pos, item in enumerate(ranking, start=1):

        cidade, p, ind = item

        classe = classe_percentual(p)

        progresso = ind.get("progresso", "—")

        linhas.append(f"""
        <div class="rank-row">
            <div class="rank-pos">{pos}</div>
            <div class="rank-city">{cidade}</div>
            <div class="rank-progress {classe}">{progresso}</div>
        </div>
        """)

    return f"""
    <div class="panel">
        <div class="panel-title">{nome}</div>
        {''.join(linhas)}
    </div>
    """


def tabela_cidade(indicadores):

    linhas = []

    for chave in INDICADORES:

        ind = indicadores.get(chave, {})

        p = percentual(ind.get("progresso"))

        classe = classe_percentual(p)

        linhas.append(f"""
        <tr>
            <td>{MAPA_INDICADORES[chave]}</td>
            <td>{ind.get("meta","—")}</td>
            <td>{ind.get("ate_o_momento","—")}</td>
            <td>{ind.get("falta","—")}</td>
            <td class="{classe}">{ind.get("progresso","—")}</td>
        </tr>
        """)

    return f"""
    <table class="tabela">
    <tr>
    <th>Indicador</th>
    <th>Meta</th>
    <th>Até o momento</th>
    <th>Falta</th>
    <th>Progresso</th>
    </tr>
    {''.join(linhas)}
    </table>
    """


def gerar_dashboard():

    dados = carregar_dados()

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    cidades = sorted(dados.keys())

    tabs = []

    conteudo = []

    tabs.append('<button class="tab active" data-tab="ranking">Ranking</button>')

    ranking_cards = []

    for indicador in INDICADORES:

        ranking = gerar_ranking(dados, indicador)

        ranking_cards.append(
            render_ranking(MAPA_INDICADORES[indicador], ranking)
        )

    batidas = metas_batidas(dados)

    conteudo.append(f"""
    <div id="ranking" class="tab-content active">

    <div class="top">

    <div class="box">
    <h3>Unidades</h3>
    <div class="big">{len(cidades)}</div>
    </div>

    <div class="box">
    <h3>Metas Batidas</h3>
    {"<br>".join(batidas) if batidas else "Nenhuma meta acima de 100%"}
    </div>

    </div>

    <div class="grid">
    {''.join(ranking_cards)}
    </div>

    </div>
    """)

    for cidade in cidades:

        tabs.append(
            f'<button class="tab" data-tab="{cidade}">{cidade}</button>'
        )

        indicadores = dados[cidade]["indicadores"]

        conteudo.append(f"""
        <div id="{cidade}" class="tab-content">

        <h2>{cidade}</h2>

        {tabela_cidade(indicadores)}

        </div>
        """)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<title>Dashboard de Metas</title>

<style>

body {{
background:#06111c;
color:white;
font-family:Arial;
padding:30px;
}}

.tab {{
background:#0d1e31;
border:none;
padding:10px 18px;
margin:5px;
cursor:pointer;
color:#7f93a8;
}}

.tab.active {{
color:#00e8ff;
}}

.tab-content {{
display:none;
}}

.tab-content.active {{
display:block;
}}

.grid {{
display:grid;
grid-template-columns:1fr 1fr;
gap:20px;
}}

.panel {{
background:#0d1e31;
padding:15px;
border-radius:10px;
}}

.panel-title {{
font-weight:bold;
margin-bottom:10px;
}}

.rank-row {{
display:flex;
justify-content:space-between;
padding:5px 0;
}}

.rank-pos {{
width:30px;
}}

.big {{
font-size:40px;
}}

.tabela {{
width:100%;
border-collapse:collapse;
}}

.tabela th,
.tabela td {{
padding:10px;
border-bottom:1px solid #223;
}}

.ok {{
color:#12d99f;
}}

.warn {{
color:#f5b301;
}}

.bad {{
color:#ff4d7a;
}}

</style>

</head>

<body>

<h1>Dashboard de Metas</h1>

<div>{agora}</div>

<div>

{''.join(tabs)}

</div>

{''.join(conteudo)}

<script>

document.querySelectorAll(".tab").forEach(btn=>{{

btn.onclick=()=>{{

document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"))
document.querySelectorAll(".tab-content").forEach(c=>c.classList.remove("active"))

btn.classList.add("active")

document.getElementById(btn.dataset.tab).classList.add("active")

}}

}})

</script>

</body>

</html>
"""

    os.makedirs("docs", exist_ok=True)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:

        f.write(html)

    print("Dashboard gerado com sucesso")


if __name__ == "__main__":

    gerar_dashboard()
