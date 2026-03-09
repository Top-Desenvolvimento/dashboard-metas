#!/usr/bin/env python3
"""
Script de extração de metas da Top Estética Bucal
Coleta dados de 9 cidades e avaliações do Google
"""

import os
import json
import time
from datetime import datetime

import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# =========================
# CONFIGURAÇÕES
# =========================

LOGIN_USER = os.environ.get("LOGIN_USER", "")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "")

# Fixe fevereiro no workflow com MES_REFERENCIA=2026-02
MES_REFERENCIA = os.environ.get("MES_REFERENCIA", datetime.now().strftime("%Y-%m"))

# URLs das 9 cidades
CIDADES = {
    "Caxias": "http://caxias.topesteticabucal.com.br/sistema",
    "Farroupilha": "http://farroupilha.topesteticabucal.com.br/sistema",
    "Bento": "http://bento.topesteticabucal.com.br/sistema",
    "Encantado": "http://encantado.topesteticabucal.com.br/sistema",
    "Soledade": "http://soledade.topesteticabucal.com.br/sistema",
    "Garibaldi": "http://garibaldi.topesteticabucal.com.br/sistema",
    "Veranópolis": "http://veranopolis.topesteticabucal.com.br/sistema",
    "SS do Caí": "http://ssdocai.topesteticabucal.com.br/sistema",
    "Flores": "http://flores.topesteticabucal.com.br/sistema",
}

# URLs de avaliações do Google
GOOGLE_REVIEWS = [
    "https://share.google/3f8yPEfrb24AQYYOp",   # Caxias
    "https://share.google/ffSPadgdvp8WUEXq0",   # Farroupilha
    "https://share.google/g1snAopsGqM5I8sOl",   # Bento
    "https://share.google/sEdZu4jHIPYL77RA6",   # Encantado
    "https://share.google/5CUABlRksD1cPYWiK",   # Soledade
    "https://share.google/rOGEnBONHO2kTYVk3",   # Garibaldi
    "https://share.google/UlnGSp8MES2AnB7Yz",   # Veranópolis
    "https://share.google/33XgmkKW7UnW8o8WB",   # SS do Caí
    "https://share.google/U2cO3MWeXsKQZUenB",   # Flores
]

AVALIACOES_INICIAIS = {
    "Caxias": 285,
    "Flores": 96,
    "Farroupilha": 173,
    "Bento": 76,
    "Encantado": 206,
    "Soledade": 413,
    "Garibaldi": 128,
    "Veranópolis": 128,
    "SS do Caí": 88,
}


# =========================
# UTILITÁRIOS
# =========================

def garantir_pasta_logs():
    os.makedirs("logs", exist_ok=True)


def salvar_screenshot(driver, nome_arquivo):
    try:
        garantir_pasta_logs()
        caminho = os.path.join("logs", nome_arquivo)
        driver.save_screenshot(caminho)
        print(f"Screenshot salvo em: {caminho}")
    except Exception as e:
        print(f"Não foi possível salvar screenshot: {e}")


def setup_driver():
    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver
def formatar_mes_para_texto(mes_referencia):
    """
    Converte 2026-02 em textos úteis para tentar selecionar na interface.
    """
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

    ano, mes = mes_referencia.split("-")
    nome_mes = mapa.get(mes, mes)
    return {
        "valor": mes_referencia,
        "mes": mes,
        "ano": ano,
        "texto": f"{nome_mes}/{ano}",
        "texto_com_espaco": f"{nome_mes} / {ano}",
        "nome_mes": nome_mes,
    }


# =========================
# LOGIN E FILTROS
# =========================

def fazer_login(driver, url, cidade):
    try:
        print(f"Abrindo URL: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 20)

        print(f"Título da página em {cidade}: {driver.title}")
        print(f"URL final em {cidade}: {driver.current_url}")

        # esperar campos de login realmente estarem utilizáveis
        username = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text'], input[name='username'], input[id='username']"))
        )

        password = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']"))
        )

        # limpar campos
        driver.execute_script("arguments[0].value = '';", username)
        driver.execute_script("arguments[0].value = '';", password)

        # preencher via JS (evita invalid element state)
        driver.execute_script("arguments[0].value = arguments[1];", username, LOGIN_USER)
        driver.execute_script("arguments[0].value = arguments[1];", password, LOGIN_PASS)

        time.sleep(1)

        # tentar clicar no botão
        try:
            botao = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            botao.click()
        except:
            password.submit()

        time.sleep(4)

        print(f"Após login em {cidade}: {driver.current_url}")

        salvar_screenshot(driver, f"pos_login_{cidade}.png")

        return True

    except Exception as e:
        print(f"Erro no login em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_login_{cidade}.png")
        return False

