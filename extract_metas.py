#!/usr/bin/env python3
"""
Script de extração de metas da Top Estética Bucal
Coleta dados de 9 cidades e avaliações do Google
"""

import os
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# Configurações
LOGIN_USER = os.environ.get('LOGIN_USER', 'MANUS')
LOGIN_PASS = os.environ.get('LOGIN_PASS', 'MANUS2026')

# URLs das 9 cidades
CIDADES = {
    'Caxias': 'http://caxias.topesteticabucal.com.br/sistema',
    'Farroupilha': 'http://farroupilha.topesteticabucal.com.br/sistema',
    'Bento': 'http://bento.topesteticabucal.com.br/sistema',
    'Encantado': 'https://encantado.topesteticabucal.com.br/sistema',
    'Soledade': 'http://soledade.topesteticabucal.com.br/sistema',
    'Garibaldi': 'http://garibaldi.topesteticabucal.com.br/sistema',
    'Veranópolis': 'http://veranopolis.topesteticabucal.com.br/sistema',
    'SS do Caí': 'https://ssdocai.topesteticabucal.com.br/sistema',
    'Flores': 'https://flores.topesteticabucal.com.br/sistema'
}

# URLs de avaliações do Google (na ordem das cidades)
GOOGLE_REVIEWS = [
    'https://share.google/3f8yPEfrb24AQYYOp',   # Caxias
    'https://share.google/ffSPadgdvp8WUEXq0',   # Farroupilha
    'https://share.google/g1snAopsGqM5I8sOl',   # Bento
    'https://share.google/sEdZu4jHIPYL77RA6',   # Encantado
    'https://share.google/5CUABlRksD1cPYWiK',   # Soledade
    'https://share.google/rOGEnBONHO2kTYVk3',   # Garibaldi
    'https://share.google/UlnGSp8MES2AnB7Yz',   # Veranópolis
    'https://share.google/33XgmkKW7UnW8o8WB',   # SS do Caí
    'https://share.google/U2cO3MWeXsKQZUenB'    # Flores
]

# Valores iniciais de avaliações (antes da meta começar)
AVALIACOES_INICIAIS = {
    'Caxias': 285,
    'Flores': 94,
    'Farroupilha': 173,
    'Bento': 76,
    'Encantado': 206,
    'Soledade': 413,
    'Garibaldi': 128,
    'Veranópolis': 128,
    'SS do Caí': 88
}

from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.service import Service

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')

    service = Service('/usr/bin/chromedriver')

    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver
def fazer_login(driver, url):
    """Faz login no sistema da clínica"""
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        # Aguarda campos de login
        username_field = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        password_field = driver.find_element(By.NAME, 'password')
        
        # Preenche credenciais
        username_field.send_keys(LOGIN_USER)
        password_field.send_keys(LOGIN_PASS)
        
        # Submete formulário
        password_field.submit()
        
        # Aguarda carregamento
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Erro no login: {e}")
        return False

def extrair_metas_financeiras(driver):
    """Extrai dados de metas financeiras"""
    try:
        # Navega para página de metas financeiras
        driver.find_element(By.LINK_TEXT, 'Metas Financeiras').click()
        time.sleep(2)
        
        # Extrai dados (ajuste os seletores conforme seu sistema)
        ortodontia = driver.find_element(By.ID, 'ortodontia_valor').text
        clinico = driver.find_element(By.ID, 'clinico_valor').text
        
        return {
            'ortodontia': ortodontia,
            'clinico_geral': clinico
        }
    except Exception as e:
        print(f"Erro ao extrair metas financeiras: {e}")
        return {}

def extrair_metas_servicos(driver):
    """Extrai dados de metas de serviços"""
    try:
        # Navega para página de serviços
        driver.find_element(By.LINK_TEXT, 'Metas de Serviços').click()
        time.sleep(2)
        
        # Extrai dados (ajuste os seletores conforme seu sistema)
        profilaxia = driver.find_element(By.ID, 'profilaxia').text
        restauracao = driver.find_element(By.ID, 'restauracao').text
        
        return {
            'profilaxia': profilaxia,
            'restauracao': restauracao
        }
    except Exception as e:
        print(f"Erro ao extrair metas de serviços: {e}")
        return {}

def obter_avaliacoes_google(url):
    """Obtém número de avaliações do Google"""
    try:
        # Aqui você pode implementar web scraping ou usar API do Google
        # Por enquanto retorna valor simulado
        response = requests.get(url, timeout=10)
        # Implementar parsing conforme estrutura da página
        return 0
    except Exception as e:
        print(f"Erro ao obter avaliações do Google: {e}")
        return 0

