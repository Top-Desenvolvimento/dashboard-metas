#!/usr/bin/env python3
"""
Coleta de metas da Top Estética Bucal

Fluxo:
1. Faz login em cada unidade
2. Clica em FINANÇAS
3. Clica em Metas
4. Lê o que estiver visível na tela
5. Busca automaticamente o total atual de avaliações no Google
6. Calcula o indicador avaliacoes_google
7. Salva JSON / CSV / Excel
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

GOOGLE_REVIEW_URLS = {
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

INDICADORES_SISTEMA = {
    "ortodontia": ["Ortodontia"],
    "clinico_geral": ["Clínico Geral", "Clinico Geral"],
    "meta_avaliacao": ["Meta de Avaliação", "Meta de Avaliacao"],
    "meta_profilaxia": ["Meta de Profilaxia"],
    "meta_restauracao": ["Meta de Restauração", "Meta de Restauracao"],
}

ORDEM_INDICADORES = [
    "ortodontia",
    "clinico_geral",
    "avaliacoes_google",
    "meta_avaliacao",
    "meta_profilaxia",
    "meta_restauracao",
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
    chrome_options.add_argument("--lang=pt-BR")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(40)
    return driver


def normalizar_texto(texto):
    return " ".join((texto or "").replace("\xa0", " ").split()).strip()


def carregar_json_opcional(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def carregar_json_metas_existente():
    caminho = "data/metas_atual.json"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def carregar_google_inicial():
    return carregar_json_opcional("data/google_inicial.json")


def carregar_google_meta():
    return carregar_json_opcional("data/google_meta.json")


def inteiro_seguro(valor):
    try:
        texto = str(valor).strip()
        if not texto:
            return 0
        texto = texto.replace(".", "").replace(",", "")
        return int(texto)
    except Exception:
        return 0


def formatar_percentual_google(valor):
    return f"{valor:.1f}%".replace(".", ",")


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

        btn_financas = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[normalize-space(text())='FINANÇAS' or normalize-space(text())='Finanças']")
            )
        )
        driver.execute_script("arguments[0].click();", btn_financas)
        time.sleep(2)

        salvar_screenshot(driver, f"menu_financas_{cidade}.png")

        candidatos = [
            (By.LINK_TEXT, "Metas"),
            (By.PARTIAL_LINK_TEXT, "Metas"),
            (By.XPATH, "//a[normalize-space(text())='Metas']"),
            (By.XPATH, "//*[self::a or self::span or self::div][normalize-space(text())='Metas']"),
        ]

        clicou = False

        for by, value in candidatos:
            try:
                elem = wait.until(EC.presence_of_element_located((by, value)))
                driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", elem)
                clicou = True
                break
            except Exception:
                continue

        if not clicou:
            raise Exception("Submenu 'Metas' não encontrado ou não clicável")

        time.sleep(3)
        salvar_screenshot(driver, f"tela_metas_{cidade}.png")
        print(f"Tela de metas aberta em {cidade}: {driver.current_url}")
        return True

    except Exception as e:
        print(f"Erro ao abrir tela de metas em {cidade}: {e}")
        salvar_screenshot(driver, f"erro_tela_metas_{cidade}.png")
        return False


def obter_texto_tela(driver):
    return driver.find_element(By.TAG_NAME, "body").text or ""


def extrair_por_titulos(texto_completo, titulos):
    texto = normalizar_texto(texto_completo)

    for titulo in titulos:
        pattern = re.compile(
            rf"{re.escape(titulo)}\s+Até o momento\s+Falta\s+Progresso\s+"
            rf"(?:Meta(?:\s+desafio)?)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)",
            re.IGNORECASE
        )

        match = pattern.search(texto)
        if match:
            return {
                "meta": match.group(1).strip(),
                "ate_o_momento": match.group(2).strip(),
                "falta": match.group(3).strip(),
                "progresso": match.group(4).strip(),
            }

    return {
        "meta": "",
        "ate_o_momento": "",
        "falta": "",
        "progresso": "",
    }


def extrair_total_google_do_texto(texto):
    """
    Prioriza exatamente padrões como:
    '90 avaliações no Google'
    """
    if not texto:
        return None

    texto_norm = " ".join(str(texto).split())

    padroes_prioritarios = [
        r"(\d[\d.]*)\s+avaliações\s+no\s+Google",
        r"(\d[\d.]*)\s+avaliação\s+no\s+Google",
        r"(\d[\d.]*)\s+avaliações",
        r"(\d[\d.]*)\s+avaliação",
        r"(\d[\d.]*)\s+reviews",
        r"(\d[\d.]*)\s+review",
        r"(\d[\d.]*)\s+comentários",
        r"(\d[\d.]*)\s+comentário",
    ]

    for padrao in padroes_prioritarios:
        m = re.search(padrao, texto_norm, re.IGNORECASE)
        if m:
            try:
                valor = int(m.group(1).replace(".", ""))
                if 0 <= valor <= 50000:
                    return valor
            except Exception:
                pass

    return None


def obter_total_google(driver, cidade, url_google):
    """
    Busca o total atual de avaliações.
    Se o Google bloquear, retorna None.
    """
    if not url_google:
        return None

    aba_original = driver.current_window_handle

    try:
        print(f"Buscando avaliações Google de {cidade}...")
        driver.switch_to.new_window("tab")
        driver.get(url_google)
        time.sleep(6)

        salvar_screenshot(driver, f"google_{cidade}.png")

        texto = driver.find_element(By.TAG_NAME, "body").text
        pagina = driver.page_source

        print(f"Texto Google em {cidade}:")
        print(texto[:3000])

        bloqueios = [
            "About this page",
            "Sobre esta página",
            "unusual traffic",
            "tráfego incomum",
            "detected unusual traffic",
            "Our systems have detected unusual traffic",
        ]

        texto_total = f"{texto}\n{pagina}"
        if any(b.lower() in texto_total.lower() for b in bloqueios):
            print(f"Google bloqueou ou redirecionou a consulta em {cidade}.")
            return None

        total = extrair_total_google_do_texto(texto)

        if total is None:
            total = extrair_total_google_do_texto(pagina)

        if total is None:
            print(f"Nenhum total de avaliações encontrado em {cidade}.")
            return None

        print(f"Total Google encontrado em {cidade}: {total}")
        return total

    except Exception as e:
        print(f"Erro ao buscar Google de {cidade}: {e}")
        salvar_screenshot(driver, f"erro_google_{cidade}.png")
        return None

    finally:
        try:
            driver.close()
        except Exception:
            pass
        try:
            driver.switch_to.window(aba_original)
        except Exception:
            pass


def calcular_indicador_google(cidade, mes_referencia, atual_total, google_inicial, google_meta, anterior=None):
    """
    Se atual_total vier como None (bloqueio do Google), mantém o valor anterior.
    """
    if atual_total is None:
        if anterior:
            print(f"Mantendo último valor válido de Google para {cidade}.")
            return anterior

        return {
            "meta": "",
            "ate_o_momento": "",
            "falta": "",
            "progresso": "",
        }

    inicial_mes = inteiro_seguro(google_inicial.get(mes_referencia, {}).get(cidade, 0))
    meta_mes = inteiro_seguro(google_meta.get(mes_referencia, {}).get(cidade, 0))

    ate_o_momento = max(atual_total - inicial_mes, 0)

    if meta_mes > 0:
        falta = max(meta_mes - ate_o_momento, 0)
        progresso = (ate_o_momento / meta_mes) * 100
        progresso_txt = formatar_percentual_google(progresso)
        meta_txt = str(meta_mes)
        falta_txt = str(falta)
    else:
        progresso_txt = ""
        meta_txt = ""
        falta_txt = ""

    return {
        "meta": meta_txt,
        "ate_o_momento": str(ate_o_momento),
        "falta": falta_txt,
        "progresso": progresso_txt,
    }


def extrair_todas_metas(driver, cidade):
    texto = obter_texto_tela(driver)

    print(f"======== TEXTO COMPLETO DA PÁGINA EM {cidade} ========")
    print(texto)
    print(f"======== FIM DO TEXTO EM {cidade} ========")

    dados = {}
    for chave, titulos in INDICADORES_SISTEMA.items():
        dados[chave] = extrair_por_titulos(texto, titulos)

    dados["avaliacoes_google"] = {
        "meta": "",
        "ate_o_momento": "",
        "falta": "",
        "progresso": "",
    }

    print(f"Metas extraídas do sistema em {cidade}: {json.dumps(dados, ensure_ascii=False)}")
    salvar_screenshot(driver, f"metas_extraidas_{cidade}.png")
    return dados


def coletar_dados_todas_cidades():
    dados = {}
    driver = setup_driver()

    google_inicial = carregar_google_inicial()
    google_meta = carregar_google_meta()
    dados_anteriores = carregar_json_metas_existente()

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

                anterior_google = (
                    dados_anteriores.get(cidade, {})
                    .get("indicadores", {})
                    .get("avaliacoes_google", {})
                )

                total_google_atual = obter_total_google(
                    driver=driver,
                    cidade=cidade,
                    url_google=GOOGLE_REVIEW_URLS.get(cidade, ""),
                )

                metas["avaliacoes_google"] = calcular_indicador_google(
                    cidade=cidade,
                    mes_referencia=MES_REFERENCIA,
                    atual_total=total_google_atual,
                    google_inicial=google_inicial,
                    google_meta=google_meta,
                    anterior=anterior_google,
                )

                print(f"Indicador Google em {cidade}: {json.dumps(metas['avaliacoes_google'], ensure_ascii=False)}")

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
        for indicador in ORDEM_INDICADORES:
            valores = info.get("indicadores", {}).get(indicador, {})
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
        for indicador in ORDEM_INDICADORES:
            valores = info.get("indicadores", {}).get(indicador, {})
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