def selecionar_mes_referencia(driver, mes_referencia, cidade):
    """
    Seleciona o campo Mês/Ano com o valor desejado.
    Exemplo: Fevereiro / 2026
    """
    try:
        info_mes = formatar_mes_para_texto(mes_referencia)
        wait = WebDriverWait(driver, 15)

        print(f"Tentando selecionar mês {mes_referencia} em {cidade}...")

        texto_mes = info_mes["nome_mes"]
        texto_mes_ano = f"{info_mes['nome_mes']} / {info_mes['ano']}"
        texto_mes_ano_sem_espaco = f"{info_mes['nome_mes']}/{info_mes['ano']}"

        # Primeiro tenta localizar um select próximo ao texto "Mês/Ano"
        try:
            label_mes = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Mês/Ano') or contains(text(), 'Mes/Ano')]")
                )
            )
            salvar_screenshot(driver, f"campo_mes_encontrado_{cidade}.png")
        except Exception:
            label_mes = None

        # Tenta selects comuns
        selects = driver.find_elements(By.TAG_NAME, "select")
        for select_elem in selects:
            try:
                select = Select(select_elem)

                for opcao in [
                    texto_mes_ano,
                    texto_mes_ano_sem_espaco,
                    texto_mes,
                    mes_referencia
                ]:
                    try:
                        select.select_by_visible_text(opcao)
                        time.sleep(2)
                        print(f"Mês selecionado por texto: {opcao}")
                        salvar_screenshot(driver, f"mes_selecionado_{cidade}.png")
                        return True
                    except Exception:
                        pass

                try:
                    select.select_by_value(mes_referencia)
                    time.sleep(2)
                    print(f"Mês selecionado por value: {mes_referencia}")
                    salvar_screenshot(driver, f"mes_selecionado_{cidade}.png")
                    return True
                except Exception:
                    pass

            except Exception:
                continue

        # Tenta inputs
        for campo in driver.find_elements(By.CSS_SELECTOR, "input, select"):
            try:
                nome = (campo.get_attribute("name") or "").lower()
                campo_id = (campo.get_attribute("id") or "").lower()
                if "mes" in nome or "mes" in campo_id or "ano" in nome or "ano" in campo_id:
                    try:
                        campo.clear()
                    except Exception:
                        pass
                    campo.send_keys(mes_referencia)
                    time.sleep(2)
                    salvar_screenshot(driver, f"mes_selecionado_{cidade}.png")
                    return True
            except Exception:
                pass

        # Tenta clicar em opção visível
        for texto in [texto_mes_ano, texto_mes_ano_sem_espaco, texto_mes]:
            try:
                opcao = driver.find_element(By.XPATH, f"//*[contains(text(), '{texto}')]")
                driver.execute_script("arguments[0].click();", opcao)
                time.sleep(2)
                print(f"Mês selecionado por clique: {texto}")
                salvar_screenshot(driver, f"mes_selecionado_{cidade}.png")
                return True
            except Exception:
                pass

        print(f"Não foi possível selecionar o mês em {cidade}")
        salvar_screenshot(driver, f"mes_nao_encontrado_{cidade}.png")
        return False

    except Exception as e:
        print(f"Erro ao selecionar mês em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_selecao_mes_{cidade}.png")
        return False

def navegar_ate_metas(driver, cidade):
    """
    Navega: FINANÇAS > METAS
    """
    try:
        wait = WebDriverWait(driver, 15)

        print(f"Navegando até FINANÇAS > METAS em {cidade}...")

        # 1. Clicar em FINANÇAS
        financas = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'FINANÇAS') or contains(text(), 'Finanças')]"))
        )
        driver.execute_script("arguments[0].click();", financas)
        time.sleep(2)

        # 2. Clicar em METAS
        metas = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'METAS') or contains(text(), 'Metas')]"))
        )
        driver.execute_script("arguments[0].click();", metas)
        time.sleep(3)

        print(f"Chegou na tela de metas em {cidade}: {driver.current_url}")
        salvar_screenshot(driver, f"tela_metas_{cidade}.png")
        return True

    except Exception as e:
        print(f"Erro ao navegar até FINANÇAS > METAS em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_navegacao_metas_{cidade}.png")
        return False


