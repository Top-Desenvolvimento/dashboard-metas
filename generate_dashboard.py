#!/usr/bin/env python3
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

INDICADORES_FINANCEIROS = ["ortodontia", "clinico_geral"]
INDICADORES_SERVICOS = [
    "avaliacoes_google",
    "meta_avaliacao",
    "meta_profilaxia",
    "meta_restauracao",
]
ORDEM_INDICADORES = INDICADORES_FINANCEIROS + INDICADORES_SERVICOS


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
        "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
        "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
        "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro",
    }
    try:
        ano, mes = valor.split("-")
        return f"{mapa.get(mes, mes)}/{ano}"
    except Exception:
        return valor


def garantir_valor(valor):
    texto = "" if valor is None else str(valor).strip()
    return texto if texto else "—"


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
    return any(str(ind.get(k, "")).strip() for k in ["meta", "ate_o_momento", "falta", "progresso"])


def classe_status(percentual):
    if percentual is None:
        return "empty"
    if percentual >= 100:
        return "ok"
    if percentual >= 70:
        return "warn"
    return "bad"


def cor_status(percentual):
    status = classe_status(percentual)
    if status == "ok":
        return "#13d99f"
    if status == "warn":
        return "#f5b301"
    if status == "bad":
        return "#ff4d7a"
    return "#4d6475"


def progresso_geral_cidade(indicadores):
    vals = []
    for chave in ORDEM_INDICADORES:
        p = percentual_para_float(indicadores.get(chave, {}).get("progresso", ""))
        if p is not None:
            vals.append(p)
    return (sum(vals) / len(vals)) if vals else None


def processar_cidades(dados):
    cidades = []
    for cidade, info in dados.items():
        indicadores = info.get("indicadores", {})
        cidades.append({
            "cidade": cidade,
            "slug": slug(cidade),
            "mes_referencia": info.get("mes_referencia", ""),
            "timestamp": info.get("timestamp", ""),
            "indicadores": indicadores,
            "progresso_geral": progresso_geral_cidade(indicadores),
        })

    cidades.sort(key=lambda x: (x["progresso_geral"] is None, -(x["progresso_geral"] or 0), x["cidade"]))
    return cidades


def metas_batidas(cidades):
    saida = []
    for cidade in cidades:
        for chave in ORDEM_INDICADORES:
            indicador = cidade["indicadores"].get(chave, {})
            p = percentual_para_float(indicador.get("progresso", ""))
            if p is not None and p >= 100:
                saida.append({
                    "cidade": cidade["cidade"],
                    "indicador": MAPA_INDICADORES[chave],
                    "progresso": indicador.get("progresso", ""),
                    "percentual_num": p,
                })
    saida.sort(key=lambda x: (-x["percentual_num"], x["cidade"], x["indicador"]))
    return saida


def rankings_por_segmento(cidades):
    rankings = {}
    for chave in ORDEM_INDICADORES:
        itens = []
        for cidade in cidades:
            indicador = cidade["indicadores"].get(chave, {})
            p = percentual_para_float(indicador.get("progresso", ""))
            itens.append({
                "cidade": cidade["cidade"],
                "meta": indicador.get("meta", ""),
                "ate_o_momento": indicador.get("ate_o_momento", ""),
                "progresso": indicador.get("progresso", ""),
                "percentual_num": p,
            })
        itens.sort(key=lambda x: (x["percentual_num"] is None, -(x["percentual_num"] or 0), x["cidade"]))
        rankings[chave] = itens
    return rankings


def circle_card_html(titulo, indicador):
    percentual = percentual_para_float(indicador.get("progresso", ""))
    if percentual is None:
        percentual = 0
    status = classe_status(percentual)
    cor = cor_status(percentual)
    perc_txt = garantir_valor(indicador.get("progresso", ""))
    if perc_txt == "—":
        perc_txt = "0%"

    progress = max(0, min(percentual, 100))
    deg = (progress / 100) * 360

    return f"""
    <section class="metric-card financial">
        <div class="metric-head">
            <div class="metric-title">{titulo}</div>
            <div class="metric-percent {status}">↗ {perc_txt}</div>
        </div>

        <div class="financial-body">
            <div class="ring" style="--deg:{deg}deg; --ring-color:{cor};">
                <div class="ring-inner">{perc_txt}</div>
            </div>

            <div class="financial-values">
                <div class="value-row"><span>Meta</span><strong>{garantir_valor(indicador.get("meta", ""))}</strong></div>
                <div class="value-row"><span>Realizado</span><strong class="highlight">{garantir_valor(indicador.get("ate_o_momento", ""))}</strong></div>
                <div class="value-row"><span>Falta</span><strong class="{status}">{garantir_valor(indicador.get("falta", ""))}</strong></div>
            </div>
        </div>
    </section>
    """


