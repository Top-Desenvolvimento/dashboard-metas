#!/usr/bin/env python3
"""
Generate Dashboard - Top Estética Bucal

Fluxo correto:
Login -> FINANÇAS -> Metas -> extrair tabelas (financeiro + serviços)

Saída:
- data/metas_atual.json
"""

import os
import json
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ====== Configurações ======
LOGIN_USER = os.environ.get("LOGIN_USER", "MANUS")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "MANUS2026")

# URLs das cidades
CIDADES = {
    "Caxias": "http://caxias.topesteticabucal.com.br/sistema",
    "Farroupilha": "http://farroupilha.topesteticabucal.com.br/sistema",
    "Bento": "http://bento.topesteticabucal.com.br/sistema",
    "Encantado": "https://encantado.topesteticabucal.com.br/sistema",
    "Soledade": "http://soledade.topesteticabucal.com.br/sistema",
    "Garibaldi": "http://garibaldi.topesteticabucal.com.br/sistema",
    "Veranópolis": "http://veranopolis.topesteticabucal.com.br/sistema",
    "SS do Caí": "http://ssdocai.topesteticabucal.com.br/sistema",   # (usando http)
    "Flores": "http://flores.topesteticabucal.com.br/sistema",       # (usando http)
}

OUTPUT_JSON = os.path.join("data", "metas_atual.json")


# ====== Selenium helpers ======
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)


def click_wait(wait: WebDriverWait, by: By, selector: str):
    el = wait.until(EC.element_to_be_clickable((by, selector)))
    el.click()
    return el


def fazer_login(driver, base_url) -> bool:
    try:
        wait = WebDriverWait(driver, 25)
        driver.get(base_url)

        usuario = wait.until(EC.presence_of_element_located((By.ID, "usuario")))
        senha = wait.until(EC.presence_of_element_located((By.ID, "senha")))

        usuario.clear()
        usuario.send_keys(LOGIN_USER)

        senha.clear()
        senha.send_keys(LOGIN_PASS)

        click_wait(wait, By.CSS_SELECTOR, "input[type='submit']")
        time.sleep(1)
        return True

    except Exception as e:
        print(f"Erro no login ({base_url}): {e}")
        return False


def ir_para_metas(driver) -> bool:
    """
    Clique em FINANÇAS -> Metas (robusto: não depende de ser <a> com link text).
    """
    wait = WebDriverWait(driver, 30)

    try:
        # Espera o body existir
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 1) Clicar em FINANÇAS (aceita FINANÇAS / Finanças / FINANCAS)
        financas_xpath = (
            "//*[self::a or self::button or self::div or self::span]"
            "[contains(translate(normalize-space(.),"
            " 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇFINANÇAS',"
            " 'AAAAAEEEEIIIIOOOOOUUUUCFINANCAS'),"
            " 'FINANCAS')]"
        )
        el_fin = wait.until(EC.element_to_be_clickable((By.XPATH, financas_xpath)))
        el_fin.click()
        time.sleep(1)

        # 2) Clicar em METAS
        metas_xpath = (
            "//*[self::a or self::button or self::div or self::span]"
            "[contains(translate(normalize-space(.),"
            " 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇMETAS',"
            " 'AAAAAEEEEIIIIOOOOOUUUUCMETAS'),"
            " 'METAS')]"
        )
        el_metas = wait.until(EC.element_to_be_clickable((By.XPATH, metas_xpath)))
        el_metas.click()

        # Aguarda a página de metas carregar (presença do select do mês/ano ajuda)
        wait.until(EC.presence_of_element_located((By.ID, "mes_ano")))
        time.sleep(2)
        return True

    except Exception as e:
        print(f"Erro ao navegar FINANÇAS > Metas: {e}")
        return False
        
if not ir_para_metas(driver):
    print("Tentando plano B por URL direta de metas...")
    ir_para_metas_por_url(driver, url)  # precisa ter essa função

def ir_para_metas_por_url(driver, base_url):
    wait = WebDriverWait(driver, 30)
    metas_url = base_url.rstrip("/") + "/index2.php?conteudo=lista_metas"
    driver.get(metas_url)
    wait.until(EC.presence_of_element_located((By.ID, "mes_ano")))
    time.sleep(2)

def extrair_tabelas(driver):
    """
    Extrai todas as tabelas da página (lista de matrizes de texto).
    """
    tables = driver.find_elements(By.TAG_NAME, "table")
    all_tables = []

    for table in tables:
        rows = table.find_elements(By.TAG_NAME, "tr")
        t = []
        for r in rows:
            cells = r.find_elements(By.CSS_SELECTOR, "th,td")
            t.append([c.text.strip() for c in cells])
        # só adiciona se tiver conteúdo
        if any(any(cell for cell in row) for row in t):
            all_tables.append(t)

    return all_tables


def detectar_mes_ano(driver) -> str:
    """
    Tenta capturar o mês/ano selecionado (como no print: Fevereiro / 2026).
    """
    try:
        sel = driver.find_element(By.ID, "mes_ano")
        opts = sel.find_elements(By.TAG_NAME, "option")
        for o in opts:
            if o.is_selected():
                return o.text.strip()
    except Exception:
        pass
    return "N/A"


# ====== Main ======
def main():
    os.makedirs("data", exist_ok=True)

    driver = setup_driver()

    resultado = {
        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cidades": {},
    }

    try:
        for cidade, url in CIDADES.items():
            print(f"Coletando dados de {cidade}...")

            if not fazer_login(driver, url):
                print(f"Falha ao coletar dados de {cidade} (login).")
                continue

            if not ir_para_metas(driver):
                print(f"Falha ao coletar dados de {cidade} (menu finanças/metas).")
                continue

            mes_ano = detectar_mes_ano(driver)
            tabelas = extrair_tabelas(driver)

            if not tabelas:
                print(f"Falha ao coletar dados de {cidade}: nenhuma tabela encontrada.")
                continue

            resultado["cidades"][cidade] = {
                "url": url,
                "mes_ano": mes_ano,
                "tabelas": tabelas,
            }

        if len(resultado["cidades"]) == 0:
            print("X Nenhum dado foi coletado!")
            raise SystemExit(1)

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON gerado em: {OUTPUT_JSON}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
