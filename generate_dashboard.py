import json
import os
import re
from datetime import datetime

ARQUIVO_JSON = "data/metas_atual.json"
ARQUIVO_HTML = "docs/index.html"

MAPA_INDICADORES = {
    "ortodontia": "Ortodontia",
    "clinico_geral": "Clínico Geral",
    "avaliacoes_google": "Avaliações Google",
    "meta_avaliacao": "Meta de Avaliação",
    "meta_profilaxia": "Meta de Profilaxia",
    "meta_restauracao": "Meta de Restauração",
}

ORDEM_INDICADORES = [
    "ortodontia",
    "clinico_geral",
    "avaliacoes_google",
    "meta_avaliacao",
    "meta_profilaxia",
    "meta_restauracao",
]


def carregar_dados():
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def slug(texto):
    texto = texto.lower()
    mapa = {
        "ã": "a", "á": "a", "à": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for a, b in mapa.items():
        texto = texto.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")


def texto_seguro(valor, padrao="—"):
    if valor is None:
        return padrao
    texto = str(valor).strip()
    return texto if texto else padrao


def percentual(valor):
    if not valor:
        return None
    texto = str(valor).replace("%", "").replace(",", ".").strip()
    try:
        return float(texto)
    except Exception:
        return None


def classe_percentual(p):
    if p is None:
        return "empty"
    if p >= 100:
        return "ok"
    if p >= 70:
        return "warn"
    return "bad"


def largura_barra(p):
    if p is None:
        return 0
    return max(0, min(p, 100))


def mes_label(valor):
    if not valor:
        return datetime.now().strftime("%m/%Y")
    mapa = {
        "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
        "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
        "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro",
    }
    try:
        ano, mes = valor.split("-")
        return f"{mapa.get(mes, mes)}/{ano}"
    except Exception:
        return valor


def progresso_geral(info_cidade):
    indicadores = info_cidade.get("indicadores", {})
    valores = []
    for chave in ORDEM_INDICADORES:
        p = percentual(indicadores.get(chave, {}).get("progresso"))
        if p is not None:
            valores.append(p)
    if not valores:
        return None
    return sum(valores) / len(valores)


def gerar_ranking(base, indicador):
    ranking = []
    for cidade, info_cidade in base.items():
        ind = info_cidade.get("indicadores", {}).get(indicador, {})
        p = percentual(ind.get("progresso"))
        ranking.append((cidade, p, ind))
    ranking.sort(key=lambda x: (x[1] is None, -(x[1] or 0), x[0]))
    return ranking


def metas_batidas(base):
    resultado = []
    for cidade, info_cidade in base.items():
        indicadores = info_cidade.get("indicadores", {})
        for nome, ind in indicadores.items():
            p = percentual(ind.get("progresso"))
            if p is not None and p >= 100:
                resultado.append({
                    "cidade": cidade,
                    "indicador": MAPA_INDICADORES.get(nome, nome),
                    "progresso": texto_seguro(ind.get("progresso")),
                    "percentual_num": p,
                })
    resultado.sort(key=lambda x: (-x["percentual_num"], x["cidade"], x["indicador"]))
    return resultado


def render_ranking_card(titulo, ranking):
    linhas = []
    for pos, item in enumerate(ranking, start=1):
        cidade, p, dados = item
        status = classe_percentual(p)
        largura = largura_barra(p)

        badge = "pos-other"
        if pos == 1:
            badge = "pos-1"
        elif pos == 2:
            badge = "pos-2"
        elif pos == 3:
            badge = "pos-3"

        linhas.append(f"""
        <div class="rank-row">
            <div class="rank-left">
                <div class="rank-pos {badge}">{pos}</div>
                <div class="rank-city">{cidade}</div>
            </div>
            <div class="rank-mid">
                <div class="rank-bar">
                    <div class="rank-fill {status}" style="width:{largura}%"></div>
                </div>
            </div>
            <div class="rank-right">
                <div class="rank-progress {status}">{texto_seguro(dados.get("progresso"))}</div>
                <div class="rank-value">{texto_seguro(dados.get("ate_o_momento"))}</div>
            </div>
        </div>
        """)

    return f"""
    <section class="panel">
        <div class="panel-header">
            <div class="panel-title">{titulo}</div>
        </div>
        <div class="panel-body">
            {''.join(linhas)}
        </div>
    </section>
    """


def render_city_table(indicadores):
    linhas = []

    for chave in ORDEM_INDICADORES:
        ind = indicadores.get(chave, {})
        p = percentual(ind.get("progresso"))
        status = classe_percentual(p)

        linhas.append(f"""
        <tr>
            <td class="td-title">{MAPA_INDICADORES[chave]}</td>
            <td>{texto_seguro(ind.get("meta"))}</td>
            <td>{texto_seguro(ind.get("ate_o_momento"))}</td>
            <td>{texto_seguro(ind.get("falta"))}</td>
            <td class="{status}">{texto_seguro(ind.get("progresso"))}</td>
        </tr>
        """)

    return f"""
    <div class="table-wrap">
        <table class="dash-table">
            <thead>
                <tr>
                    <th>Indicador</th>
                    <th>Meta</th>
                    <th>Até o momento</th>
                    <th>Falta</th>
                    <th>Progresso</th>
                </tr>
            </thead>
            <tbody>
                {''.join(linhas)}
            </tbody>
        </table>
    </div>
    """


def gerar_dashboard():
    base = carregar_dados()
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    cidades_ordenadas = sorted(
        base.items(),
        key=lambda item: (
            progresso_geral(item[1]) is None,
            -(progresso_geral(item[1]) or 0),
            item[0]
        )
    )

    mes_ref = ""
    if cidades_ordenadas:
        mes_ref = mes_label(cidades_ordenadas[0][1].get("mes_referencia", ""))

    tabs = ['<button class="tab-btn active" data-tab="ranking-geral">🏆 Ranking Geral</button>']
    for cidade, _ in cidades_ordenadas:
        tabs.append(f'<button class="tab-btn" data-tab="{slug(cidade)}">📍 {cidade}</button>')

    batidas = metas_batidas(base)

    ranking_cards = []
    for chave in ORDEM_INDICADORES:
        ranking_cards.append(
            render_ranking_card(MAPA_INDICADORES[chave], gerar_ranking(base, chave))
        )

    if batidas:
        batidas_html = []
        agrupado = {}
        for item in batidas:
            agrupado.setdefault(item["cidade"], []).append(item)

        for cidade, itens in agrupado.items():
            linhas = []
            for item in itens:
                linhas.append(f"""
                <div class="hit-line">
                    <span>✓ {item["indicador"]}</span>
                    <strong class="blink">{item["progresso"]}</strong>
                </div>
                """)
            batidas_html.append(f"""
            <div class="hit-card">
                <div class="hit-city">{cidade}</div>
                {''.join(linhas)}
            </div>
            """)
        bloco_batidas = "".join(batidas_html)
    else:
        bloco_batidas = '<div class="empty-message">Nenhuma meta acima de 100% no momento.</div>'

    cidades_html = []
    for cidade, info_cidade in cidades_ordenadas:
        indicadores = info_cidade.get("indicadores", {})
        pg = progresso_geral(info_cidade)
        pg_txt = f"{pg:.1f}%".replace(".", ",") if pg is not None else "—"

        cidades_html.append(f"""
        <div id="{slug(cidade)}" class="tab-content">
            <section class="summary-grid">
                <div class="summary-card">
                    <div class="summary-label">Cidade</div>
                    <div class="summary-value">{cidade}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Mês de Referência</div>
                    <div class="summary-value">{mes_label(info_cidade.get("mes_referencia", ""))}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Progresso Geral</div>
                    <div class="summary-value alt">{pg_txt}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Atualizado</div>
                    <div class="summary-value alt2">{agora}</div>
                </div>
            </section>

            <section class="panel">
                <div class="panel-header">
                    <div class="panel-title">Indicadores da Cidade</div>
                </div>
                {render_city_table(indicadores)}
            </section>
        </div>
        """)

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard de Metas</title>
<style>
:root {{
    --bg: #030a12;
    --panel: rgba(7, 19, 32, 0.95);
    --panel2: rgba(4, 14, 24, 0.95);
    --border: rgba(0, 232, 255, 0.14);
    --line: rgba(255,255,255,0.06);
    --text: #eaf7ff;
    --muted: #7f93a8;
    --cyan: #00e8ff;
    --green: #12d99f;
    --yellow: #f5b301;
    --red: #ff4d7a;
    --shadow: 0 0 0 1px rgba(0,232,255,.07), 0 10px 30px rgba(0,0,0,.35);
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: Inter, Arial, sans-serif;
    background:
        radial-gradient(circle at top left, rgba(0,232,255,.10), transparent 28%),
        radial-gradient(circle at top right, rgba(18,217,159,.08), transparent 25%),
        linear-gradient(180deg, #01050b, #06111c 45%, #02070d 100%);
    color: var(--text);
    min-height: 100vh;
}}

.wrap {{
    max-width: 1500px;
    margin: 0 auto;
    padding: 18px;
}}

.header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 18px;
    padding: 8px 0 20px;
}}

