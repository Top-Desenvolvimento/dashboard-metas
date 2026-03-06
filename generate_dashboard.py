#!/usr/bin/env python3
"""
Gera o dashboard HTML atualizado com os dados mais recentes
"""

import json
import os
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Optional

def carregar_dados():
    """Carrega dados do JSON"""
    with open('data/metas_atual.json', 'r', encoding='utf-8') as f:
        return json.load(f)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def _parse_float_money_br(text: str) -> Optional[float]:
    if not text:
        return None
    t = text.replace("R$", "").replace("\u00a0", " ").strip()
    t = t.replace(".", "").replace(",", ".")
    m = re.search(r"(-?\d+(?:\.\d+)?)", t)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _parse_ratio(text: str) -> tuple[Optional[float], Optional[float]]:
    if not text or "/" not in text:
        return None, None
    left, right = [p.strip() for p in text.split("/", 1)]

    if "R$" in left or "R$" in right:
        return _parse_float_money_br(left), _parse_float_money_br(right)

    def _num(x: str) -> Optional[float]:
        m = re.search(r"(\d+)", x.replace(".", ""))
        return float(m.group(1)) if m else None

    return _num(left), _num(right)


def calcular_percentual_por_texto(text: str) -> Optional[float]:
    atual, meta = _parse_ratio(text)
    if atual is None or meta in (None, 0):
        return None
    return (atual / meta) * 100.0


def carregar_index_historico() -> dict[str, Any]:
    path = DATA_DIR / "historico_index.json"
    if not path.exists():
        return {"meses": []}
    return json.loads(path.read_text(encoding="utf-8"))

