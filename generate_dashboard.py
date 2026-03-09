#!/usr/bin/env python3
"""
Gera dashboard HTML moderno para GitHub Pages
"""

import json
import os
import re
from datetime import datetime


def carregar_dados():
    with open("data/metas_atual.json", "r", encoding="utf-8") as f:
        return json.load(f)


def moeda_para_float(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    if not texto:
        return 0.0

    texto = texto.replace("R$", "").replace(" ", "")
    texto = texto.replace(".", "").replace(",", ".")
    texto = re.sub(r"[^0-9.\-]", "", texto)

    try:
        return float(texto)
    except Exception:
        return 0.0


def numero_para_float(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    if not texto:
        return 0.0

    texto = texto.replace(".", "").replace(",", ".")
    texto = re.sub(r"[^0-9.\-]", "", texto)

    try:
        return float(texto)
    except Exception:
        return 0.0


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_numero(valor):
    if float(valor).is_integer():
        return str(int(valor))
    return f"{valor:.1f}".replace(".", ",")


def formatar_percentual(valor):
    return f"{valor:.1f}%"


def classe_status(percentual):
    if percentual >= 100:
        return "ok"
    if percentual >= 70:
        return "warn"
    return "bad"


def mes_label(valor):
    if not valor:
        return datetime.now().strftime("%B/%Y")

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


def slug(texto):
    texto = texto.lower()
    texto = texto.replace("ã", "a").replace("á", "a").replace("à", "a").replace("â", "a")
    texto = texto.replace("é", "e").replace("ê", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o").replace("ô", "o").replace("õ", "o")
    texto = texto.replace("ú", "u")
    texto = texto.replace("ç", "c")
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto


def processar_cidade(cidade, info):
    orto = moeda_para_float(info.get("metas_financeiras", {}).get("ortodontia", 0))
    clin = moeda_para_float(info.get("metas_financeiras", {}).get("clinico_geral", 0))
    prof = numero_para_float(info.get("metas_servicos", {}).get("profilaxia", 0))
    rest = numero_para_float(info.get("metas_servicos", {}).get("restauracao", 0))
    aval = numero_para_float(info.get("avaliacoes", {}).get("novas", 0))

    # Metas estimadas para visualização.
    # Quando você trouxer metas reais no JSON, eu ajusto para ficar exato.
    meta_orto = max(orto, 1) if orto > 0 else 1
    meta_clin = max(clin, 1) if clin > 0 else 1
    meta_prof = max(prof, 1) if prof > 0 else 1
    meta_rest = max(rest, 1) if rest > 0 else 1
    meta_aval = max(aval, 1) if aval > 0 else 1

    indicadores = {
        "ortodontia": {
            "label": "Ortodontia",
            "tipo": "financeiro",
            "realizado": orto,
            "meta": meta_orto,
            "percentual": (orto / meta_orto * 100) if meta_orto else 0,
            "formatador": "moeda",
        },
        "clinico_geral": {
            "label": "Clínico Geral",
            "tipo": "financeiro",
            "realizado": clin,
            "meta": meta_clin,
            "percentual": (clin / meta_clin * 100) if meta_clin else 0,
            "formatador": "moeda",
        },
        "profilaxia": {
            "label": "Meta de Profilaxia",
            "tipo": "servico",
            "realizado": prof,
            "meta": meta_prof,
            "percentual": (prof / meta_prof * 100) if meta_prof else 0,
            "formatador": "numero",
        },
        "restauracao": {
            "label": "Meta de Restauração",
            "tipo": "servico",
            "realizado": rest,
            "meta": meta_rest,
            "percentual": (rest / meta_rest * 100) if meta_rest else 0,
            "formatador": "numero",
        },
        "avaliacoes": {
            "label": "Avaliações Google",
            "tipo": "servico",
            "realizado": aval,
            "meta": meta_aval,
            "percentual": (aval / meta_aval * 100) if meta_aval else 0,
            "formatador": "numero",
        },
    }

    progresso_geral = sum(i["percentual"] for i in indicadores.values()) / len(indicadores)
    total_financeiro = orto + clin

    return {
        "cidade": cidade,
        "slug": slug(cidade),
        "mes_referencia": info.get("mes_referencia", ""),
        "timestamp": info.get("timestamp", ""),
        "indicadores": indicadores,
        "progresso_geral": progresso_geral,
        "total_financeiro": total_financeiro,
    }


def valor_formatado(ind):
    if ind["formatador"] == "moeda":
        return formatar_moeda(ind["realizado"])
    return formatar_numero(ind["realizado"])


def meta_formatada(ind):
    if ind["formatador"] == "moeda":
        return formatar_moeda(ind["meta"])
    return formatar_numero(ind["meta"])


def falta_formatada(ind):
    falta = max(ind["meta"] - ind["realizado"], 0)
    if ind["formatador"] == "moeda":
        return formatar_moeda(falta)
    return formatar_numero(falta)


def gerar_ranking_card(titulo, tipo, ranking):
    linhas = []

    for pos, item in enumerate(ranking, start=1):
        perc = item["percentual"]
        status = classe_status(perc)
        barras = min(max(perc, 0), 100)

        if item["formatador"] == "moeda":
            detalhe = formatar_moeda(item["realizado"])
        else:
            detalhe = f'{formatar_numero(item["realizado"])} / {formatar_numero(item["meta"])}'

        linhas.append(f"""
            <div class="rank-row">
                <div class="rank-pos pos-{1 if pos == 1 else 2 if pos == 2 else 3 if pos == 3 else 9}">{pos}</div>
                <div class="rank-city">{item["cidade"]}</div>
                <div class="rank-bar">
                    <div class="rank-fill {status}" style="width:{barras}%"></div>
                </div>
                <div class="rank-perc {status}">{formatar_percentual(perc)}</div>
                <div class="rank-val">{detalhe}</div>
            </div>
        """)

    return f"""
        <section class="panel">
            <div class="panel-header">
                <div class="panel-title">{titulo}</div>
                <div class="panel-tag">{tipo}</div>
            </div>
            <div class="panel-body">
                {''.join(linhas)}
            </div>
        </section>
    """


def gerar_card_cidade(ind):
    perc = ind["percentual"]
    status = classe_status(perc)
    width = min(max(perc, 0), 100)

    return f"""
        <section class="city-card">
            <div class="city-card-head">
                <div class="city-card-title">{ind["label"]}</div>
                <div class="city-card-perc {status}">{formatar_percentual(perc)}</div>
            </div>

            <div class="city-progress">
                <div class="city-progress-fill {status}" style="width:{width}%"></div>
            </div>

            <div class="city-metrics">
                <div><span>Meta:</span><strong>{meta_formatada(ind)}</strong></div>
                <div><span>Realizado:</span><strong>{valor_formatado(ind)}</strong></div>
                <div><span>Falta:</span><strong>{falta_formatada(ind)}</strong></div>
            </div>
        </section>
    """


def gerar_html(dados):
    cidades = [processar_cidade(cidade, info) for cidade, info in dados.items()]
    cidades.sort(key=lambda x: x["progresso_geral"], reverse=True)

    mes_referencia = cidades[0]["mes_referencia"] if cidades else ""
    mes_texto = mes_label(mes_referencia)
    agora = datetime.now().strftime("%H:%M:%S")

    ranking_geral = sorted(cidades, key=lambda x: x["progresso_geral"], reverse=True)

    ranking_orto = sorted(
        [{"cidade": c["cidade"], **c["indicadores"]["ortodontia"]} for c in cidades],
        key=lambda x: x["percentual"],
        reverse=True
    )
    ranking_clin = sorted(
        [{"cidade": c["cidade"], **c["indicadores"]["clinico_geral"]} for c in cidades],
        key=lambda x: x["percentual"],
        reverse=True
    )
    ranking_aval = sorted(
        [{"cidade": c["cidade"], **c["indicadores"]["avaliacoes"]} for c in cidades],
        key=lambda x: x["percentual"],
        reverse=True
    )
    ranking_prof = sorted(
        [{"cidade": c["cidade"], **c["indicadores"]["profilaxia"]} for c in cidades],
        key=lambda x: x["percentual"],
        reverse=True
    )
    ranking_rest = sorted(
        [{"cidade": c["cidade"], **c["indicadores"]["restauracao"]} for c in cidades],
        key=lambda x: x["percentual"],
        reverse=True
    )

    tabs = ['<button class="tab-btn active" data-tab="ranking-geral">🏆 Ranking Geral</button>']
    for c in cidades:
        tabs.append(f'<button class="tab-btn" data-tab="{c["slug"]}">📍 {c["cidade"]}</button>')

    ranking_cards = f"""
        <div id="ranking-geral" class="tab-content active">
            <section class="top-grid">
                <div class="summary-card">
                    <div class="summary-label">Unidades</div>
                    <div class="summary-value">{len(cidades)}</div>
                    <div class="summary-sub">cidades monitoradas</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Melhor desempenho</div>
                    <div class="summary-value">{ranking_geral[0]["cidade"] if ranking_geral else '-'}</div>
                    <div class="summary-sub">{formatar_percentual(ranking_geral[0]["progresso_geral"]) if ranking_geral else '-'}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Mês de referência</div>
                    <div class="summary-value">{mes_texto}</div>
                    <div class="summary-sub">fechamento da dashboard</div>
                </div>
            </section>

            <section class="beat-panel">
                <div class="panel-header">
                    <div class="panel-title">Metas batidas por cidade</div>
                </div>
                <div class="beat-grid">
                    {''.join(
                        f'''
                        <div class="beat-item">
                            <div class="beat-city">{c["cidade"]}</div>
                            <div class="beat-list">
                                {''.join(
                                    f'<div class="beat-line">✓ {i["label"]} <strong>{formatar_percentual(i["percentual"])}</strong></div>'
                                    for i in c["indicadores"].values() if i["percentual"] >= 100
                                ) or '<div class="beat-line muted">Nenhuma meta acima de 100%</div>'}
                            </div>
                        </div>
                        '''
                        for c in ranking_geral
                    )}
                </div>
            </section>

            <div class="panels-grid">
                {gerar_ranking_card("Ortodontia", "Financeiro", ranking_orto)}
                {gerar_ranking_card("Clínico Geral", "Financeiro", ranking_clin)}
                {gerar_ranking_card("Avaliações Google", "Serviço", ranking_aval)}
                {gerar_ranking_card("Meta de Profilaxia", "Serviço", ranking_prof)}
                {gerar_ranking_card("Meta de Restauração", "Serviço", ranking_rest)}
            </div>
        </div>
    """

    cidades_html = []
    for c in cidades:
        ind = c["indicadores"]
        cidades_html.append(f"""
            <div id="{c["slug"]}" class="tab-content">
                <section class="city-top-grid">
                    <div class="summary-card">
                        <div class="summary-label">Meta Financeira</div>
                        <div class="summary-value">{formatar_moeda(ind["ortodontia"]["meta"] + ind["clinico_geral"]["meta"])}</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-label">Realizado</div>
                        <div class="summary-value">{formatar_moeda(ind["ortodontia"]["realizado"] + ind["clinico_geral"]["realizado"])}</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-label">Progresso Financeiro</div>
                        <div class="summary-value">
                            {formatar_percentual((ind["ortodontia"]["percentual"] + ind["clinico_geral"]["percentual"]) / 2)}
                        </div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-label">Progresso Geral</div>
                        <div class="summary-value">{formatar_percentual(c["progresso_geral"])}</div>
                    </div>
                </section>

                <div class="section-title">💰 Metas Financeiras</div>
                <div class="city-grid">
                    {gerar_card_cidade(ind["ortodontia"])}
                    {gerar_card_cidade(ind["clinico_geral"])}
                </div>

                <div class="section-title">⚡ Metas de Serviços</div>
                <div class="city-grid">
                    {gerar_card_cidade(ind["avaliacoes"])}
                    {gerar_card_cidade(ind["profilaxia"])}
                    {gerar_card_cidade(ind["restauracao"])}
                </div>
            </div>
        """)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Dashboard de Metas - Top Estética Bucal</title>
    <style>
        :root {{
            --bg: #030a12;
            --bg-2: #071320;
            --panel: rgba(7, 19, 32, 0.88);
            --border: rgba(0, 232, 255, 0.14);
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

        .bg-grid {{
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(0,232,255,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,232,255,0.05) 1px, transparent 1px);
            background-size: 42px 42px;
            opacity: .12;
            pointer-events: none;
        }}

        .wrap {{
            max-width: 1440px;
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
            line-height: 1.05;
            text-shadow: 0 0 18px rgba(0, 232, 255, 0.18);
        }}

        .hero-left p {{
            margin-top: 8px;
            color: var(--muted);
            font-size: 1.05rem;
        }}

        .hero-left .logo {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px;
            height: 34px;
            margin-right: 10px;
            border-radius: 12px;
            background: rgba(0, 232, 255, 0.10);
            box-shadow: inset 0 0 10px rgba(0,232,255,.18), 0 0 25px rgba(0,232,255,.12);
            color: var(--cyan);
            font-size: 18px;
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

        .pill strong {{
            color: #fff;
        }}

        .pill.online {{
            color: var(--green);
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
            background: rgba(255,255,255,.02);
        }}

        .tab-btn.active {{
            color: var(--cyan);
            border-color: rgba(0, 232, 255, 0.35);
            background: rgba(0,232,255,.08);
            box-shadow: inset 0 0 14px rgba(0,232,255,.09);
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .top-grid,
        .city-top-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 18px;
        }}

        .city-top-grid {{
            grid-template-columns: repeat(4, 1fr);
        }}

        .summary-card,
        .panel,
        .city-card,
        .beat-panel {{
            background: linear-gradient(180deg, rgba(7, 19, 32, 0.95), rgba(4, 14, 24, 0.95));
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: var(--shadow);
        }}

        .summary-card {{
            padding: 18px;
            min-height: 112px;
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

        .summary-sub {{
            margin-top: 8px;
            color: var(--muted);
        }}

        .beat-panel {{
            padding: 16px;
            margin-bottom: 18px;
        }}

        .beat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 14px;
        }}

        .beat-item {{
            padding: 14px;
            border-radius: 14px;
            background: rgba(255,255,255,.02);
            border: 1px solid rgba(255,255,255,.04);
        }}

        .beat-city {{
            font-weight: 800;
            color: var(--green);
            margin-bottom: 8px;
        }}

        .beat-line {{
            display: flex;
            justify-content: space-between;
            gap: 10px;
            color: #b9d8e6;
            padding: 4px 0;
        }}

        .beat-line strong {{
            color: var(--cyan);
        }}

        .muted {{
            color: var(--muted);
        }}

        .panels-grid,
        .city-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .panel-header,
        .city-card-head {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }}

        .panel {{
            padding: 16px;
        }}

        .panel-title,
        .city-card-title {{
            font-size: 1.15rem;
            font-weight: 800;
        }}

        .panel-tag {{
            color: var(--muted);
            font-size: .92rem;
        }}

        .rank-row {{
            display: grid;
            grid-template-columns: 42px 140px 1fr 90px 110px;
            align-items: center;
            gap: 12px;
            padding: 13px 0;
            border-top: 1px solid rgba(255,255,255,.04);
        }}

        .rank-row:first-child {{
            border-top: 0;
        }}

        .rank-pos {{
            width: 32px;
            height: 32px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,.08);
            color: #fff;
            font-weight: 700;
        }}

        .pos-1 {{ background: rgba(245,179,1,.22); color: #ffd45c; }}
        .pos-2 {{ background: rgba(180,196,210,.20); color: #dbe6ef; }}
        .pos-3 {{ background: rgba(165,102,38,.22); color: #ffb56d; }}

        .rank-city {{
            font-weight: 700;
        }}

        .rank-bar,
        .city-progress {{
            height: 10px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(255,255,255,.05);
        }}

        .rank-fill,
        .city-progress-fill {{
            height: 100%;
            border-radius: 999px;
        }}

        .ok {{ color: var(--green); }}
        .warn {{ color: var(--yellow); }}
        .bad {{ color: var(--red); }}

        .rank-fill.ok,
        .city-progress-fill.ok {{
            background: linear-gradient(90deg, #12d99f, #08f0c2);
        }}

        .rank-fill.warn,
        .city-progress-fill.warn {{
            background: linear-gradient(90deg, #f0a500, #f7c52b);
        }}

        .rank-fill.bad,
        .city-progress-fill.bad {{
            background: linear-gradient(90deg, #ff4d7a, #ff6a91);
        }}

        .rank-perc {{
            font-weight: 800;
            text-align: right;
        }}

        .rank-val {{
            text-align: right;
            color: var(--muted);
            font-size: .95rem;
        }}

        .section-title {{
            margin: 22px 0 12px;
            font-size: 1.2rem;
            font-weight: 800;
            color: #fff;
        }}

        .city-card {{
            padding: 16px;
        }}

        .city-card-perc {{
            font-size: 1.6rem;
            font-weight: 800;
        }}

        .city-metrics {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px solid rgba(255,255,255,.05);
        }}

        .city-metrics span {{
            display: block;
            color: var(--muted);
            margin-bottom: 6px;
        }}

        .city-metrics strong {{
            color: #fff;
            font-size: 1rem;
        }}

        footer {{
            margin-top: 26px;
            padding: 18px 0 10px;
            border-top: 1px solid var(--line);
            color: var(--muted);
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
        }}

        @media (max-width: 1100px) {{
            .panels-grid,
            .city-grid,
            .beat-grid,
            .top-grid,
            .city-top-grid {{
                grid-template-columns: 1fr;
            }}

            .rank-row {{
                grid-template-columns: 36px 110px 1fr 80px;
            }}

            .rank-val {{
                display: none;
            }}
        }}

        @media (max-width: 720px) {{
            .hero {{
                flex-direction: column;
            }}

            .hero-left h1 {{
                font-size: 2rem;
            }}

            .city-metrics {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="bg-grid"></div>

    <main class="wrap">
        <header class="hero">
            <div class="hero-left">
                <h1><span class="logo">◎</span>Dashboard de Metas</h1>
                <p>Top Estética Bucal — 9 Unidades</p>
            </div>

            <div class="hero-right">
                <div class="pill"><strong>{mes_texto}</strong></div>
                <div class="pill"><strong>{agora}</strong></div>
                <div class="pill online"><strong>● Online</strong></div>
                <a class="pill btn" href="../data/metas_top_estetica.xlsx" download>⬇ Exportar Planilha</a>
            </div>
        </header>

        <nav class="tabs">
            {''.join(tabs)}
        </nav>

        {ranking_cards}
        {''.join(cidades_html)}

        <footer>
            <div>Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
            <div>Dashboard gerado automaticamente via GitHub Actions</div>
        </footer>
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
    print("Gerando dashboard HTML moderno...")
    dados = carregar_dados()
    html = gerar_html(dados)

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✓ Dashboard gerado com sucesso em docs/index.html")


if __name__ == "__main__":
    main()
