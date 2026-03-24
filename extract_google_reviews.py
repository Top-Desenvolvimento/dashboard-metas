import os
import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

OUTPUT_PATH = os.path.join("data", "google_reviews.json")
DEBUG_DIR = os.path.join("data", "google_debug")

UNIDADES = [
    {"cidade": "Flores", "url": "https://share.google/3f8yPEfrb24AQYYOp"},
    {"cidade": "Caxias", "url": "https://share.google/ffSPadgdvp8WUEXq0"},
    {"cidade": "Farroupilha", "url": "https://share.google/g1snAopsGqM5I8sOl"},
    {"cidade": "Bento", "url": "https://share.google/sEdZu4jHIPYL77RA6"},
    {"cidade": "Encantado", "url": "https://share.google/5CUABlRksD1cPYWiK"},
    {"cidade": "Soledade", "url": "https://share.google/rOGEnBONHO2kTYVk3"},
    {"cidade": "Garibaldi", "url": "https://share.google/UlnGSp8MES2AnB7Yz"},
    {"cidade": "Veranópolis", "url": "https://share.google/33XgmkKW7UnW8o8WB"},
    {"cidade": "SS do Caí", "url": "https://share.google/U2cO3MWeXsKQZUenB"},
]

def slug(texto: str) -> str:
    texto = texto.lower().strip()
    mapa = {
        "ã": "a", "á": "a", "à": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for a, b in mapa.items():
        texto = texto.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")

def normalizar_numero(texto: str):
    if not texto:
        return None
    texto_limpo = texto.replace(".", "").replace(",", "").strip()
    return int(texto_limpo) if texto_limpo.isdigit() else None

def salvar_debug(cidade, texto, html):
    os.makedirs(DEBUG_DIR, exist_ok=True)

    nome = slug(cidade)
    txt_path = os.path.join(DEBUG_DIR, f"{nome}.txt")
    html_path = os.path.join(DEBUG_DIR, f"{nome}.html")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(texto or "")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html or "")

def extrair_de_texto(texto: str):
    padroes = [
        r"(\d[\d\.\,]*)\s+avaliaç(?:ão|ões)",
        r"(\d[\d\.\,]*)\s+reviews",
        r"(\d[\d\.\,]*)\s+reseñas",
        r"Com\s+base\s+em\s+(\d[\d\.\,]*)\s+avaliaç(?:ão|ões)",
        r"Based\s+on\s+(\d[\d\.\,]*)\s+reviews",
        r"(\d[\d\.\,]*)\s+opiniões",
        r"(\d[\d\.\,]*)\s+Google reviews",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            numero = normalizar_numero(match.group(1))
            if numero is not None:
                return numero, f"regex:{padrao}"
    return None, None

def extrair_por_selectors(page):
    candidatos = [
        '[aria-label*="avalia"]',
        '[aria-label*="review"]',
        '[aria-label*="reseña"]',
        '[aria-label*="opini"]',
        'span[aria-label*="avalia"]',
        'span[aria-label*="review"]',
        'div[aria-label*="review"]',
    ]

    for selector in candidatos:
        try:
            textos = page.locator(selector).all_inner_texts()
            for texto in textos:
                numero, origem = extrair_de_texto(texto)
                if numero is not None:
                    return numero, f"selector:{selector}|{origem}"
        except Exception:
            pass

    return None, None

def extrair_por_links(page):
    try:
        textos = page.locator("a").all_inner_texts()
        for texto in textos:
            numero, origem = extrair_de_texto(texto)
            if numero is not None:
                return numero, f"link|{origem}"
    except Exception:
        pass
    return None, None

def extrair_numero_avaliacoes(page):
    body_text = ""
    html = ""

    try:
        body_text = page.locator("body").inner_text(timeout=8000)
    except Exception:
        pass

    try:
        html = page.content()
    except Exception:
        pass

    numero, origem = extrair_de_texto(body_text)
    if numero is not None:
        return numero, origem, body_text, html

    numero, origem = extrair_por_selectors(page)
    if numero is not None:
        return numero, origem, body_text, html

    numero, origem = extrair_por_links(page)
    if numero is not None:
        return numero, origem, body_text, html

    return None, None, body_text, html

def coletar_reviews(page, unidade):
    cidade = unidade["cidade"]
    url = unidade["url"]
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)

        numero, origem_extracao, texto, html = extrair_numero_avaliacoes(page)
        salvar_debug(cidade, texto, html)

        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": numero,
            "url_origem": url,
            "url_final": page.url,
            "origem_extracao": origem_extracao,
            "status": "ok" if numero is not None else "nao_encontrado"
        }

    except PlaywrightTimeoutError:
        salvar_debug(cidade, "", "")
        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": None,
            "url_origem": url,
            "url_final": None,
            "origem_extracao": None,
            "status": "timeout"
        }
    except Exception as e:
        salvar_debug(cidade, "", "")
        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": None,
            "url_origem": url,
            "url_final": None,
            "origem_extracao": None,
            "status": f"erro: {str(e)}"
        }

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            locale="pt-BR",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for unidade in UNIDADES:
            print(f"Coletando Google: {unidade['cidade']}")
            resultado = coletar_reviews(page, unidade)
            print(
                f"Resultado {unidade['cidade']}: "
                f"status={resultado['status']} | "
                f"avaliacoes={resultado['avaliacoes']} | "
                f"origem={resultado['origem_extracao']}"
            )
            resultados.append(resultado)

        context.close()
        browser.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"Arquivo gerado: {OUTPUT_PATH}")
    print(f"Arquivos de debug salvos em: {DEBUG_DIR}")

if __name__ == "__main__":
    main()
