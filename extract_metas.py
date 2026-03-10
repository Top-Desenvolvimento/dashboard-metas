#!/usr/bin/env python3
"""
Coleta de metas da Top Estética Bucal

Fluxo:
1. Faz login em cada unidade
2. Abre a tela de metas diretamente
3. Lê as tabelas reais da página
4. Salva JSON / CSV / Excel

Indicadores coletados:
- ortodontia
- clinico_geral
- avaliacoes_google
- meta_avaliacao
- meta_profilaxia
- meta_restauracao
"""

import os
import json
import time
from datetime import datetime

import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


LOGIN_USER = os.environ.get("LOGIN_USER", "")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "")


def calcular_mes_referencia():
    hoje = datetime.now()
    if hoje.day <= 5:
        if hoje.month == 1:
            ano = hoje.year - 1
            mes = 12
        else:
            ano = hoje.year
            mes = hoje.month - 1
    else:
        ano = hoje.year
        mes = hoje.month
    return f"{ano}-{mes:02d}"


MES_REFERENCIA_ENV = os.environ.get("MES_REFERENCIA", "AUTO")
MES_REFERENCIA = calcular_mes_referencia() if MES_REFERENCIA_ENV == "AUTO" else MES_REFERENCIA_ENV


CIDADES = {
    "Caxias": "http://caxias.topesteticabucal.com.br/sistema",
    "Farroupilha": "http://farroupilha.topesteticabucal.com.br/sistema",
    "Bento": "http://bento.topesteticabucal.com.br/sistema",
    "Encantado": "https://encantado.topesteticabucal.com.br/sistema",
    "Soledade": "http://soledade.topesteticabucal.com.br/sistema",
    "Garibaldi": "http://garibaldi.topesteticabucal.com.br/sistema",
    "Veranópolis": "http://veranopolis.topesteticabucal.com.br/sistema",
    "SS do Caí": "https://ssdocai.topesteticabucal.com.br/sistema",
    "Flores": "http://flores.topesteticabucal.com.br/sistema",
}

GOOGLE_REVIEWS = {
    "Caxias": "https://share.google/3f8yPEfrb24AQYYOp",
    "Farroupilha": "https://share.google/ffSPadgdvp8WUEXq0",
    "Bento": "https://share.google/g1snAopsGqM5I8sOl",
    "Encantado": "https://share.google/sEdZu4jHIPYL77RA6",
    "Soledade": "https://share.google/5CUABlRksD1cPYWiK",
    "Garibaldi": "https://share.google/rOGEnBONHO2kTYVk3",
    "Veranópolis": "https://share.google/UlnGSp8MES2AnB7Yz",
    "SS do Caí": "https://share.google/33XgmkKW7UnW8o8WB",
    "Flores": "https://share.google/U2cO3MWeXsKQZUenB",
}


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


def normalizar_texto(texto):
    return " ".join((texto or "").replace("\xa0", " ").split()).strip()


def texto_pagina(driver):
    body = driver.find_element(By.TAG_NAME, "body").text
    return normalizar_texto(body)


def extrair_bloco_por_regex(texto, titulo):
    """
    Extrai blocos no formato:
    TÍTULO
    Até o momento
    Falta
    Progresso
    Meta
    VALOR_META
    VALOR_ATE
    VALOR_FALTA
    VALOR_PROGRESSO
    """

    pattern = re.compile(
        rf"{re.escape(titulo)}\s+Até o momento\s+Falta\s+Progresso\s+Meta\s+(.+?)\s+(.+?)\s+(.+?)\s+([0-9.,%-]+)",
        re.IGNORECASE | re.DOTALL
    )

    match = pattern.search(texto)

    if not match:
        return {
            "meta": "",
            "ate_o_momento": "",
            "falta": "",
            "progresso": "",
        }

    return {
        "meta": normalizar_texto(match.group(1)),
        "ate_o_momento": normalizar_texto(match.group(2)),
        "falta": normalizar_texto(match.group(3)),
        "progresso": normalizar_texto(match.group(4)),
    }


def extrair_todas_metas(driver, cidade):
    """
    Extrai as 6 metas reais a partir do texto visível da página.
    """
    texto = texto_pagina(driver)

    print(f"Texto da página em {cidade}:")
    print(texto[:3000])

    dados = {
        "ortodontia": extrair_bloco_por_regex(texto, "Ortodontia"),
        "clinico_geral": extrair_bloco_por_regex(texto, "Clínico Geral"),
        "avaliacoes_google": extrair_bloco_por_regex(texto, "Avaliações Google"),
        "meta_avaliacao": extrair_bloco_por_regex(texto, "Meta de Avaliação"),
        "meta_profilaxia": extrair_bloco_por_regex(texto, "Meta de Profilaxia"),
        "meta_restauracao": extrair_bloco_por_regex(texto, "Meta de Restauração"),
    }

    salvar_screenshot(driver, f"metas_extraidas_{cidade}.png")
    print(f"Metas extraídas em {cidade}: {json.dumps(dados, ensure_ascii=False)}")

    return dados


