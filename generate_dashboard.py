#!/usr/bin/env python3
"""
Generate Dashboard - Top Estética Bucal

Fluxo:
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

def debug_state(driver, label):
    try:
        print(f"[DEBUG] {label} | url={driver.current_url} | title={driver.title}")
    except Exception as e:
        print(f"[DEBUG] {label} | (falha ao ler url/title): {e}")

def save_debug(driver, cidade, etapa):
    try:
        os.makedirs("debug", exist_ok=True)
        path = f"debug/{cidade}_{etapa}.png".replace(" ", "_").replace("/", "_")
        driver.save_screenshot(path)
        print(f"[DEBUG] screenshot: {path}")
    except Exception as e:
        print(f"[DEBUG] falha ao salvar screenshot: {e}")

# ====== Credenciais (vem do GitHub Secrets via workflow) ======
LOGIN_USER = os.environ.get("LOGIN_USER", "MANUS")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "MANUS2026")

# ====== Cidades ======
CIDADES = {
    "Caxias": "http://caxias.topesteticabucal.com.br/sistema",
    "Farroupilha": "http://farroupilha.topesteticabucal.com.br/sistema",
    "Bento": "http://bento.topesteticabucal.com.br/sistema",
    "Encantado": "https://encantado.topesteticabucal.com.br/sistema",
    "Soledade": "http://soledade.topesteticabucal.com.br/sistema",
    "Garibaldi": "http://garibaldi.topesteticabucal.com.br/sistema",
    "Veranópolis": "http://veranopolis.topesteticabucal.com.br/sistema",
    "SS do Caí": "http://ssdocai.topesteticabucal.com.br/sistema",
    "Flores": "http://flores.topesteticabucal.com.br/sistema",
}

OUTPUT_JSON = os.path.join("data", "metas_atual.json")


# ====== Selenium setup ======
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)


# ====== Navegação ======
def fazer_login(driver, base_url) -> bool:
    try:
        wait = WebDriverWait(driver, 30)
        driver.get(base_url)

        usuario = wait.until(EC.presence_of_element_located((By.ID, "usuario")))
        senha = wait.until(EC.presence_of_element_located((By.ID, "senha")))

        usuario.clear()
        usuario.send_keys(LOGIN_USER)

        senha.clear()
        senha.send_keys(LOGIN_PASS)

        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
        btn.click()

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        return True

    except Exception as e:
        print(f"Erro no login ({base_url}): {e}")
        return False


def ir_para_metas_via_menu(driver) -> bool:
    """
    Clica em FINANÇAS -> Metas, sem depender de <a>.
    Aceita variações com/sem acento e maiúsculas/minúsculas.
    """
    wait = WebDriverWait(driver, 30)

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        financas_xpath = (
            "//*[self::a or self::button or self::div or self::span]"
            "[contains(translate(normalize-space(.),"
            " 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇFINANÇASfinançasFINANCASfinancas',"
            " 'AAAAAEEEEIIIIOOOOOUUUUCFINANCASFINANCASFINANCASFINANCAS'),"
            " 'FINANCAS')]"
        )
        metas_xpath = (
            "//*[self::a or self::button or self::div or self::span]"
            "[contains(translate(normalize-space(.),"
            " 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇMETASmetas',"
            " 'AAAAAEEEEIIIIOOOOOUUUUCMETASMETAS'),"
            " 'METAS')]"
        )

        el_fin = wait.until(EC.element_to_be_clickable((By.XPATH, financas_xpath)))
        el_fin.click()
        time.sleep(1)

        el_metas = wait.until(EC.element_to_be_clickable((By.XPATH, metas_xpath)))
        el_metas.click()

        # Na página de metas do seu print existe o select "mes_ano"
        wait.until(EC.presence_of_element_located((By.ID, "mes_ano")))
        time.sleep(2)

        return True

    except Exception as e:
        print(f"Erro ao navegar FINANÇAS > Metas (menu): {e}")
        return False


def ir_para_metas_por_url(driver, base_url) -> bool:
    """
    Plano B: vai direto na URL da lista de metas.
    """
    try:
        wait = WebDriverWait(driver, 30)
        metas_url = base_url.rstrip("/") + "/index2.php?conteudo=lista_metas"
        driver.get(metas_url)

        wait.until(EC.presence_of_element_located((By.ID, "mes_ano")))
        time.sleep(2)
        return True

    except Exception as e:
        print(f"Erro ao abrir metas por URL ({base_url}): {e}")
        return False


def garantir_pagina_metas(driver, base_url, cidade) -> bool:
    debug_state(driver, f"{cidade} | antes do login")

    if not fazer_login(driver, base_url):
        debug_state(driver, f"{cidade} | falhou login")
        save_debug(driver, cidade, "falha_login")
        return False

    debug_state(driver, f"{cidade} | logou")

    if ir_para_metas_via_menu(driver):
        debug_state(driver, f"{cidade} | abriu metas via menu")
        return True

    debug_state(driver, f"{cidade} | falhou menu, tentando URL direta")
    ok = ir_para_metas_por_url(driver, base_url)
    if not ok:
        debug_state(driver, f"{cidade} | falhou URL direta")
        save_debug(driver, cidade, "falha_url_metas")
        return False

    debug_state(driver, f"{cidade} | abriu metas via URL direta")
    return True
def detectar_mes_ano(driver) -> str:
    try:
        sel = driver.find_element(By.ID, "mes_ano")
        for o in sel.find_elements(By.TAG_NAME, "option"):
            if o.is_selected():
                return o.text.strip()
    except Exception:
        pass
    return "N/A"


def extrair_tabelas(driver):
    tables = driver.find_elements(By.TAG_NAME, "table")
    all_tables = []

    for table in tables:
        rows = table.find_elements(By.TAG_NAME, "tr")
        t = []
        for r in rows:
            cells = r.find_elements(By.CSS_SELECTOR, "th,td")
            t.append([c.text.strip() for c in cells])

        if any(any(cell for cell in row) for row in t):
            all_tables.append(t)

    return all_tables


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

            if not garantir_pagina_metas(driver, url):
                print(f"Falha ao coletar dados de {cidade} (login/menu/url).")
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