def gerar_html(dados):
    """Gera o HTML do dashboard"""
    
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
    mes_ano = datetime.now().strftime('%B / %Y')
    mes_key = datetime.now().strftime('%Y-%m')
    idx = carregar_index_historico()
    meses = idx.get("meses") if isinstance(idx, dict) else []
    if not isinstance(meses, list):
        meses = []
    
    # Cabeçalho HTML
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Metas - Top Estética</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        
        h1 {{
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #718096;
            font-size: 1.2em;
        }}
        
        .info-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f7fafc;
            padding: 15px 25px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .status {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .status-dot {{
            width: 12px;
            height: 12px;
            background: #48bb78;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .card {{
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.3s, box-shadow 0.3s;
            position: relative;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .cidade-nome {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2d3748;
        }}
        
        .percentual {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .badge {{
            position: absolute;
            top: 14px;
            right: 14px;
            background: #48bb78;
            color: white;
            font-weight: 700;
            font-size: 0.8em;
            padding: 6px 10px;
            border-radius: 999px;
            box-shadow: 0 10px 20px rgba(72, 187, 120, 0.35);
            transform: rotate(2deg);
            animation: pop 1.5s ease-in-out infinite;
        }}

        @keyframes pop {{
            0%, 100% {{ transform: rotate(2deg) scale(1); }}
            50% {{ transform: rotate(-2deg) scale(1.03); }}
        }}

        .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 18px;
        }}

        .select {{
            display: flex;
            align-items: center;
            gap: 10px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 10px 12px;
        }}

        select {{
            border: none;
            outline: none;
            font-size: 0.95em;
            background: transparent;
        }}
        
        .meta-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .meta-item:last-child {{
            border-bottom: none;
        }}
        
        .meta-label {{
            color: #718096;
            font-size: 0.9em;
        }}
        
        .meta-valor {{
            font-weight: bold;
            color: #2d3748;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
            transition: width 1s ease;
        }}
        
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Dashboard de Metas</h1>
            <p class="subtitle">Top Estética Bucal — 9 Unidades</p>
            <p class="subtitle">{mes_ano}</p>
        </header>
        
        <div class="topbar">
            <div class="info-bar" style="flex: 1;">
                <div class="status">
                    <div class="status-dot"></div>
                    <span><strong>{timestamp}</strong></span>
                </div>
                <div>
                    <span>🏆 Unidades: <strong>9 cidades</strong></span>
                </div>
            </div>
            <div class="select">
                <span><strong>📅 Mês</strong></span>
                <select id="mesSelect">
                    <option value="atual">Atual</option>
                    {''.join([f'<option value="{m}">{m}</option>' for m in meses])}
                </select>
                <a id="downloadJson" href="data/metas_atual.json" style="margin-left:8px; text-decoration:none; color:#667eea; font-weight:700;">Baixar JSON</a>
                <a id="downloadPptx" href="exports/{mes_key}/dashboard_metas_{mes_key}_latest.pptx" style="margin-left:8px; text-decoration:none; color:#2d3748; font-weight:700;">Baixar PPTX</a>
                <a href="admin.html" style="margin-left:8px; text-decoration:none; color:#764ba2; font-weight:700;">Admin Google</a>
            </div>
        </div>
        
        <div id="summary" class="info-bar" style="margin-bottom: 10px;">
            <div>
                <div style="font-weight:700; color:#2d3748;">Resumo do mês</div>
                <div style="color:#718096; font-size: 0.95em;" id="summaryText">Carregando…</div>
            </div>
            <div style="color:#718096; font-size:0.95em;" id="compareText"></div>
        </div>

        <div class="grid" id="grid">
'''
    
    # Gera cards para cada cidade (render inicial; ao trocar o mês, o JS re-renderiza)
    for cidade, info in dados.items():
        ortho = info.get("metas_financeiras", {}).get("ortodontia", "—")
        clinico = info.get("metas_financeiras", {}).get("clinico_geral", "—")
        prof = info.get("metas_servicos", {}).get("profilaxia", "—")
        rest = info.get("metas_servicos", {}).get("restauracao", "—")
        novas = info.get("avaliacoes", {}).get("novas", 0)

        p_prof = calcular_percentual_por_texto(prof) or 0
        p_rest = calcular_percentual_por_texto(rest) or 0
        percent_top = max(p_prof, p_rest)
        percent_txt = f"{percent_top:.0f}%" if percent_top else "---%"

        bateu = (p_prof >= 100) or (p_rest >= 100)
        bar = min(120, max(0, percent_top))

        html += f'''
            <div class="card">
                {('<div class="badge">META BATIDA</div>' if bateu else '')}
                <div class="card-header">
                    <span class="cidade-nome">{cidade}</span>
                    <span class="percentual">{percent_txt}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">Ortodontia</span>
                    <span class="meta-valor">{ortho}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">Clínico Geral</span>
                    <span class="meta-valor">{clinico}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">Profilaxia</span>
                    <span class="meta-valor">{prof}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">Restauração</span>
                    <span class="meta-valor">{rest}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">⭐ Novas Avaliações</span>
                    <span class="meta-valor">{novas}</span>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {bar:.0f}%"></div>
                </div>
            </div>
'''
    
    # Rodapé
    html += f'''
        </div>
        
        <footer>
            <p>Última atualização: {timestamp}</p>
            <p>Top Estética Bucal — Sistema de Metas</p>
            <p>🤖 Atualizado automaticamente (coleta + geração do HTML)</p>
        </footer>
    </div>

<script>
async function loadJson(path) {
  const r = await fetch(path, {cache: "no-store"});
  if (!r.ok) throw new Error("Falha ao carregar " + path);
  return await r.json();
}

function pctFromRatio(text) {
  if (!text || typeof text !== "string") return null;
  const parts = text.split("/");
  if (parts.length < 2) return null;
  const left = parts[0].replace(/[^0-9]/g, "");
  const right = parts[1].replace(/[^0-9]/g, "");
  const a = parseFloat(left);
  const m = parseFloat(right);
  if (!a || !m) return null;
  return (a / m) * 100;
}

function parseRatio(text) {
  if (!text || typeof text !== "string") return null;
  const parts = text.split("/");
  if (parts.length < 2) return null;
  const left = parts[0].replace(/[^0-9]/g, "");
  const right = parts[1].replace(/[^0-9]/g, "");
  const a = parseFloat(left);
  const m = parseFloat(right);
  if (Number.isNaN(a) || Number.isNaN(m)) return null;
  return {a, m};
}

function computeSummary(dados) {
  const entries = Object.entries(dados || {});
  let novasTotal = 0;
  let profA = 0, profM = 0, restA = 0, restM = 0;
  for (const [, info] of entries) {
    const novas = (info.avaliacoes && info.avaliacoes.novas) ?? 0;
    novasTotal += Number(novas) || 0;
    const prof = (info.metas_servicos && info.metas_servicos.profilaxia) || "";
    const rest = (info.metas_servicos && info.metas_servicos.restauracao) || "";
    const r1 = parseRatio(prof);
    const r2 = parseRatio(rest);
    if (r1) { profA += r1.a; profM += r1.m; }
    if (r2) { restA += r2.a; restM += r2.m; }
  }
  const profPct = profM ? Math.round((profA/profM)*100) : null;
  const restPct = restM ? Math.round((restA/restM)*100) : null;
  return {novasTotal, profA, profM, profPct, restA, restM, restPct};
}

function renderSummary(dados, labelMes) {
  const s = computeSummary(dados);
  const el = document.getElementById("summaryText");
  const p1 = (s.profPct == null) ? "—" : `${s.profA} / ${s.profM} (${s.profPct}%)`;
  const p2 = (s.restPct == null) ? "—" : `${s.restA} / ${s.restM} (${s.restPct}%)`;
  el.textContent = `${labelMes} | ⭐ Novas avaliações (total): ${s.novasTotal} | Profilaxia: ${p1} | Restauração: ${p2}`;
}

function renderGrid(dados) {
  const grid = document.getElementById("grid");
  const entries = Object.entries(dados || {});
  entries.sort((a,b) => a[0].localeCompare(b[0], "pt-BR"));
  grid.innerHTML = entries.map(([cidade, info]) => {
    const ortho = (info.metas_financeiras && info.metas_financeiras.ortodontia) || "—";
    const clinico = (info.metas_financeiras && info.metas_financeiras.clinico_geral) || "—";
    const prof = (info.metas_servicos && info.metas_servicos.profilaxia) || "—";
    const rest = (info.metas_servicos && info.metas_servicos.restauracao) || "—";
    const novas = (info.avaliacoes && info.avaliacoes.novas) ?? 0;
    const p1 = pctFromRatio(prof) || 0;
    const p2 = pctFromRatio(rest) || 0;
    const top = Math.max(p1, p2);
    const bateu = (p1 >= 100) || (p2 >= 100);
    const bar = Math.min(120, Math.max(0, top));
    const pct = top ? `${Math.round(top)}%` : "---%";
    return `
      <div class="card">
        ${bateu ? '<div class="badge">META BATIDA</div>' : ''}
        <div class="card-header">
          <span class="cidade-nome">${cidade}</span>
          <span class="percentual">${pct}</span>
        </div>
        <div class="meta-item"><span class="meta-label">Ortodontia</span><span class="meta-valor">${ortho}</span></div>
        <div class="meta-item"><span class="meta-label">Clínico Geral</span><span class="meta-valor">${clinico}</span></div>
        <div class="meta-item"><span class="meta-label">Profilaxia</span><span class="meta-valor">${prof}</span></div>
        <div class="meta-item"><span class="meta-label">Restauração</span><span class="meta-valor">${rest}</span></div>
        <div class="meta-item"><span class="meta-label">⭐ Novas Avaliações</span><span class="meta-valor">${novas}</span></div>
        <div class="progress-bar"><div class="progress-fill" style="width:${bar}%"></div></div>
      </div>
    `;
  }).join("");
}

document.getElementById("mesSelect").addEventListener("change", async (e) => {
  const v = e.target.value;
  const dl = document.getElementById("downloadJson");
  const pptx = document.getElementById("downloadPptx");
  const cmp = document.getElementById("compareText");
  try {
    if (v === "atual") {
      const dados = await loadJson("data/metas_atual.json");
      dl.href = "data/metas_atual.json";
      const mesAtual = (dados && Object.values(dados)[0] && dados[Object.keys(dados)[0]].avaliacoes && dados[Object.keys(dados)[0]].avaliacoes.mes) || null;
      if (mesAtual) pptx.href = `exports/${mesAtual}/dashboard_metas_${mesAtual}_latest.pptx`;
      renderSummary(dados, mesAtual ? `Mês ${mesAtual}` : "Atual");
      cmp.textContent = "";
      renderGrid(dados);
      return;
    }
    const monthPayload = await loadJson(`data/meses/${v}.json`);
    dl.href = `data/meses/${v}.json`;
    pptx.href = `exports/${v}/dashboard_metas_${v}_latest.pptx`;
    const dadosMes = monthPayload.dados || monthPayload;
    renderSummary(dadosMes, `Mês ${v}`);
    renderGrid(dadosMes);

    // comparação simples com mês anterior (se existir)
    try {
      const idx = await loadJson("data/historico_index.json");
      const meses = (idx && idx.meses) || [];
      const i = meses.indexOf(v);
      if (i > 0) {
        const prev = meses[i-1];
        const prevPayload = await loadJson(`data/meses/${prev}.json`);
        const prevDados = prevPayload.dados || prevPayload;
        const curS = computeSummary(dadosMes);
        const prevS = computeSummary(prevDados);
        const delta = curS.novasTotal - prevS.novasTotal;
        cmp.textContent = `Comparação com ${prev}: Δ novas avaliações (total) = ${delta >= 0 ? "+" : ""}${delta}`;
      } else {
        cmp.textContent = "";
      }
    } catch (e) {
      cmp.textContent = "";
    }
  } catch (err) {
    console.error(err);
    alert("Não consegui carregar os dados do mês selecionado. Verifique se o arquivo existe em data/meses/.");
  }
});

// inicializa resumo ao abrir a página
(async () => {
  try {
    const dados = await loadJson("data/metas_atual.json");
    const mesAtual = (dados && Object.values(dados)[0] && dados[Object.keys(dados)[0]].avaliacoes && dados[Object.keys(dados)[0]].avaliacoes.mes) || null;
    renderSummary(dados, mesAtual ? `Mês ${mesAtual}` : "Atual");
  } catch (e) {
    const el = document.getElementById("summaryText");
    if (el) el.textContent = "Sem dados carregados ainda.";
  }
})();
</script>
</body>
</html>
'''
    
    return html

def main():
    """Função principal"""
    print("Gerando dashboard HTML...")
    
    # Carrega dados
    dados = carregar_dados()
    
    # Gera HTML
    html = gerar_html(dados)
    
    # Salva em docs/ para GitHub Pages
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Copia dados necessários para o seletor de mês funcionar no GitHub Pages
    try:
        os.makedirs('docs/data', exist_ok=True)
        for rel in [
            'data/metas_atual.json',
            'data/historico_index.json',
            'data/google_baselines.json',
        ]:
            if os.path.exists(rel):
                Path('docs').joinpath(rel).parent.mkdir(parents=True, exist_ok=True)
                Path('docs').joinpath(rel).write_text(Path(rel).read_text(encoding='utf-8'), encoding='utf-8')

        # copia pasta data/meses
        meses_src = DATA_DIR / "meses"
        if meses_src.exists():
            for p in meses_src.glob("*.json"):
                dst = Path("docs") / "data" / "meses" / p.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as e:
        print(f"Atenção: não consegui copiar arquivos de data/ para docs/: {e}")
    
    print("✓ Dashboard HTML gerado com sucesso em docs/index.html")

if __name__ == '__main__':
    main()
