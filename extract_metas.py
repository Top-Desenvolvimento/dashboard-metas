#!/usr/bin/env python3
"""
Coleta de metas da Top Estética Bucal

Saída exata para a dashboard:
{
  "Cidade": {
    "mes_referencia": "2026-03",
    "timestamp": "...",
    "indicadores": {
      "ortodontia": {"meta":"", "ate_o_momento":"", "falta":"", "progresso":""},
      "clinico_geral": {...},
      "avaliacoes_google": {...},
      "meta_avaliacao": {...},
      "meta_profilaxia": {...},
      "meta_restauracao": {...}
    }
  }
}
"""

import os
import re
import json
import time
from datetime import datetime

import pandas as pd
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


INDICADORES_ORDEM = [
    ("ortodontia", "Ortodontia"),
    ("clinico_geral", "Clínico Geral"),
    ("avaliacoes_google", "Avaliações Google"),
    ("meta_avaliacao", "Meta de Avaliação"),
    ("meta_profilaxia", "Meta de Profilaxia"),
    ("meta_restauracao", "Meta de Restauração"),
]


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


def normalizar_linhas(texto):
    linhas = [normalizar_texto(l) for l in (texto or "").splitlines()]
    return [l for l in linhas if l]


def fazer_login(driver, url, cidade):
    try:
        print(f"Abrindo URL: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 20)

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
        salvar_screenshot(driver, f"pos_login_{cidade}.png")
        print(f"Após login em {cidade}: {driver.current_url}")
        return True

    except Exception as e:
        print(f"Erro no login em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_login_{cidade}.png")
        return False


def abrir_tela_metas(driver, cidade):
    try:
        wait = WebDriverWait(driver, 20)

        print(f"Navegando até FINANÇAS > Metas em {cidade}...")

        # clica em FINANÇAS
        btn_financas = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space(text())='FINANÇAS' or normalize-space(text())='Finanças']")
            )
        )
        driver.execute_script("arguments[0].click();", btn_financas)
        time.sleep(2)

        salvar_screenshot(driver, f"menu_financas_{cidade}.png")

        # clica em Metas
        btn_metas = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space(text())='Metas']")
            )
        )
        driver.execute_script("arguments[0].click();", btn_metas)
        time.sleep(3)

        salvar_screenshot(driver, f"tela_metas_{cidade}.png")
        print(f"Tela de metas aberta em {cidade}: {driver.current_url}")

        return True

    except Exception as e:
        print(f"Erro ao abrir tela de metas em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_tela_metas_{cidade}.png")
        return False


def obter_texto_pagina(driver):
    body = driver.find_element(By.TAG_NAME, "body").text
    return body


def extrair_bloco_linhas(linhas, titulo):
    """
    Busca blocos no formato exato visível da página, por exemplo:

    Meta de Avaliação
    Até o momento
    Falta
    Progresso
    Meta
    205
    33
    -172
    16,098%
    """
    titulo_norm = titulo.lower()

    for i, linha in enumerate(linhas):
        if linha.lower() != titulo_norm:
            continue

        bloco = linhas[i:i + 14]

        # Caso padrão
        if len(bloco) >= 9:
            if (
                "até o momento" in bloco[1].lower()
                and "falta" in bloco[2].lower()
                and "progresso" in bloco[3].lower()
                and bloco[4].lower() == "meta"
            ):
                return {
                    "meta": bloco[5] if len(bloco) > 5 else "",
                    "ate_o_momento": bloco[6] if len(bloco) > 6 else "",
                    "falta": bloco[7] if len(bloco) > 7 else "",
                    "progresso": bloco[8] if len(bloco) > 8 else "",
                }

        # Fallback
        try:
            idx_meta = next(idx for idx, item in enumerate(bloco) if item.lower() == "meta")
            if idx_meta + 4 < len(bloco):
                return {
                    "meta": bloco[idx_meta + 1],
                    "ate_o_momento": bloco[idx_meta + 2],
                    "falta": bloco[idx_meta + 3],
                    "progresso": bloco[idx_meta + 4],
                }
        except StopIteration:
            pass

    return {
        "meta": "",
        "ate_o_momento": "",
        "falta": "",
        "progresso": "",
    }


def extrair_todas_metas(driver, cidade):
    texto = obter_texto_pagina(driver)
    linhas = normalizar_linhas(texto)

    print(f"Primeiras linhas da página em {cidade}:")
    for linha in linhas[:120]:
        print(linha)

    dados = {}
    for chave, titulo in INDICADORES_ORDEM:
        dados[chave] = extrair_bloco_linhas(linhas, titulo)

    print(f"Metas extraídas em {cidade}: {json.dumps(dados, ensure_ascii=False)}")
    salvar_screenshot(driver, f"metas_extraidas_{cidade}.png")
    return dados


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
    os.makedirs("data", exist_ok=True)
    with open("data/metas_atual.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print("JSON salvo em: data/metas_atual.json")


def salvar_csv(dados):
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
    caminho = "data/historico_metas.csv"
    if os.path.exists(caminho):
        df.to_csv(caminho, mode="a", header=False, index=False)
    else:
        df.to_csv(caminho, index=False)

    print("CSV atualizado em: data/historico_metas.csv")


def gerar_excel(dados):
    os.makedirs("data", exist_ok=True)
    rows = []

    for cidade, info in dados.items():
        for indicador, valores in info.get("indicadores", {}).items():
            rows.append({
                "Cidade": cidade,
                "Mês Referência": info.get("mes_referencia", ""),
                "Timestamp": info.get("timestamp", ""),
                "Indicador": indicador,
                "Meta": valores.get("meta", ""),
                "Até o Momento": valores.get("ate_o_momento", ""),
                "Falta": valores.get("falta", ""),
                "Progresso": valores.get("progresso", ""),
            })

    with pd.ExcelWriter("data/metas_top_estetica.xlsx", engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="Metas", index=False)

    print("Excel gerado em: data/metas_top_estetica.xlsx")


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
