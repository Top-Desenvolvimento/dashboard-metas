import os
import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

OUTPUT_PATH = os.path.join("data", "google_reviews.json")

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

def normalizar_numero(texto: str):
    if not texto:
        return None
    texto_limpo = texto.replace(".", "").replace(",", "").strip()
    return int(texto_limpo) if texto_limpo.isdigit() else None

def extrair_de_texto(texto: str):
    padroes = [
        r"(\d[\d\.\,]*)\s+avaliaç(?:ão|ões)",
        r"(\d[\d\.\,]*)\s+reviews",
        r"(\d[\d\.\,]*)\s+reseñas",
        r"Com\s+base\s+em\s+(\d[\d\.\,]*)\s+avaliaç(?:ão|ões)",
        r"Based\s+on\s+(\d[\d\.\,]*)\s+reviews",
        r"(\d[\d\.\,]*)\s+opiniões",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            numero = normalizar_numero(match.group(1))
            if numero is not None:
                return numero
    return None

def extrair_por_selectors(page):
    candidatos = [
        '[aria-label*="avalia"]',
        '[aria-label*="review"]',
        '[aria-label*="reseña"]',
    ]

    for selector in candidatos:
        try:
            textos = page.locator(selector).all_inner_texts()
            for texto in textos:
                numero = extrair_de_texto(texto)
                if numero is not None:
                    return numero
        except Exception:
            pass

    return None

def extrair_numero_avaliacoes(page):
    try:
        body_text = page.locator("body").inner_text(timeout=5000)
        numero = extrair_de_texto(body_text)
        if numero is not None:
            return numero
    except Exception:
        pass

    numero = extrair_por_selectors(page)
    if numero is not None:
        return numero

    return None

def coletar_reviews(page, unidade):
    cidade = unidade["cidade"]
    url = unidade["url"]
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

        final_url = page.url
        total = extrair_numero_avaliacoes(page)

        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": total,
            "url_origem": url,
            "url_final": final_url,
            "status": "ok" if total is not None else "nao_encontrado"
        }

    except PlaywrightTimeoutError:
        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": None,
            "url_origem": url,
            "url_final": None,
            "status": "timeout"
        }
    except Exception as e:
        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": None,
            "url_origem": url,
            "url_final": None,
            "status": f"erro: {str(e)}"
        }

def main():
    os.makedirs("data", exist_ok=True)
    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for unidade in UNIDADES:
            print(f"Coletando Google Reviews: {unidade['cidade']}")
            resultado = coletar_reviews(page, unidade)
            print(f"Resultado {unidade['cidade']}: {resultado['status']} | avaliações={resultado['avaliacoes']}")
            resultados.append(resultado)

        context.close()
        browser.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"Arquivo salvo em: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
