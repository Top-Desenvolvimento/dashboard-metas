#!/usr/bin/env python3
"""
Gera dashboard HTML usando apenas dados reais do JSON.
Sem estimar metas.
"""

import json
import os
import re
from datetime import datetime


def carregar_dados():
    with open("data/metas_atual.json", "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_config_google():
    caminho = "data/config_google.json"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


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
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto


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


def valor_percentual(texto):
    if texto is None:
        return 0.0
    t = str(texto).replace("%", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(t)
    except Exception:
        return 0.0


def classe_status(percentual):
    if percentual >= 100:
        return "ok"
    if percentual >= 70:
        return "warn"
    return "bad"


def garantir_valor(valor):
    return valor if str(valor).strip() else "0"


def processar_dados(dados, config_google):
    cidades = []

    for cidade, info in dados.items():
        indicadores = info.get("indicadores", {})
        mes_referencia = info.get("mes_referencia", "")

        # injeta meta manual do Google, se existir
        google_meta_manual = (
            config_google.get(mes_referencia, {}).get(cidade)
            if config_google.get(mes_referencia)
            else None
        )

        if google_meta_manual is not None:
            real = indicadores.get("avaliacoes_google", {}).get("ate_o_momento", "0")
            try:
                real_int = int(str(real).replace(".", "").replace(",", "").strip())
            except Exception:
                real_int = 0
            falta = max(int(google_meta_manual) - real_int, 0)
            progresso = (real_int / int(google_meta_manual) * 100) if int(google_meta_manual) > 0 else 0

            indicadores["avaliacoes_google"] = {
                "meta": str(google_meta_manual),
                "ate_o_momento": str(real_int),
                "falta": str(falta),
                "progresso": f"{progresso:.1f}%".replace(".", ","),
            }

        percentuais = []
        for valores in indicadores.values():
            percentuais.append(valor_percentual(valores.get("progresso", "0%")))

        progresso_geral = sum(percentuais) / len(percentuais) if percentuais else 0

        cidades.append({
            "cidade": cidade,
            "slug": slug(cidade),
            "mes_referencia": mes_referencia,
            "timestamp": info.get("timestamp", ""),
            "indicadores": indicadores,
            "progresso_geral": progresso_geral,
        })

    cidades.sort(key=lambda x: x["progresso_geral"], reverse=True)
    return cidades


def render_indicador(nome, dados):
    perc = valor_percentual(dados.get("progresso", "0%"))
    status = classe_status(perc)
    largura = min(max(perc, 0), 100)

    return f"""
    <section class="city-card">
        <div class="city-card-head">
            <div class="city-card-title">{nome}</div>
            <div class="city-card-perc {status}">{garantir_valor(dados.get("progresso", "0%"))}</div>
        </div>

        <div class="city-progress">
            <div class="city-progress-fill {status}" style="width:{largura}%"></div>
        </div>

        <div class="city-metrics">
            <div><span>Meta:</span><strong>{garantir_valor(dados.get("meta", "0"))}</strong></div>
            <div><span>Até o momento:</span><strong>{garantir_valor(dados.get("ate_o_momento", "0"))}</strong></div>
            <div><span>Falta:</span><strong>{garantir_valor(dados.get("falta", "0"))}</strong></div>
        </div>
    </section>
    """


def gerar_html(cidades):
    mes = cidades[0]["mes_referencia"] if cidades else ""
    mes_texto = mes_label(mes)
    agora = datetime.now().strftime("%H:%M:%S")

    tabs = ['<button class="tab-btn active" data-tab="ranking-geral">🏆 Ranking Geral</button>']
    for c in cidades:
        tabs.append(f'<button class="tab-btn" data-tab="{c["slug"]}">📍 {c["cidade"]}</button>')

    ranking_cards = []
    for c in cidades:
        ranking_cards.append(f"""
        <div class="beat-item">
            <div class="beat-city">{c["cidade"]}</div>
            <div class="beat-line">Progresso geral <strong>{c["progresso_geral"]:.1f}%</strong></div>
        </div>
        """)

    cidades_html = []
    for c in cidades:
        i = c["indicadores"]

        cidades_html.append(f"""
        <div id="{c["slug"]}" class="tab-content">
            <section class="city-top-grid">
                <div class="summary-card">
                    <div class="summary-label">Mês de Referência</div>
                    <div class="summary-value">{mes_texto}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Progresso Geral</div>
                    <div class="summary-value">{c["progresso_geral"]:.1f}%</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Cidade</div>
                    <div class="summary-value">{c["cidade"]}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Atualizado em</div>
                    <div class="summary-value">{agora}</div>
                </div>
            </section>

            <div class="section-title">💰 Metas Financeiras</div>
            <div class="city-grid">
                {render_indicador("Ortodontia", i.get("ortodontia", {}))}
                {render_indicador("Clínico Geral", i.get("clinico_geral", {}))}
            </div>

            <div class="section-title">⚡ Metas de Serviços</div>
            <div class="city-grid">
                {render_indicador("Avaliações Google", i.get("avaliacoes_google", {}))}
                {render_indicador("Meta de Avaliação", i.get("meta_avaliacao", {}))}
                {render_indicador("Meta de Profilaxia", i.get("meta_profilaxia", {}))}
                {render_indicador("Meta de Restauração", i.get("meta_restauracao", {}))}
            </div>
        </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Dashboard de Metas - Top Estética</title>
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
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: Inter, Segoe UI, Arial, sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at top left, rgba(0, 232, 255, 0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(16, 224, 163, 0.08), transparent 25%),
        linear-gradient(180deg, #02060d, #04101b 45%, #02070d 100%);
    min-height: 100vh;
}}
.wrap {{ max-width: 1440px; margin: 0 auto; padding: 16px; }}
.hero {{
    display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; padding: 8px 0 24px;
}}
.hero-left h1 {{
    font-size: 2.8rem; font-weight: 800; line-height: 1.05; text-shadow: 0 0 18px rgba(0, 232, 255, 0.18);
}}
.hero-left p {{ margin-top: 8px; color: var(--muted); font-size: 1.05rem; }}
.hero-right {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
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
    color: #031018; font-weight: 700;
}}
.tabs {{
    display: flex; align-items: center; gap: 8px; overflow-x: auto; padding: 10px 0 16px;
    border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); margin-bottom: 20px;
}}
.tab-btn {{
    background: transparent; color: var(--muted); border: 1px solid transparent; border-radius: 12px;
    padding: 10px 14px; cursor: pointer; white-space: nowrap; transition: .2s ease; font-weight: 600;
}}
.tab-btn.active {{
    color: var(--cyan); border-color: rgba(0, 232, 255, 0.35);
    background: rgba(0,232,255,.08); box-shadow: inset 0 0 14px rgba(0,232,255,.09);
}}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.top-grid, .city-top-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 18px;
}}
.summary-card, .city-card, .beat-panel {{
    background: linear-gradient(180deg, rgba(7, 19, 32, 0.95), rgba(4, 14, 24, 0.95));
    border: 1px solid var(--border); border-radius: 18px; box-shadow: var(--shadow);
}}
.summary-card {{ padding: 18px; min-height: 112px; }}
.summary-label {{
    color: var(--muted); font-size: .85rem; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 12px;
}}
.summary-value {{ font-size: 2rem; font-weight: 800; color: var(--cyan); }}
.beat-panel {{ padding: 16px; margin-bottom: 18px; }}
.beat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 14px; }}
.beat-item {{
    padding: 14px; border-radius: 14px; background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.04);
}}
.beat-city {{ font-weight: 800; color: var(--green); margin-bottom: 8px; }}
.beat-line {{ display: flex; justify-content: space-between; gap: 10px; color: #b9d8e6; padding: 4px 0; }}
.city-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
.city-card {{ padding: 16px; }}
.city-card-head {{
    display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px;
}}
.city-card-title {{ font-size: 1.15rem; font-weight: 800; }}
.city-card-perc {{ font-size: 1.6rem; font-weight: 800; }}
.city-progress {{
    height: 10px; border-radius: 999px; overflow: hidden; background: rgba(255,255,255,.05);
}}
.city-progress-fill {{ height: 100%; border-radius: 999px; }}
.ok {{ color: var(--green); }}
.warn {{ color: var(--yellow); }}
.bad {{ color: var(--red); }}
.city-progress-fill.ok {{ background: linear-gradient(90deg, #12d99f, #08f0c2); }}
.city-progress-fill.warn {{ background: linear-gradient(90deg, #f0a500, #f7c52b); }}
.city-progress-fill.bad {{ background: linear-gradient(90deg, #ff4d7a, #ff6a91); }}
.city-metrics {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; padding-top: 14px;
    border-top: 1px solid rgba(255,255,255,.05);
}}
.city-metrics span {{ display: block; color: var(--muted); margin-bottom: 6px; }}
.city-metrics strong {{ color: #fff; font-size: 1rem; }}
.section-title {{ margin: 22px 0 12px; font-size: 1.2rem; font-weight: 800; color: #fff; }}
@media (max-width: 1100px) {{
    .city-grid, .beat-grid, .top-grid, .city-top-grid {{ grid-template-columns: 1fr; }}
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
        <section class="top-grid">
            <div class="summary-card">
                <div class="summary-label">Unidades</div>
                <div class="summary-value">{len(cidades)}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Melhor desempenho</div>
                <div class="summary-value">{cidades[0]["cidade"] if cidades else '-'}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Mês de referência</div>
                <div class="summary-value">{mes_texto}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Atualizado</div>
                <div class="summary-value">{agora}</div>
            </div>
        </section>

        <section class="beat-panel">
            <div class="section-title">Metas por cidade</div>
            <div class="beat-grid">
                {''.join(ranking_cards)}
            </div>
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
</html>"""


def main():
    print("Gerando dashboard HTML...")
    dados = carregar_dados()
    config_google = carregar_config_google()
    cidades = processar_dados(dados, config_google)

    html = gerar_html(cidades)

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✓ Dashboard gerado com sucesso em docs/index.html")


if __name__ == "__main__":
    main()