.header-left h1 {{
    font-size: 2.8rem;
    font-weight: 900;
}}

.header-left p {{
    margin-top: 8px;
    color: var(--muted);
}}

.header-right {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
}}

.pill {{
    padding: 14px 18px;
    border-radius: 14px;
    background: rgba(7, 19, 32, 0.86);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    font-weight: 700;
}}

.pill.btn {{
    color: #031018;
    text-decoration: none;
    background: linear-gradient(135deg, rgba(0,232,255,.95), rgba(18,217,159,.95));
}}

.tabs {{
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 10px 0 16px;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    margin-bottom: 18px;
}}

.tab-btn {{
    background: transparent;
    color: var(--muted);
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 14px;
    cursor: pointer;
    white-space: nowrap;
    font-weight: 700;
}}

.tab-btn.active {{
    color: var(--cyan);
    border-color: rgba(0,232,255,.30);
    background: rgba(0,232,255,.08);
}}

.tab-content {{
    display: none;
}}

.tab-content.active {{
    display: block;
}}

.top-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
}}

.panel, .summary-card {{
    background: linear-gradient(180deg, var(--panel), var(--panel2));
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: var(--shadow);
}}

.panel {{
    padding: 16px;
    margin-bottom: 18px;
}}

.panel-header {{
    margin-bottom: 12px;
}}