def extrair_texto_seguro(driver, seletores):
    """
    Tenta vários seletores até encontrar um valor.
    """
    for by, valor in seletores:
        try:
            texto = driver.find_element(by, valor).text.strip()
            if texto:
                return texto
        except Exception:
            continue
    return ""


def extrair_metas_financeiras(driver, cidade):
    """Extrai dados financeiros já na tela de metas."""
    try:
        time.sleep(2)

        ortodontia = extrair_texto_seguro(driver, [
            (By.ID, "ortodontia_valor"),
            (By.ID, "ortodontia"),
            (By.NAME, "ortodontia"),
            (By.XPATH, "//*[contains(text(), 'Ortodontia')]/following::*[1]"),
            (By.XPATH, "//*[contains(text(), 'Ortodontia')]/ancestor::*[1]//*[contains(text(), 'R$')]"),
        ])

        clinico = extrair_texto_seguro(driver, [
            (By.ID, "clinico_valor"),
            (By.ID, "clinico_geral"),
            (By.NAME, "clinico_geral"),
            (By.XPATH, "//*[contains(text(), 'Clínico Geral')]/following::*[1]"),
            (By.XPATH, "//*[contains(text(), 'Clinico Geral')]/following::*[1]"),
            (By.XPATH, "//*[contains(text(), 'Clínico Geral')]/ancestor::*[1]//*[contains(text(), 'R$')]"),
        ])

        salvar_screenshot(driver, f"financeiro_extraido_{cidade}.png")

        return {
            "ortodontia": ortodontia or "R$ 0",
            "clinico_geral": clinico or "R$ 0",
        }

    except Exception as e:
        print(f"Erro ao extrair metas financeiras de {cidade}: {e}")
        salvar_screenshot(driver, f"erro_financeiro_{cidade}.png")
        return {
            "ortodontia": "R$ 0",
            "clinico_geral": "R$ 0",
        }
def extrair_metas_servicos(driver, cidade):
    """Extrai dados de metas de serviços."""
    try:
        abriu = abrir_menu_por_texto(driver, [
            "Metas de Serviços",
            "Meta de Serviços",
            "Serviços",
            "Metas Serviços",
        ])

        if not abriu:
            raise Exception("Menu de metas de serviços não encontrado")

        profilaxia = extrair_texto_seguro(driver, [
            (By.ID, "profilaxia"),
            (By.NAME, "profilaxia"),
            (By.XPATH, "//*[contains(text(), 'Profilaxia')]/following::*[1]"),
        ])

        restauracao = extrair_texto_seguro(driver, [
            (By.ID, "restauracao"),
            (By.NAME, "restauracao"),
            (By.XPATH, "//*[contains(text(), 'Restauração')]/following::*[1]"),
            (By.XPATH, "//*[contains(text(), 'Restauracao')]/following::*[1]"),
        ])

        return {
            "profilaxia": profilaxia or "0",
            "restauracao": restauracao or "0",
        }

    except Exception as e:
        print(f"Erro ao extrair metas de serviços de {cidade}: {e}")
        salvar_screenshot(driver, f"erro_servicos_{cidade}.png")
        return {
            "profilaxia": "0",
            "restauracao": "0",
        }