def service_card_html(titulo, indicador):
    percentual = percentual_para_float(indicador.get("progresso", ""))
    largura = max(0, min(percentual or 0, 100))
    status = classe_status(percentual)

    return f"""
    <section class="service-card">
        <div class="service-head">
            <div class="service-title">{titulo}</div>
            <div class="service-percent {status}">{garantir_valor(indicador.get("progresso", ""))}</div>
        </div>
        <div class="service-bar">
            <div class="service-fill {status}" style="width:{largura}%"></div>
        </div>
        <div class="service-values">
            <div><span>Meta:</span> <strong>{garantir_valor(indicador.get("meta", ""))}</strong></div>
            <div><span>Realizado:</span> <strong>{garantir_valor(indicador.get("ate_o_momento", ""))}</strong></div>
            <div><span>Falta:</span> <strong>{garantir_valor(indicador.get("falta", ""))}</strong></div>
        </div>
    </section>
    """


def ranking_segmento_card(titulo, itens):
    linhas = []
    for idx, item in enumerate(itens, start=1):
        percentual = item["percentual_num"]
        largura = max(0, min(percentual or 0, 100))
        status = classe_status(percentual)
        meta_exibida = garantir_valor(item["ate_o_momento"] if item["ate_o_momento"] else item["meta"])

        badge_class = "pos-other"
        if idx == 1:
            badge_class = "pos-1"
        elif idx == 2:
            badge_class = "pos-2"
        elif idx == 3:
            badge_class = "pos-3"

        linhas.append(f"""
        <div class="rank-item">
            <div class="rank-left">
                <div class="rank-pos {badge_class}">{idx}</div>
                <div class="rank-city">{item["cidade"]}</div>
            </div>
            <div class="rank-mid">
                <div class="rank-bar">
                    <div class="rank-fill {status}" style="width:{largura}%"></div>
                </div>
            </div>
            <div class="rank-right">
                <div class="rank-progress {status}">{garantir_valor(item["progresso"])}</div>
                <div class="rank-value">{meta_exibida}</div>
            </div>
        </div>
        """)

    return f"""
    <section class="segment-card">
        <div class="segment-header">
            <div class="segment-title">🏆 {titulo}</div>
        </div>
        <div class="segment-body">
            {''.join(linhas)}
        </div>
    </section>
    """