.panel-title {{
    font-size: 1.1rem;
    font-weight: 900;
}}

.hit-card {{
    padding: 12px 0;
    border-top: 1px solid rgba(255,255,255,.05);
}}

.hit-card:first-child {{
    border-top: none;
}}

.hit-city {{
    color: var(--green);
    font-size: 1.3rem;
    font-weight: 900;
    margin-bottom: 8px;
}}

.hit-line {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: #bfe8ef;
    padding: 4px 0;
}}

.empty-message {{
    color: var(--muted);
}}

.rankings-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}}

.rank-row {{
    display: grid;
    grid-template-columns: 180px 1fr 120px;
    gap: 14px;
    align-items: center;
    padding: 12px 0;
    border-top: 1px solid rgba(255,255,255,.05);
}}

.rank-row:first-child {{
    border-top: none;
}}

.rank-left {{
    display: flex;
    align-items: center;
    gap: 10px;
}}

.rank-pos {{
    width: 34px;
    height: 34px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    background: rgba(255,255,255,.08);
}}

.pos-1 {{ background: rgba(245,179,1,.20); color: #ffd45c; }}
.pos-2 {{ background: rgba(180,196,210,.20); color: #dbe6ef; }}
.pos-3 {{ background: rgba(165,102,38,.20); color: #ffb56d; }}
.pos-other {{ color: #fff; }}

.rank-city {{
    font-weight: 800;
}}

.rank-bar {{
    height: 10px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(255,255,255,.05);
}}

.rank-fill {{
    height: 100%;
    border-radius: 999px;
}}

.rank-fill.ok {{ background: linear-gradient(90deg, #12d99f, #08f0c2); }}
.rank-fill.warn {{ background: linear-gradient(90deg, #f0a500, #f7c52b); }}
.rank-fill.bad {{ background: linear-gradient(90deg, #ff4d7a, #ff6a91); }}
.rank-fill.empty {{ background: #223345; }}

.rank-right {{
    text-align: right;
}}

.rank-progress {{
    font-weight: 900;
}}

.rank-value {{
    color: var(--muted);
    margin-top: 4px;
}}

.summary-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 18px;
}}

.summary-card {{
    padding: 18px;
}}

.summary-label {{
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .08em;
    font-size: .82rem;
    margin-bottom: 12px;
}}

.summary-value {{
    color: var(--cyan);
    font-size: 1.9rem;
    font-weight: 900;
}}

.summary-value.alt {{
    color: var(--yellow);
}}

.summary-value.alt2 {{
    color: var(--green);
}}

.table-wrap {{
    overflow-x: auto;
}}

.dash-table {{
    width: 100%;
    border-collapse: collapse;
}}

.dash-table th,
.dash-table td {{
    text-align: left;
    padding: 14px 12px;
    border-top: 1px solid rgba(255,255,255,.05);
}}

.dash-table th {{
    color: var(--muted);
    text-transform: uppercase;
    font-size: .82rem;
    letter-spacing: .05em;
}}

.td-title {{
    font-weight: 800;
}}

.ok {{
    color: var(--green);
    font-weight: 900;
}}

.warn {{
    color: var(--yellow);
    font-weight: 900;
}}

.bad {{
    color: var(--red);
    font-weight: 900;
}}

.empty {{
    color: var(--muted);
    font-weight: 700;
}}

@keyframes pulse {{
    0%,100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: .35; transform: scale(1.03); }}
}}

.blink {{
    animation: pulse 1.2s infinite;
}}

@media (max-width: 1200px) {{
    .top-grid,
    .rankings-grid,
    .summary-grid {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 860px) {{
    .header {{
        flex-direction: column;
    }}

    .header-left h1 {{
        font-size: 2.1rem;
    }}

    .rank-row {{
        grid-template-columns: 1fr;
    }}

    .rank-right {{
        text-align: left;
    }}
}}
</style>
</head>
<body>
<div class="wrap">

    <header class="header">
        <div class="header-left">
            <h1>Dashboard de Metas</h1>
            <p>Top Estética Bucal — {len(cidades_ordenadas)} Unidades</p>
        </div>
        <div class="header-right">
            <div class="pill">{mes_ref}</div>
            <div class="pill">{agora}</div>
            <div class="pill">● Online</div>
            <a class="pill btn" href="../data/metas_top_estetica.xlsx" download>⬇ Exportar Planilha</a>
        </div>
    </header>

    <nav class="tabs">
        {''.join(tabs)}
    </nav>

    <div id="ranking-geral" class="tab-content active">
        <section class="top-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Unidades</div>
                </div>
                <div style="font-size:3rem; color:var(--cyan); font-weight:900;">{len(cidades_ordenadas)}</div>
                <div style="margin-top:8px; color:var(--muted);">cidades monitoradas</div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Metas Batidas por Cidade</div>
                </div>
                {bloco_batidas}
            </div>
        </section>

        <section class="rankings-grid">
            {''.join(ranking_cards)}
        </section>
    </div>

    {''.join(cidades_html)}

</div>

<script>
const buttons = document.querySelectorAll('.tab-btn');
const contents = document.querySelectorAll('.tab-content');

buttons.forEach(btn => {{
    btn.addEventListener('click', () => {{
        buttons.forEach(b => b.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');

        const target = document.getElementById(btn.dataset.tab);
        if (target) {{
            target.classList.add('active');
        }}
    }});
}});
</script>
</body>
</html>
"""

    os.makedirs("docs", exist_ok=True)
    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("Dashboard gerado com sucesso.")


if __name__ == "__main__":
    gerar_dashboard()
