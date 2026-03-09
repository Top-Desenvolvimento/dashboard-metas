#!/usr/bin/env python3
"""
Script de extração de metas da Top Estética Bucal
Fluxo:
1. Faz login em cada unidade
2. Navega em FINANÇAS > METAS
3. Seleciona o mês de referência
4. Extrai metas financeiras e de serviços
5. Salva JSON, CSV e Excel
"""

import os
import json
import time
from datetime import datetime

import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
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
MES_REFERENCIA = os.environ.get("MES_REFERENCIA", datetime.now().strftime("%Y-%m"))

CIDADES = {
    "Caxias": "http://caxias.topesteticabucal.com.br/sistema",
    "Farroupilha": "http://farroupilha.topesteticabucal.com.br/sistema",
    "Bento": "http://bento.topesteticabucal.com.br/sistema",
    "Encantado": "https://encantado.topesteticabucal.com.br/sistema",
    "Soledade": "http://soledade.topesteticabucal.com.br/sistema",
    "Garibaldi": "http://garibaldi.topesteticabucal.com.br/sistema",
    "Veranópolis": "http://veranopolis.topesteticabucal.com.br/sistema",
    "SS do Caí": "https://ssdocai.topesteticabucal.com.br/sistema",
    "Flores": "https://flores.topesteticabucal.com.br/sistema",
}

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
    "Flores": 94,
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
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(40)
    return driver


def formatar_mes_para_texto(mes_referencia):
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
        "ano": ano,
        "mes": mes,
        "nome_mes": nome_mes,
        "texto": f"{nome_mes}/{ano}",
        "texto_com_espaco": f"{nome_mes} / {ano}",
        "valor": mes_referencia,
    }


def extrair_texto_seguro(driver, seletores):
    for by, valor in seletores:
        try:
            el = driver.find_element(by, valor)
            texto = el.text.strip()
            if texto:
                return texto
            value = (el.get_attribute("value") or "").strip()
            if value:
                return value
        except Exception:
            continue
    return ""


# =========================
# LOGIN E NAVEGAÇÃO
# =========================

def fazer_login(driver, url, cidade):
    try:
        print(f"Abrindo URL: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 20)

        print(f"Título da página em {cidade}: {driver.title}")
        print(f"URL final em {cidade}: {driver.current_url}")

        username = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='text'], input[name='username'], input[id='username']")
            )
        )

        password = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='password']")
            )
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", username)
        time.sleep(0.5)

        driver.execute_script("arguments[0].value = '';", username)
        driver.execute_script("arguments[0].value = '';", password)

        driver.execute_script("arguments[0].value = arguments[1];", username, LOGIN_USER)
        driver.execute_script("arguments[0].value = arguments[1];", password, LOGIN_PASS)

        time.sleep(1)

        clicou = False
        for seletor in [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.XPATH, "//button[contains(., 'Entrar')]"),
            (By.XPATH, "//button[contains(., 'Login')]"),
            (By.XPATH, "//input[@value='Entrar']"),
        ]:
            try:
                botao = driver.find_element(*seletor)
                driver.execute_script("arguments[0].click();", botao)
                clicou = True
                break
            except Exception:
                continue

        if not clicou:
            password.submit()

        time.sleep(4)

        print(f"Após login em {cidade}: {driver.current_url}")
        salvar_screenshot(driver, f"pos_login_{cidade}.png")
        return True

    except Exception as e:
        print(f"Erro no login em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_login_{cidade}.png")
        return False


def navegar_ate_metas(driver, cidade):
    """
    Abre diretamente a página de metas financeiras
    """

    try:
        print(f"Abrindo tela de metas diretamente em {cidade}...")

        base = driver.current_url.split("index2.php")[0]

        url_metas = base + "index2.php?conteudo=financeiro_metas"

        driver.get(url_metas)

        time.sleep(4)

        print(f"URL metas em {cidade}: {driver.current_url}")

        salvar_screenshot(driver, f"tela_metas_{cidade}.png")

        return True

    except Exception as e:
        print(f"Erro ao abrir tela de metas em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_navegacao_metas_{cidade}.png")
        return False
def selecionar_mes_referencia(driver, mes_referencia, cidade):
    """
    Seleciona o Mês/Ano na tela de metas.
    """
    try:
        info_mes = formatar_mes_para_texto(mes_referencia)
        wait = WebDriverWait(driver, 15)

        print(f"Tentando selecionar mês {mes_referencia} em {cidade}...")

        texto_mes = info_mes["nome_mes"]
        texto_mes_ano = f"{info_mes['nome_mes']} / {info_mes['ano']}"
        texto_mes_ano_sem_espaco = f"{info_mes['nome_mes']}/{info_mes['ano']}"

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Mês/Ano') or contains(text(), 'Mes/Ano')]")
                )
            )
        except Exception:
            pass

        selects = driver.find_elements(By.TAG_NAME, "select")
        for select_elem in selects:
            try:
                select = Select(select_elem)

                for opcao in [
                    texto_mes_ano,
                    texto_mes_ano_sem_espaco,
                    texto_mes,
                    mes_referencia,
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
                    print(f"Mês preenchido manualmente: {mes_referencia}")
                    salvar_screenshot(driver, f"mes_selecionado_{cidade}.png")
                    return True
            except Exception:
                pass

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


# =========================
# EXTRAÇÃO
# =========================

def extrair_metas_financeiras(driver, cidade):
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
    try:
        time.sleep(2)

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

        salvar_screenshot(driver, f"servicos_extraidos_{cidade}.png")

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
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return 0
        return 0
    except Exception as e:
        print(f"Erro ao obter avaliações do Google: {e}")
        return 0


# =========================
# COLETA
# =========================

def coletar_dados_todas_cidades():
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
