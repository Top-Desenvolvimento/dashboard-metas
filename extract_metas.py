"""
Script de extração automática de metas do sistema Top Estética Bucal.
Acessa 9 unidades via web scraping, extrai dados de metas financeiras e de serviços,
e gera uma planilha Excel com abas por cidade + aba de ranking.
"""

import os
import json
import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Configurações
USERNAME = os.getenv("SYSTEM_LOGIN")
PASSWORD = os.getenv("SYSTEM_PASSWORD")
OUTPUT_DIR = "."
EXCEL_PATH = os.path.join("data", "metas_top_estetica.xlsx")
CSV_HISTORY_PATH = os.path.join("data", "historico_metas.csv")
JSON_CURRENT_PATH = os.path.join("data", "current_metas.json")

CIDADES = [
    {"nome": "Flores", "url": "http://flores.topesteticabucal.com.br/sistema"},
    {"nome": "Caxias", "url": "http://caxias.topesteticabucal.com.br/sistema"},
    {"nome": "Farroupilha", "url": "http://farroupilha.topesteticabucal.com.br/sistema"},
    {"nome": "Bento", "url": "http://bento.topesteticabucal.com.br/sistema"},
    {"nome": "Encantado", "url": "https://encantado.topesteticabucal.com.br/sistema"},
    {"nome": "Soledade", "url": "http://soledade.topesteticabucal.com.br/sistema"},
    {"nome": "Garibaldi", "url": "http://garibaldi.topesteticabucal.com.br/sistema"},
    {"nome": "Veranópolis", "url": "http://veranopolis.topesteticabucal.com.br/sistema"},
    {"nome": "SS do Caí", "url": "https://ssdocai.topesteticabucal.com.br/sistema/"},
]


def extract_city_data(page, cidade_info):
    """Extrai dados de metas de uma cidade."""
    nome = cidade_info["nome"]
    base_url = cidade_info["url"]

    try:
        # Login
        page.goto(base_url, timeout=30000)
        page.fill("#usuario", USERNAME)
        page.fill("#senha", PASSWORD)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle", timeout=15000)

        # Navegar para Metas
        metas_url = base_url.rstrip("/") + "/index2.php?conteudo=lista_metas"
        if base_url.endswith("/sistema/"):
            metas_url = base_url + "index2.php?conteudo=lista_metas"
        page.goto(metas_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)

        # Extrair dados
        data = page.evaluate("""() => {
            const tables = Array.from(document.querySelectorAll('table'));
            return tables.map(table => {
                return Array.from(table.querySelectorAll('tr')).map(tr => {
                    return Array.from(tr.querySelectorAll('td, th')).map(td => td.innerText.trim());
                });
            });
        }""")

        mes_ano = page.evaluate("""() => {
            const select = document.getElementById('mes_ano');
            if (select) {
                const selected = select.options[select.selectedIndex];
                return selected ? selected.text : 'N/A';
            }
            return 'N/A';
        }""")

        # Processar
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = []

        if len(data) > 0:
            t1 = data[0]
            for i in range(0, len(t1), 3):
                if i + 2 < len(t1) and len(t1[i + 2]) >= 5:
                    rows.append({
                        "Data/Hora": timestamp,
                        "Cidade": nome,
                        "Mês/Ano": mes_ano,
                        "Tipo": "Financeiro",
                        "Nome": t1[i][0],
                        "Meta": t1[i + 2][1],
                        "Realizado": t1[i + 2][2],
                        "Falta": t1[i + 2][3],
                        "Progresso": t1[i + 2][4],
                    })
if len(data) > 1:
    t2 = data[1]
    for i in range(0, len(t2), 3):
        if i + 2 < len(t2) and len(t2[i + 2]) >= 5:
            rows.append({
                "Data/Hora": timestamp,
                "Cidade": nome,
                "Mês/Ano": mes_ano,
                "Tipo": "Serviços",
                "Nome": t2[i][0],
                "Meta": t2[i + 2][1],
                "Realizado": t2[i + 2][2],
                "Falta": t2[i + 2][3],
                "Progresso": t2[i + 2][4],
            })
                "Progresso": t2[i + 2][4],
            })
