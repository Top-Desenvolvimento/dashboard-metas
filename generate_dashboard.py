#!/usr/bin/env python3
"""
Gera dashboard HTML a partir de data/metas_atual.json

Estrutura esperada:
{
  "Caxias": {
    "mes_referencia": "2026-03",
    "timestamp": "...",
    "indicadores": {
      "ortodontia": {"meta":"", "ate_o_momento":"", "falta":"", "progresso":""},
      ...
    }
  }
}
"""

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


def mes_label(valor):
    if not valor:
        return datetime.now().strftime("%m/%Y")

    mapa = {
        "01": "Janeiro",
        "02": "Fevereiro",
        "03": "Março",
        "04": "Abril",
        "05": "Maio",
        "06": "Junho",
        "07": "Julho",
        "08": "Agosto",
        "09": "Setembro",
        "10": "Outubro",
        "11": "Novembro",
        "12": "Dezembro",
    }

    try:
        ano, mes = valor.split("-")
        return f"{mapa.get(mes, mes)}/{ano}"
    except Exception:
        return valor


def garantir_valor(valor):
    valor = "" if valor is None else str(valor).strip()
    return valor if valor else "—"


def percentual_para_float(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    if not texto or texto == "—":
        return None

    texto = texto.replace("%", "").replace(".", "").replace(",", ".").strip()

    try:
        return float(texto)
    except Exception:
        return None


def indicador_tem_dados(ind):
    if not ind:
        return False

    campos = [
        str(ind.get("meta", "")).strip(),
        str(ind.get("ate_o_momento", "")).strip(),
        str(ind.get("falta", "")).strip(),
        str(ind.get("progresso", "")).strip(),
    ]
    return any(campo != "" for campo in campos)


def classe_status(percentual):
    if percentual is None:
        return "empty"
    if percentual >= 100:
        return "ok"
    if percentual >= 70:
        return "warn"
    return "bad"


def processar_cidades(dados):
    cidades = []

    for cidade, info in dados.items():
        indicadores = info.get("indicadores", {})

        percentuais_validos = []
        for chave in ORDEM_INDICADORES:
            p = percentual_para_float(indicadores.get(chave, {}).get("progresso", ""))
            if p is not None:
                percentuais_validos.append(p)

        progresso_geral = sum(percentuais_validos) / len(percentuais_validos) if percentuais_validos else None

        cidades.append({
            "cidade": cidade,
            "slug": slug(cidade),
            "mes_referencia": info.get("mes_referencia", ""),
            "timestamp": info.get("timestamp", ""),
            "indicadores": indicadores,
            "progresso_geral": progresso_geral,
        })

    cidades.sort(
        key=lambda c: (c["progresso_geral"] is None, -(c["progresso_geral"] or 0), c["cidade"])
    )

    return cidades


def montar_metas_batidas(cidades):
    batidas = []

    for cidade in cidades:
        for chave in ORDEM_INDICADORES:
            indicador = cidade["indicadores"].get(chave, {})
            percentual = percentual_para_float(indicador.get("progresso", ""))

            if percentual is not None and percentual >= 100:
                batidas.append({
                    "cidade": cidade["cidade"],
                    "meta": MAPA_INDICADORES[chave],
                    "progresso": indicador.get("progresso", ""),
                    "percentual_num": percentual,
                })

    batidas.sort(key=lambda x: (-x["percentual_num"], x["cidade"], x["meta"]))
    return batidas


def montar_rankings(cidades):
    rankings = {}

    for chave in ORDEM_INDICADORES:
        ranking = []

        for cidade in cidades:
            indicador = cidade["indicadores"].get(chave, {})
            percentual = percentual_para_float(indicador.get("progresso", ""))

            ranking.append({
                "cidade": cidade["cidade"],
                "progresso": indicador.get("progresso", ""),
                "percentual_num": percentual,
                "meta": indicador.get("meta", ""),
                "ate_o_momento": indicador.get("ate_o_momento", ""),
                "falta": indicador.get("falta", ""),
                "tem_dado": indicador_tem_dados(indicador),
            })

        ranking.sort(
            key=lambda x: (
                x["percentual_num"] is None,
                -(x["percentual_num"] or 0),
                x["cidade"]
            )
        )

        rankings[chave] = ranking

    return rankings


def render_metadado_card(titulo, valor):
    return f"""
    <div class="summary-card">
        <div class="summary-label">{titulo}</div>
        <div class="summary-value">{valor}</div>
    </div>
    """


def render_tabela_cidade(indicadores):
    linhas = []

    for chave in ORDEM_INDICADORES:
        nome = MAPA_INDICADORES[chave]
        ind = indicadores.get(chave, {})

        progresso = ind.get("progresso", "")
        percentual = percentual_para_float(progresso)
        status = classe_status(percentual)

        linhas.append(f"""
        <tr>
            <td class="cell-title">{nome}</td>
            <td>{garantir_valor(ind.get("meta", ""))}</td>
            <td>{garantir_valor(ind.get("ate_o_momento", ""))}</td>
            <td>{garantir_valor(ind.get("falta", ""))}</td>
            <td class="perc {status}">{garantir_valor(progresso)}</td>
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


def render_ranking_card(titulo, ranking):
    linhas = []

    for pos, item in enumerate(ranking, start=1):
        percentual = item["percentual_num"]
        status = classe_status(percentual)

        progresso_exibido = garantir_valor(item["progresso"])
        meta = garantir_valor(item["meta"])
        ate = garantir_valor(item["ate_o_momento"])

        badge = pos
        pos_class = "pos-other"
        if pos == 1:
            pos_class = "pos-1"
        elif pos == 2:
            pos_class = "pos-2"
        elif pos == 3:
            pos_class = "pos-3"

        linhas.append(f"""
        <div class="rank-row">
            <div class="rank-pos {pos_class}">{badge}</div>
            <div class="rank-city">{item["cidade"]}</div>
            <div class="rank-meta">Meta: {meta}</div>
            <div class="rank-ate">Até o momento: {ate}</div>
            <div class="rank-perc {status}">{progresso_exibido}</div>
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


def gerar_html(cidades):
    mes = cidades[0]["mes_referencia"] if cidades else ""
    mes_texto = mes_label(mes)
    agora = datetime.now().strftime("%H:%M:%S")

    metas_batidas = montar_metas_batidas(cidades)
    rankings = montar_rankings(cidades)

    tabs = ['<button class="tab-btn active" data-tab="ranking-geral">🏆 Ranking Geral</button>']
    for cidade in cidades:
        tabs.append(f'<button class="tab-btn" data-tab="{cidade["slug"]}">📍 {cidade["cidade"]}</button>')

    destaque_html = ""
    if metas_batidas:
        itens = []
        for item in metas_batidas:
            itens.append(f"""
            <div class="hit-badge">
                <span class="hit-city">{item["cidade"]}</span>
                <span class="hit-sep">—</span>
                <span class="hit-meta">{item["meta"]}</span>
                <span class="hit-sep">—</span>
                <span class="hit-perc blink">{item["progresso"]}</span>
            </div>
            """)
        destaque_html = f"""
        <section class="highlight-panel">
            <div class="highlight-title">🏆 Metas Batidas</div>
            <div class="highlight-grid">
                {''.join(itens)}
            </div>
        </section>
        """
    else:
        destaque_html = """
        <section class="highlight-panel">
            <div class="highlight-title">🏆 Metas Batidas</div>
            <div class="highlight-empty">Nenhuma cidade atingiu 100% em alguma meta até o momento.</div>
        </section>
        """

    ranking_cards = []
    for chave in ORDEM_INDICADORES:
        ranking_cards.append(
            render_ranking_card(MAPA_INDICADORES[chave], rankings[chave])
        )

    cidades_html = []
    for cidade in cidades:
        progresso_geral = (
            f"{cidade['progresso_geral']:.1f}%".replace(".", ",")
            if cidade["progresso_geral"] is not None
            else "—"
        )

        cidades_html.append(f"""
        <div id="{cidade["slug"]}" class="tab-content">
            <section class="summary-grid">
                {render_metadado_card("Mês de Referência", mes_texto)}
                {render_metadado_card("Progresso Geral", progresso_geral)}
                {render_metadado_card("Cidade", cidade["cidade"])}
                {render_metadado_card("Atualizado em", agora)}
            </section>

            <section class="city-panel">
                <div class="panel-header">
                    <div class="panel-title">Dados da Cidade</div>
                </div>
                {render_tabela_cidade(cidade["indicadores"])}
            </section>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Dashboard de Metas</title>
<style>
:root {{
    --bg: #030a12;
    --panel: rgba(7, 19, 32, 0.92);
    --panel-2: rgba(4, 14, 24, 0.92);
    --border: rgba(0, 232, 255, 0.16);
    --line: rgba(255, 255, 255, 0.06);
    --text: #e6f7ff;
    --muted: #7e95a7;
    --cyan: #00e8ff;
    --green: #10e0a3;
    --yellow: #f5b301;
    --red: #ff4d7a;
    --shadow: 0 0 0 1px rgba(0, 232, 255, 0.08), 0 10px 30px rgba(0, 0, 0, 0.35);
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: Inter, Segoe UI, Arial, sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at top left, rgba(0, 232, 255, 0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(16, 224, 163, 0.08), transparent 25%),
        linear-gradient(180deg, #02060d, #04101b 45%, #02070d 100%);
    min-height: 100vh;
}}

.wrap {{
    max-width: 1500px;
    margin: 0 auto;
    padding: 16px;
}}

.hero {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    padding: 8px 0 24px;
}}

.hero-left h1 {{
    font-size: 2.8rem;
    font-weight: 800;
}}

.hero-left p {{
    margin-top: 8px;
    color: var(--muted);
    font-size: 1.05rem;
}}

.hero-right {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
}}

.pill {{
    background: rgba(7, 19, 32, 0.8);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    border-radius: 14px;
    padding: 14px 16px;
    color: var(--text);
    min-width: 120px;
}}

.pill.btn {{
    text-decoration: none;
    background: linear-gradient(135deg, rgba(0,232,255,.95), rgba(16,224,163,.95));
    color: #031018;
    font-weight: 700;
}}

.tabs {{
    display: flex;
    align-items: center;
    gap: 8px;
    overflow-x: auto;
    padding: 10px 0 16px;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    margin-bottom: 20px;
}}

.tab-btn {{
    background: transparent;
    color: var(--muted);
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 14px;
    cursor: pointer;
    white-space: nowrap;
    transition: .2s ease;
    font-weight: 600;
}}

.tab-btn:hover {{
    color: var(--text);
    border-color: var(--border);
}}

.tab-btn.active {{
    color: var(--cyan);
    border-color: rgba(0, 232, 255, 0.35);
    background: rgba(0,232,255,.08);
}}

.tab-content {{
    display: none;
}}

.tab-content.active {{
    display: block;
}}

.highlight-panel,
.panel,
.city-panel,
.summary-card {{
    background: linear-gradient(180deg, var(--panel), var(--panel-2));
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: var(--shadow);
}}

.highlight-panel {{
    padding: 18px;
    margin-bottom: 18px;
}}

.highlight-title {{
    font-size: 1.2rem;
    font-weight: 800;
    margin-bottom: 14px;
}}

.highlight-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}}

.hit-badge {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    padding: 14px;
    border-radius: 14px;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.05);
}}

.hit-city {{
    color: #fff;
    font-weight: 800;
}}

.hit-meta {{
    color: var(--cyan);
    font-weight: 700;
}}

.hit-perc {{
    color: var(--green);
    font-weight: 900;
}}

.hit-sep {{
    color: var(--muted);
}}

.highlight-empty {{
    color: var(--muted);
}}

.summary-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 18px;
}}

.summary-card {{
    padding: 18px;
    min-height: 110px;
}}

.summary-label {{
    color: var(--muted);
    font-size: .85rem;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 12px;
}}

.summary-value {{
    font-size: 2rem;
    font-weight: 800;
    color: var(--cyan);
}}

.panel,
.city-panel {{
    padding: 16px;
    margin-bottom: 18px;
}}

.panel-header {{
    margin-bottom: 14px;
}}

.panel-title {{
    font-size: 1.15rem;
    font-weight: 800;
}}

.rankings-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}}

.rank-row {{
    display: grid;
    grid-template-columns: 42px 1.2fr 1fr 1fr 110px;
    gap: 10px;
    align-items: center;
    padding: 12px 0;
    border-top: 1px solid rgba(255,255,255,.05);
}}

.rank-row:first-child {{
    border-top: none;
}}

.rank-pos {{
    width: 32px;
    height: 32px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    background: rgba(255,255,255,.08);
}}

.pos-1 {{ background: rgba(245,179,1,.20); color: #ffd45c; }}
.pos-2 {{ background: rgba(180,196,210,.20); color: #dbe6ef; }}
.pos-3 {{ background: rgba(165,102,38,.22); color: #ffb56d; }}
.pos-other {{ color: #fff; }}

.rank-city {{
    font-weight: 700;
    color: #fff;
}}

.rank-meta,
.rank-ate {{
    color: var(--muted);
    font-size: .92rem;
}}

.rank-perc {{
    text-align: right;
    font-weight: 800;
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
    padding: 14px 12px;
    border-top: 1px solid rgba(255,255,255,.05);
    text-align: left;
}}

.dash-table th {{
    color: var(--muted);
    font-size: .9rem;
    text-transform: uppercase;
    letter-spacing: .05em;
}}

.dash-table td {{
    color: #fff;
}}

.cell-title {{
    font-weight: 800;
}}

.perc.ok {{
    color: var(--green);
    font-weight: 800;
}}

.perc.warn {{
    color: var(--yellow);
    font-weight: 800;
}}

.perc.bad {{
    color: var(--red);
    font-weight: 800;
}}

.perc.empty {{
    color: var(--muted);
    font-weight: 700;
}}

.ok {{ color: var(--green); }}
.warn {{ color: var(--yellow); }}
.bad {{ color: var(--red); }}
.empty {{ color: var(--muted); }}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: .4; transform: scale(1.03); }}
}}

.blink {{
    animation: pulse 1.2s infinite;
}}

@media (max-width: 1200px) {{
    .rankings-grid,
    .highlight-grid,
    .summary-grid {{
        grid-template-columns: 1fr;
    }}

    .rank-row {{
        grid-template-columns: 36px 1fr;
        gap: 8px;
    }}

    .rank-meta,
    .rank-ate,
    .rank-perc {{
        grid-column: 2;
        text-align: left;
    }}
}}

@media (max-width: 760px) {{
    .hero {{
        flex-direction: column;
    }}

    .hero-left h1 {{
        font-size: 2rem;
    }}
}}
</style>
</head>
<body>
<main class="wrap">
    <header class="hero">
        <div class="hero-left">
            <h1>Dashboard de Metas</h1>
            <p>Top Estética Bucal — {len(cidades)} Unidades</p>
        </div>
        <div class="hero-right">
            <div class="pill"><strong>{mes_texto}</strong></div>
            <div class="pill"><strong>{agora}</strong></div>
            <div class="pill"><strong>● Online</strong></div>
            <a class="pill btn" href="../data/metas_top_estetica.xlsx" download>⬇ Exportar Planilha</a>
        </div>
    </header>

    <nav class="tabs">
        {''.join(tabs)}
    </nav>

    <div id="ranking-geral" class="tab-content active">
        {destaque_html}

        <div class="rankings-grid">
            {''.join(ranking_cards)}
        </div>
    </div>

    {''.join(cidades_html)}
</main>

<script>
const buttons = document.querySelectorAll('.tab-btn');
const contents = document.querySelectorAll('.tab-content');

buttons.forEach(btn => {{
    btn.addEventListener('click', () => {{
        buttons.forEach(b => b.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        const target = document.getElementById(btn.dataset.tab);
        if (target) target.classList.add('active');
    }});
}});
</script>
</body>
</html>
"""
    return html


def main():
    dados = carregar_dados()
    cidades = processar_cidades(dados)

    html = gerar_html(cidades)

    os.makedirs("docs", exist_ok=True)
    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Dashboard gerado com sucesso em {ARQUIVO_HTML}")


if __name__ == "__main__":
    pass
