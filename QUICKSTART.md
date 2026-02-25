#!/usr/bin/env python3
"""
Gera o dashboard HTML atualizado com os dados mais recentes
"""

import json
import os
from datetime import datetime

def carregar_dados():
    """Carrega dados do JSON"""
    with open('data/metas_atual.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def calcular_percentual(atual, meta):
    """Calcula percentual de atingimento da meta"""
    try:
        atual_num = float(atual.replace('R$', '').replace('.', '').replace(',', '.').strip())
        meta_num = float(meta)
        return (atual_num / meta_num) * 100
    except:
        return 0

def gerar_html(dados):
    """Gera o HTML do dashboard"""
    
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
    mes_ano = datetime.now().strftime('%B / %Y')
    
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
        
        <div class="info-bar">
            <div class="status">
                <div class="status-dot"></div>
                <span><strong>{timestamp}</strong></span>
            </div>
            <div>
                <span>🏆 Unidades: <strong>9 cidades</strong></span>
            </div>
        </div>
        
        <div class="grid">
'''
    
    # Gera cards para cada cidade
    for cidade, info in dados.items():
        # Calcula percentuais (simplificado - ajuste conforme suas metas reais)
        ortho = info['metas_financeiras'].get('ortodontia', 'R$ 0')
        clinico = info['metas_financeiras'].get('clinico_geral', 'R$ 0')
        
        html += f'''
            <div class="card">
                <div class="card-header">
                    <span class="cidade-nome">{cidade}</span>
                    <span class="percentual">---%</span>
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
                    <span class="meta-valor">{info['metas_servicos'].get('profilaxia', '0')}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">Restauração</span>
                    <span class="meta-valor">{info['metas_servicos'].get('restauracao', '0')}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">⭐ Novas Avaliações</span>
                    <span class="meta-valor">{info['avaliacoes']['novas']}</span>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 75%"></div>
                </div>
            </div>
'''
    
    # Rodapé
    html += f'''
        </div>
        
        <footer>
            <p>Última atualização: {timestamp}</p>
            <p>Top Estética Bucal — Sistema de Metas</p>
            <p>🤖 Atualizado automaticamente a cada hora via GitHub Actions</p>
        </footer>
    </div>
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
    
    print("✓ Dashboard HTML gerado com sucesso em docs/index.html")

if __name__ == '__main__':
    main()