def coletar_dados_todas_cidades():
    """Coleta dados de todas as 9 cidades"""
    driver = setup_driver()
    dados = {}
    
    try:
        for idx, (cidade, url) in enumerate(CIDADES.items()):
            print(f"Coletando dados de {cidade}...")
            
            if fazer_login(driver, url):
                metas_financeiras = extrair_metas_financeiras(driver)
                metas_servicos = extrair_metas_servicos(driver)
                
                # Coleta avaliações do Google
                avaliacoes_atual = obter_avaliacoes_google(GOOGLE_REVIEWS[idx])
                avaliacoes_inicial = AVALIACOES_INICIAIS[cidade]
                avaliacoes_novas = avaliacoes_atual - avaliacoes_inicial
                
                dados[cidade] = {
                    'metas_financeiras': metas_financeiras,
                    'metas_servicos': metas_servicos,
                    'avaliacoes': {
                        'inicial': avaliacoes_inicial,
                        'atual': avaliacoes_atual,
                        'novas': avaliacoes_novas
                    },
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"Falha ao coletar dados de {cidade}")
                
    finally:
        driver.quit()
    
    return dados

def salvar_json(dados):
    """Salva dados em JSON"""
    output_path = 'data/metas_atual.json'
    os.makedirs('data', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    print(f"JSON salvo em: {output_path}")

def salvar_csv(dados):
    """Salva histórico em CSV"""
    output_path = 'data/historico_metas.csv'
    os.makedirs('data', exist_ok=True)
    
    # Prepara dados para CSV
    rows = []
    for cidade, info in dados.items():
        row = {
            'cidade': cidade,
            'timestamp': info['timestamp'],
            'ortodontia': info['metas_financeiras'].get('ortodontia', ''),
            'clinico_geral': info['metas_financeiras'].get('clinico_geral', ''),
            'profilaxia': info['metas_servicos'].get('profilaxia', ''),
            'restauracao': info['metas_servicos'].get('restauracao', ''),
            'avaliacoes_novas': info['avaliacoes']['novas']
        }
        rows.append(row)
    
    # Append ao CSV existente ou cria novo
    df = pd.DataFrame(rows)
    if os.path.exists(output_path):
        df.to_csv(output_path, mode='a', header=False, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"CSV atualizado em: {output_path}")

def gerar_excel(dados):
    """Gera planilha Excel formatada"""
    output_path = 'data/metas_top_estetica.xlsx'
    
    # Cria DataFrames
    df_financeiro = []
    df_servicos = []
    df_avaliacoes = []
    
    for cidade, info in dados.items():
        df_financeiro.append({
            'Cidade': cidade,
            'Ortodontia': info['metas_financeiras'].get('ortodontia', ''),
            'Clínico Geral': info['metas_financeiras'].get('clinico_geral', '')
        })
        
        df_servicos.append({
            'Cidade': cidade,
            'Profilaxia': info['metas_servicos'].get('profilaxia', ''),
            'Restauração': info['metas_servicos'].get('restauracao', '')
        })
        
        df_avaliacoes.append({
            'Cidade': cidade,
            'Avaliações Iniciais': info['avaliacoes']['inicial'],
            'Avaliações Atuais': info['avaliacoes']['atual'],
            'Novas Avaliações': info['avaliacoes']['novas']
        })
    
    # Salva em Excel com múltiplas abas
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        pd.DataFrame(df_financeiro).to_excel(writer, sheet_name='Metas Financeiras', index=False)
        pd.DataFrame(df_servicos).to_excel(writer, sheet_name='Metas Serviços', index=False)
        pd.DataFrame(df_avaliacoes).to_excel(writer, sheet_name='Avaliações Google', index=False)
    
    print(f"Excel gerado em: {output_path}")

def main():
    """Função principal"""
    print("=" * 60)
    print("Iniciando coleta de dados - Top Estética Bucal")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Coleta dados
    dados = coletar_dados_todas_cidades()
    
    if dados:
        # Salva em diferentes formatos
        salvar_json(dados)
        salvar_csv(dados)
        gerar_excel(dados)
        
        print("\n✓ Coleta concluída com sucesso!")
        print(f"Total de cidades processadas: {len(dados)}")
    else:
        print("\n✗ Nenhum dado foi coletado!")
        exit(1)

if __name__ == '__main__':
    main()