def obter_avaliacoes_google(url):
    """
    Mantido simples por enquanto.
    Hoje retorna 0 quando não conseguir obter.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return 0
        return 0
    except Exception as e:
        print(f"Erro ao obter avaliações do Google: {e}")
        return 0


# =========================
# COLETA GERAL
# =========================

def coletar_dados_todas_cidades():
    """Coleta dados de todas as cidades."""
    dados = {}
    driver = setup_driver()

    try:
        for idx, (cidade, url) in enumerate(CIDADES.items()):
            print("-" * 60)
            print(f"Coletando dados de {cidade}...")

            try:
                if not fazer_login(driver, url, cidade):
    print(f"Falha ao coletar dados de {cidade}")
    continue

if not navegar_ate_metas(driver, cidade):
    print(f"Falha ao navegar até metas em {cidade}")
    continue

selecionar_mes_referencia(driver, MES_REFERENCIA, cidade)

metas_financeiras = extrair_metas_financeiras(driver, cidade)
metas_servicos = extrair_metas_servicos(driver, cidade)

                avaliacoes_atual = obter_avaliacoes_google(GOOGLE_REVIEWS[idx])
                avaliacoes_inicial = AVALIACOES_INICIAIS.get(cidade, 0)
                avaliacoes_novas = avaliacoes_atual - avaliacoes_inicial

                dados[cidade] = {
                    "mes_referencia": MES_REFERENCIA,
                    "metas_financeiras": metas_financeiras,
                    "metas_servicos": metas_servicos,
                    "avaliacoes": {
                        "inicial": avaliacoes_inicial,
                        "atual": avaliacoes_atual,
                        "novas": avaliacoes_novas,
                    },
                    "timestamp": datetime.now().isoformat(),
                }

                print(f"Coleta concluída em {cidade}")

            except WebDriverException as e:
                print(f"Erro de navegador em {cidade}: {e}")
                salvar_screenshot(driver, f"erro_driver_{cidade}.png")
                continue
            except Exception as e:
                print(f"Erro inesperado em {cidade}: {e}")
                salvar_screenshot(driver, f"erro_geral_{cidade}.png")
                continue

    finally:
        driver.quit()

    return dados


# =========================
# SAÍDAS
# =========================

def salvar_json(dados):
    output_path = "data/metas_atual.json"
    os.makedirs("data", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"JSON salvo em: {output_path}")


def salvar_csv(dados):
    output_path = "data/historico_metas.csv"
    os.makedirs("data", exist_ok=True)

    rows = []
    for cidade, info in dados.items():
        row = {
            "cidade": cidade,
            "mes_referencia": info.get("mes_referencia", MES_REFERENCIA),
            "timestamp": info["timestamp"],
            "ortodontia": info["metas_financeiras"].get("ortodontia", ""),
            "clinico_geral": info["metas_financeiras"].get("clinico_geral", ""),
            "profilaxia": info["metas_servicos"].get("profilaxia", ""),
            "restauracao": info["metas_servicos"].get("restauracao", ""),
            "avaliacoes_novas": info["avaliacoes"]["novas"],
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if os.path.exists(output_path):
        df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df.to_csv(output_path, index=False)

    print(f"CSV atualizado em: {output_path}")


def gerar_excel(dados):
    output_path = "data/metas_top_estetica.xlsx"

    df_financeiro = []
    df_servicos = []
    df_avaliacoes = []

    for cidade, info in dados.items():
        df_financeiro.append({
            "Cidade": cidade,
            "Mês Referência": info.get("mes_referencia", MES_REFERENCIA),
            "Ortodontia": info["metas_financeiras"].get("ortodontia", ""),
            "Clínico Geral": info["metas_financeiras"].get("clinico_geral", ""),
        })

        df_servicos.append({
            "Cidade": cidade,
            "Mês Referência": info.get("mes_referencia", MES_REFERENCIA),
            "Profilaxia": info["metas_servicos"].get("profilaxia", ""),
            "Restauração": info["metas_servicos"].get("restauracao", ""),
        })

        df_avaliacoes.append({
            "Cidade": cidade,
            "Mês Referência": info.get("mes_referencia", MES_REFERENCIA),
            "Avaliações Iniciais": info["avaliacoes"]["inicial"],
            "Avaliações Atuais": info["avaliacoes"]["atual"],
            "Novas Avaliações": info["avaliacoes"]["novas"],
        })

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(df_financeiro).to_excel(writer, sheet_name="Metas Financeiras", index=False)
        pd.DataFrame(df_servicos).to_excel(writer, sheet_name="Metas Serviços", index=False)
        pd.DataFrame(df_avaliacoes).to_excel(writer, sheet_name="Avaliações Google", index=False)

    print(f"Excel gerado em: {output_path}")


# =========================
# MAIN
# =========================

def main():
    print("=" * 60)
    print("Iniciando coleta de dados - Top Estética Bucal")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Mês de referência: {MES_REFERENCIA}")
    print("=" * 60)

    if not LOGIN_USER or not LOGIN_PASS:
        print("✗ LOGIN_USER ou LOGIN_PASS não configurados.")
        raise SystemExit(1)

    dados = coletar_dados_todas_cidades()

    if dados:
        salvar_json(dados)
        salvar_csv(dados)
        gerar_excel(dados)

        print("\n✓ Coleta concluída com sucesso!")
        print(f"Total de cidades processadas: {len(dados)}")
    else:
        print("\n✗ Nenhum dado foi coletado!")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