def normalizar_chave(texto):
    t = normalizar_texto(texto).lower()
    t = t.replace("clínico", "clinico")
    t = t.replace("avaliações", "avaliacoes")
    t = t.replace("restauração", "restauracao")
    return t


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

        driver.execute_script("arguments[0].value = '';", username)
        driver.execute_script("arguments[0].value = '';", password)
        driver.execute_script("arguments[0].value = arguments[1];", username, LOGIN_USER)
        driver.execute_script("arguments[0].value = arguments[1];", password, LOGIN_PASS)

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


def abrir_tela_metas(driver, cidade):
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
        salvar_screenshot(driver, f"erro_tela_metas_{cidade}.png")
        return False


def coletar_bloco_por_titulo(driver, titulo):
    """
    Localiza um bloco pelo título e lê a linha logo abaixo com:
    Meta | Até o momento | Falta | Progresso
    """
    try:
        xpath_titulo = (
            f"//*[self::td or self::th or self::div or self::span]"
            f"[contains(normalize-space(.), '{titulo}')]"
        )
        titulo_el = driver.find_element(By.XPATH, xpath_titulo)

        # Sobe até um container razoável
        container = titulo_el.find_element(By.XPATH, "./ancestor::table[1] | ./ancestor::tbody[1] | ./ancestor::tr[1]/parent::*")
        linhas = container.find_elements(By.XPATH, ".//tr")

        # Procura a linha de dados que vem depois do título
        encontrou_titulo = False
        for linha in linhas:
            texto_linha = normalizar_texto(linha.text)
            if not texto_linha:
                continue

            if titulo.lower() in texto_linha.lower():
                encontrou_titulo = True
                continue

            if encontrou_titulo:
                colunas = linha.find_elements(By.XPATH, ".//td")
                if len(colunas) >= 4:
                    return {
                        "meta": normalizar_texto(colunas[0].text),
                        "ate_o_momento": normalizar_texto(colunas[1].text),
                        "falta": normalizar_texto(colunas[2].text),
                        "progresso": normalizar_texto(colunas[3].text),
                    }

        return {
            "meta": "",
            "ate_o_momento": "",
            "falta": "",
            "progresso": "",
        }

    except Exception:
        return {
            "meta": "",
            "ate_o_momento": "",
            "falta": "",
            "progresso": "",
        }


def extrair_todas_metas(driver, cidade):
    """
    Extrai as 6 metas reais da tela.
    """
    dados = {
        "ortodontia": coletar_bloco_por_titulo(driver, "Ortodontia"),
        "clinico_geral": coletar_bloco_por_titulo(driver, "Clínico Geral"),
        "avaliacoes_google": coletar_bloco_por_titulo(driver, "Avaliações Google"),
        "meta_avaliacao": coletar_bloco_por_titulo(driver, "Meta de Avaliação"),
        "meta_profilaxia": coletar_bloco_por_titulo(driver, "Meta de Profilaxia"),
        "meta_restauracao": coletar_bloco_por_titulo(driver, "Meta de Restauração"),
    }

    salvar_screenshot(driver, f"metas_extraidas_{cidade}.png")
    return dados


def obter_avaliacoes_google(url):
    """
    Mantido simples por enquanto.
    Você comentou que a meta do Google será administrada à parte.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return 0
        return 0
    except Exception as e:
        print(f"Erro ao obter avaliações do Google: {e}")
        return 0


def coletar_dados_todas_cidades():
    dados = {}
    driver = setup_driver()

    try:
        for cidade, url in CIDADES.items():
            print("-" * 60)
            print(f"Coletando dados de {cidade}...")

            try:
                if not fazer_login(driver, url, cidade):
                    print(f"Falha ao coletar dados de {cidade}")
                    continue

                if not abrir_tela_metas(driver, cidade):
                    print(f"Falha ao abrir metas em {cidade}")
                    continue

                metas = extrair_todas_metas(driver, cidade)

                dados[cidade] = {
                    "mes_referencia": MES_REFERENCIA,
                    "timestamp": datetime.now().isoformat(),
                    "google_reviews_url": GOOGLE_REVIEWS.get(cidade, ""),
                    "indicadores": metas,
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
        for indicador, valores in info.get("indicadores", {}).items():
            rows.append({
                "cidade": cidade,
                "mes_referencia": info.get("mes_referencia", ""),
                "timestamp": info.get("timestamp", ""),
                "indicador": indicador,
                "meta": valores.get("meta", ""),
                "ate_o_momento": valores.get("ate_o_momento", ""),
                "falta": valores.get("falta", ""),
                "progresso": valores.get("progresso", ""),
            })

    df = pd.DataFrame(rows)
    if os.path.exists(output_path):
        df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df.to_csv(output_path, index=False)

    print(f"CSV atualizado em: {output_path}")


def gerar_excel(dados):
    output_path = "data/metas_top_estetica.xlsx"
    os.makedirs("data", exist_ok=True)

    rows = []
    for cidade, info in dados.items():
        base = {
            "Cidade": cidade,
            "Mês Referência": info.get("mes_referencia", ""),
            "Timestamp": info.get("timestamp", ""),
        }

        for indicador, valores in info.get("indicadores", {}).items():
            rows.append({
                **base,
                "Indicador": indicador,
                "Meta": valores.get("meta", ""),
                "Até o Momento": valores.get("ate_o_momento", ""),
                "Falta": valores.get("falta", ""),
                "Progresso": valores.get("progresso", ""),
            })

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="Metas", index=False)

    print(f"Excel gerado em: {output_path}")


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