def gerar_html(cidades):
    mes = cidades[0]["mes_referencia"] if cidades else ""
    mes_txt = mes_label(mes)
    hora_txt = datetime.now().strftime("%H:%M:%S")

    tabs = ['<button class="tab-btn active" data-tab="ranking-geral">🏆 Ranking Geral</button>']
    for cidade in cidades:
        tabs.append(f'<button class="tab-btn" data-tab="{cidade["slug"]}">📍 {cidade["cidade"]}</button>')

    destaques = metas_batidas(cidades)
    rankings = rankings_por_segmento(cidades)

    if destaques:
        destaques_html = []
        agrupado = {}
        for item in destaques:
            agrupado.setdefault(item["cidade"], []).append(item)

        for cidade, itens in agrupado.items():
            linhas = "".join(
                f'<div class="hit-line"><span>✓ {i["indicador"]}</span><strong class="blink">{i["progresso"]}</strong></div>'
                for i in itens
            )
            destaques_html.append(f"""
            <div class="hit-group">
                <div class="hit-city-title">{cidade}</div>
                {linhas}
            </div>
            """)
        bloco_destaques = "".join(destaques_html)
    else:
        bloco_destaques = '<div class="hit-empty">Nenhuma meta acima de 100% no momento.</div>'

    ranking_cards = []
    for chave in ORDEM_INDICADORES:
        ranking_cards.append(ranking_segmento_card(MAPA_INDICADORES[chave], rankings[chave]))

    cidades_html = []
    for cidade in cidades:
        ind = cidade["indicadores"]
        progresso_geral = (
            f"{cidade['progresso_geral']:.1f}%".replace(".", ",")
            if cidade["progresso_geral"] is not None else "—"
        )

        financeiro = "".join(
            circle_card_html(MAPA_INDICADORES[ch], ind.get(ch, {}))
            for ch in INDICADORES_FINANCEIROS
        )

        servicos = "".join(
            service_card_html(MAPA_INDICADORES[ch], ind.get(ch, {}))
            for ch in INDICADORES_SERVICOS
        )

        cidades_html.append(f"""
        <div id="{cidade["slug"]}" class="tab-content">
            <section class="city-summary-grid">
                <div class="summary-card">
                    <div class="summary-label">Meta Financeira</div>
                    <div class="summary-value">{garantir_valor(ind.get("ortodontia", {}).get("meta", "")) if garantir_valor(ind.get("ortodontia", {}).get("meta", "")) != "—" else garantir_valor(ind.get("clinico_geral", {}).get("meta", ""))}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Realizado</div>
                    <div class="summary-value alt">{garantir_valor(ind.get("ortodontia", {}).get("ate_o_momento", "")) if garantir_valor(ind.get("ortodontia", {}).get("ate_o_momento", "")) != "—" else garantir_valor(ind.get("clinico_geral", {}).get("ate_o_momento", ""))}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Progresso Geral</div>
                    <div class="summary-value alt2">{progresso_geral}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Atualizado em</div>
                    <div class="summary-value">{hora_txt}</div>
                </div>
            </section>

            <div class="section-title">💲 Metas Financeiras</div>
            <section class="financial-grid">
                {financeiro}
            </section>

            <div class="section-title">⚡ Metas de Serviços</div>
            <section class="services-grid">
                {servicos}
            </section>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard de Metas</title>
<style>
:root {{
    --bg: #020914;
    --bg2: #07111d;
    --panel: rgba(6, 16, 28, 0.92);
    --panel2: rgba(7, 20, 34, 0.96);
    --line: rgba(255,255,255,0.06);
    --border: rgba(0, 232, 255, 0.14);
    --text: #edf7ff;
    --muted: #7b91a6;
    --cyan: #00e8ff;
    --green: #12d99f;
    --yellow: #f5b301;
    --red: #ff4d7a;
    --shadow: 0 0 0 1px rgba(0,232,255,.06), 0 12px 30px rgba(0,0,0,.35);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: Inter, Segoe UI, Arial, sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at top left, rgba(0,232,255,.08), transparent 30%),
        radial-gradient(circle at top right, rgba(18,217,159,.07), transparent 28%),
        linear-gradient(180deg, #01050b, #06111c 45%, #02070d 100%);
    min-height: 100vh;
}}

.wrap {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 16px;
}}

.hero {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 18px;
    padding: 10px 0 20px;
}}

.hero h1 {{
    font-size: 3rem;
    font-weight: 900;
    line-height: 1.05;
}}

.hero p {{
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
    padding: 14px 18px;
    border-radius: 16px;
    background: rgba(6, 16, 28, 0.86);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    font-weight: 700;
}}

.pill.btn {{
    text-decoration: none;
    color: #031018;
    background: linear-gradient(135deg, rgba(0,232,255,.95), rgba(18,217,159,.95));
}}

.tabs {{
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding: 10px 0 14px;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    margin-bottom: 18px;
}}

.tab-btn {{
    border: 1px solid transparent;
    background: transparent;
    color: var(--muted);
    border-radius: 14px;
    padding: 10px 14px;
    cursor: pointer;
    white-space: nowrap;
    font-weight: 700;
}}

.tab-btn.active {{
    color: var(--cyan);
    border-color: rgba(0,232,255,.28);
    background: rgba(0,232,255,.08);
}}

.tab-content {{
    display: none;
}}

.tab-content.active {{
    display: block;
}}

.top-overview {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 22px;
}}

.overview-box,
.segment-card,
.summary-card,
.metric-card,
.service-card {{
    background: linear-gradient(180deg, var(--panel2), var(--panel));
    border: 1px solid var(--border);
    border-radius: 22px;
    box-shadow: var(--shadow);
}}

.overview-box {{
    min-height: 180px;
    padding: 18px;
}}

.box-title {{
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .08em;
    font-size: .82rem;
    margin-bottom: 16px;
}}

.big-number {{
    font-size: 2.8rem;
    color: var(--cyan);
    font-weight: 900;
}}

.big-caption {{
    color: var(--muted);
    margin-top: 8px;
}}

.hit-group {{
    margin-bottom: 18px;
}}

.hit-city-title {{
    color: var(--green);
    font-size: 1.9rem;
    font-weight: 900;
    margin-bottom: 8px;
}}

.hit-line {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 4px 0;
    color: #bfe8ef;
}}

.hit-line strong {{
    color: var(--green);
}}

.hit-empty {{
    color: var(--muted);
}}

.section-title {{
    font-size: 1.6rem;
    font-weight: 900;
    margin: 18px 0 14px;
}}

.rankings-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}}

.segment-card {{
    overflow: hidden;
}}

.segment-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 18px;
    border-bottom: 1px solid var(--line);
}}

.segment-title {{
    font-size: 1rem;
    font-weight: 900;
}}

.segment-body {{
    padding: 8px 18px 16px;
}}

.rank-item {{
    display: grid;
    grid-template-columns: 160px 1fr 160px;
    gap: 16px;
    align-items: center;
    padding: 14px 0;
    border-top: 1px solid rgba(255,255,255,.04);
}}

.rank-item:first-child {{
    border-top: none;
}}

.rank-left {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.rank-pos {{
    width: 34px;
    height: 34px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    background: rgba(255,255,255,.07);
}}

.pos-1 {{ background: rgba(245,179,1,.20); color: #ffd45c; }}
.pos-2 {{ background: rgba(180,196,210,.20); color: #dbe6ef; }}
.pos-3 {{ background: rgba(165,102,38,.20); color: #ffb56d; }}
.pos-other {{ color: #fff; }}

.rank-city {{
    font-size: 1.05rem;
    font-weight: 800;
}}

.rank-bar {{
    width: 100%;
    height: 10px;
    border-radius: 999px;
    background: rgba(255,255,255,.05);
    overflow: hidden;
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
    font-size: 1.1rem;
}}

.rank-value {{
    color: var(--muted);
    margin-top: 6px;
}}

.ok {{ color: var(--green); }}
.warn {{ color: var(--yellow); }}
.bad {{ color: var(--red); }}
.empty {{ color: var(--muted); }}

.city-summary-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 18px;
}}

.summary-card {{
    padding: 18px 22px;
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
    font-size: 2rem;
    font-weight: 900;
}}

.summary-value.alt {{
    color: #ffc71e;
}}

.summary-value.alt2 {{
    color: #26ffcd;
}}

.financial-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}}

.metric-card {{
    padding: 22px;
}}

.metric-head,
.service-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
}}

.metric-title,
.service-title {{
    font-size: 1.1rem;
    font-weight: 900;
}}

.metric-percent,
.service-percent {{
    font-size: 1.05rem;
    font-weight: 900;
}}

.financial-body {{
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 26px;
    align-items: center;
}}

.ring {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background:
      conic-gradient(var(--ring-color) 0deg var(--deg), rgba(255,255,255,.06) var(--deg) 360deg);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 18px rgba(0,0,0,.35);
}}

.ring-inner {{
    width: 86px;
    height: 86px;
    border-radius: 50%;
    background: #07111d;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--ring-color);
    font-size: 1.05rem;
    font-weight: 900;
    text-align: center;
}

.financial-values {{
    display: flex;
    flex-direction: column;
    gap: 10px;
}}

.value-row {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255,255,255,.05);
}}

.value-row:last-child {{
    border-bottom: none;
}}

.value-row span {{
    color: var(--muted);
}}

.value-row strong {{
    color: #fff;
}}

.value-row strong.highlight {{
    color: var(--cyan);
}}

.services-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}}

.service-card {{
    padding: 22px;
}}

.service-bar {{
    height: 12px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(255,255,255,.05);
    margin-bottom: 14px;
}}

.service-fill {{
    height: 100%;
    border-radius: 999px;
}}

.service-fill.ok {{ background: linear-gradient(90deg, #12d99f, #08f0c2); }}
.service-fill.warn {{ background: linear-gradient(90deg, #f0a500, #f7c52b); }}
.service-fill.bad {{ background: linear-gradient(90deg, #ff4d7a, #ff6a91); }}
.service-fill.empty {{ background: #223345; }}

.service-values {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    color: var(--muted);
}}

.service-values strong {{
    color: #fff;
}}

@keyframes pulse {{
    0%,100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: .35; transform: scale(1.03); }}
}}

.blink {{
    animation: pulse 1.2s infinite;
}}

@media (max-width: 1200px) {{
    .top-overview,
    .rankings-grid,
    .city-summary-grid,
    .financial-grid,
    .services-grid {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 820px) {{
    .hero {{
        flex-direction: column;
    }}

    .hero h1 {{
        font-size: 2.2rem;
    }}

    .rank-item {{
        grid-template-columns: 1fr;
    }}

    .rank-right {{
        text-align: left;
    }}

    .service-values {{
        grid-template-columns: 1fr;
    }}

    .financial-body {{
        grid-template-columns: 1fr;
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
            <div class="pill">{mes_txt}</div>
            <div class="pill">{hora_txt}</div>
            <div class="pill">● Online</div>
            <a class="pill btn" href="../data/metas_top_estetica.xlsx" download>⬇ Exportar Planilha</a>
        </div>
    </header>

    <nav class="tabs">
        {''.join(tabs)}
    </nav>

    <div id="ranking-geral" class="tab-content active">
        <section class="top-overview">
            <div class="overview-box">
                <div class="box-title">Unidades</div>
                <div class="big-number">{len(cidades)}</div>
                <div class="big-caption">cidades monitoradas</div>
            </div>

            <div class="overview-box">
                <div class="box-title">Metas Batidas por Cidade</div>
                {bloco_destaques}
            </div>
        </section>

        <div class="section-title">🏆 Ranking por Segmento</div>
        <section class="rankings-grid">
            {''.join(ranking_cards)}
        </section>
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
    main()
