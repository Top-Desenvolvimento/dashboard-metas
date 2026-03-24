import os
import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

OUTPUT_PATH = os.path.join("data", "google_reviews.json")
DEBUG_DIR = os.path.join("data", "google_debug")

UNIDADES = [
    {
        "cidade": "Caxias",
        "url": "https://www.google.com/search?q=top+estetica+bucal+caxias+do+sul&oq=top+estetica+bucal+caxias+do+sul+&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIICAEQABgWGB4yCAgCEAAYFhgeMggIAxAAGBYYHjIICAQQABgWGB4yBwgFEAAY7wUyBggGEEUYPDIGCAcQRRg80gEINjM3MWowajSoAgCwAgE&sourceid=chrome&ie=UTF-8#lrd=0x951ea32648147b35:0xcd0259b76311b8a,1,,,,"
    },
    {
        "cidade": "Farroupilha",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+farroupilha&sca_esv=1b9fc756e6c3b46d&sxsrf=ANbL-n6B9NnnGGX5pWbdvNmf-KO1YFmdsg%3A1774363046227&ei=pqHCac--Dcfe1sQP3fK26A0&biw=1536&bih=695&gs_ssp=eJzj4tVP1zc0TMtNM88wMkw2YLRSNaiwNDVMTTQ0TU4xt0xNMza0tDKoMEw2NjUxtkwEkuaGSUaJXvIl-QUKqcUlh1eWZCYnKiSVJifmKKQlFhXllxZk5mQkAgBFfRtw&oq=top+estetica+bucal+farrpup&gs_lp=Egxnd3Mtd2l6LXNlcnAiGnRvcCBlc3RldGljYSBidWNhbCBmYXJycHVwKgIIADINEC4YgAQYxwEYDRivATIFEAAY7wUyBRAAGO8FMgUQABjvBTIFEAAY7wUyHBAuGIAEGMcBGA0YrwEYlwUY3AQY3gQY4ATYAQFI4hlQ9QFY5ApwAXgBkAEAmAHlAaABlgqqAQUwLjUuMrgBAcgBAPgBAZgCCKACrQvCAgoQABiwAxjWBBhHwgILEC4YgAQYxwEYrwHCAgYQABgWGB7CAhoQLhiABBjHARivARiXBRjcBBjeBBjgBNgBAcICAhAmwgIIEAAYgAQYogSYAwCIBgGQBgi6BgYIARABGBSSBwUxLjMuNKAHyVWyBwUwLjMuNLgHogvCBwcyLTEuNC4zyAd6gAgA&sclient=gws-wiz-serp#lrd=0x951ea15cd79ef319:0x1c35439a35471b2a,1,,,,"
    },
    {
        "cidade": "Flores",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+flores&sca_esv=1b9fc756e6c3b46d&biw=1536&bih=695&sxsrf=ANbL-n70ypGkBvmAz2aWP_8iwXUk1niA0Q%3A1774363120979&ei=8KHCaYmwO6zL1sQP74OTyQE&ved=0ahUKEwiJ6Jzc4biTAxWspZUCHe_BJBkQ4dUDCBE&uact=5&oq=top+est%C3%A9tica+bucal+flores&gs_lp=Egxnd3Mtd2l6LXNlcnAiGnRvcCBlc3TDqXRpY2EgYnVjYWwgZmxvcmVzMgsQLhiABBjHARivATIGEAAYFhgeMgYQABgWGB4yBhAAGBYYHjIGEAAYFhgeMgIQJjIIEAAYgAQYogQyCBAAGIAEGKIEMgUQABjvBTIaEC4YgAQYxwEYrwEYlwUY3AQY3gQY4ATYAQFIpw9Q7wdYww1wAngBkAEAmAGgAqABvgiqAQUwLjUuMbgBA8gBAPgBAZgCCKACkwnCAgoQABiwAxjWBBhHwgITEC4YgAQYxwEYJxiKBRiOBRivAcICIBAuGIAEGMcBGIoFGI4FGK8BGJcFGNwEGN4EGOAE2AEBmAMAiAYBkAYIugYGCAEQARgUkgcFMi41LjGgB6ZSsgcFMC41LjG4B_wIwgcFMi01LjPIB0KACAA&sclient=gws-wiz-serp#lrd=0x951e9a09f521accb:0x3d40ee273b4c1644,1,,,,"
    },
    {
        "cidade": "Bento",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+bento+gon%C3%A7alves&sca_esv=1b9fc756e6c3b46d&biw=1536&bih=695&sxsrf=ANbL-n5r9Q-1cNM7f93akW-g3XWTGWJnMA%3A1774363190203&ei=NqLCaciEDI7w1sQPtvq-2A4&oq=top+est%C3%A9tica+bucal+bento&gs_lp=Egxnd3Mtd2l6LXNlcnAiGXRvcCBlc3TDqXRpY2EgYnVjYWwgYmVudG8qAggAMgcQIxiwAxgnMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHMgoQABiwAxjWBBhHSLYMUABYAHABeAGQAQCYAQCgAQCqAQC4AQHIAQCYAgGgAgyYAwCIBgGQBgmSBwExoAcAsgcAuAcAwgcDMy0xyAcKgAgA&sclient=gws-wiz-serp#lrd=0x951c3cad11fbee27:0x859a21c146dbd6f1,1,,,,"
    },
    {
        "cidade": "Encantado",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+encantado&biw=1536&bih=695&sca_esv=1b9fc756e6c3b46d&sxsrf=ANbL-n64kd16Vh2C9ij5J2_1SdcHEeF3wQ%3A1774363205850&ei=RaLCaajNM9mp1sQP4teJ0Aw&ved=0ahUKEwjog9mE4riTAxXZlJUCHeJrAsoQ4dUDCBE&uact=5&oq=top+est%C3%A9tica+bucal+encantado&gs_lp=Egxnd3Mtd2l6LXNlcnAiHXRvcCBlc3TDqXRpY2EgYnVjYWwgZW5jYW50YWRvMgsQLhiABBjHARivATIGEAAYFhgeMgYQABgWGB4yBRAAGO8FMggQABiABBiiBDIIEAAYgAQYogQyBRAAGO8FMhoQLhiABBjHARivARiXBRjcBBjeBBjgBNgBAUjlD1CxA1iDDHABeAGQAQCYAbQBoAGSC6oBAzAuObgBA8gBAPgBAZgCCqAC8gvCAgoQABiwAxjWBBhHwgICECaYAwCIBgGQBgi6BgYIARABGBSSBwMxLjmgB8ZUsgcDMC45uAfpC8IHBTItOC4yyAdOgAgA&sclient=gws-wiz-serp#lrd=0x951c5bb4959de801:0xfd5a6016d1665a18,1,,,,"
    },
    {
        "cidade": "Soledade",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+soledade&biw=1536&bih=695&sca_esv=1b9fc756e6c3b46d&sxsrf=ANbL-n5cUflWQGzUWYZb_B4eP_BG0_Ad0g%3A1774363231723&ei=X6LCac_sK5_I1sQP1uuRoAs&ved=0ahUKEwiPmISR4riTAxUfpJUCHdZ1BLQQ4dUDCBE&uact=5&oq=top+est%C3%A9tica+bucal+soledade&gs_lp=Egxnd3Mtd2l6LXNlcnAiHHRvcCBlc3TDqXRpY2EgYnVjYWwgc29sZWRhZGUyCxAuGIAEGMcBGK8BMgYQABgWGB4yBhAAGBYYHjIGEAAYFhgeMgYQABgWGB4yCBAAGIAEGKIEMgUQABjvBTIFEAAY7wUyGhAuGIAEGMcBGK8BGJcFGNwEGN4EGOAE2AEBSOYRUIAGWIIOcAJ4AZABAJgBrAGgAfoJqgEDMC44uAEDyAEA-AEBmAIKoALlCsICChAAGLADGNYEGEfCAggQABgWGAoYHpgDAIgGAZAGCLoGBggBEAEYFJIHAzIuOKAH6FqyBwMwLji4B9QKwgcFMi0zLjfIB1iACAA&sclient=gws-wiz-serp#lrd=0x951d4521b7eb8f11:0x9d745614261288fd,1,,,,"
    },
    {
        "cidade": "Veranópolis",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+veranopolis&biw=1536&bih=695&sca_esv=1b9fc756e6c3b46d&sxsrf=ANbL-n7ZP-TzQfuG8uPOPHs68SPoiU84Pw%3A1774363250435&ei=cqLCaZqdGoPJ1sQPuvWEsAI&ved=0ahUKEwianvqZ4riTAxWDpJUCHbo6ASYQ4dUDCBE&uact=5&oq=top+est%C3%A9tica+bucal+veranopolis&gs_lp=Egxnd3Mtd2l6LXNlcnAiH3RvcCBlc3TDqXRpY2EgYnVjYWwgdmVyYW5vcG9saXMyBhAAGBYYHjIGEAAYFhgeMgIQJjIIEAAYgAQYogQyBRAAGO8FMggQABiABBiiBDIFEAAY7wUyBRAAGO8FSIYSUNcFWLsQcAJ4AZABAJgB4QGgAZwQqgEFMC45LjK4AQPIAQD4AQGYAg2gAq0RwgIKEAAYsAMY1gQYR8ICCxAuGIAEGMcBGK8BwgIaEC4YgAQYxwEYrwEYlwUY3AQY3gQY4ATYAQGYAwCIBgGQBgi6BgYIARABGBSSBwUyLjYuNaAHz1eyBwUwLjYuNbgHnxHCBwUyLTcuNsgHcYAIAA&sclient=gws-wiz-serp#lrd=0x94cdd81458d748b1:0xd42ae7b49b227e5,1,,,,"
    },
    {
        "cidade": "Garibaldi",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+garibaldi&biw=1536&bih=695&sca_esv=1b9fc756e6c3b46d&sxsrf=ANbL-n70RUJpyrQ2TddqmSb-ErJoQOv8CA%3A1774363272767&ei=iKLCacq3LvLM1sQPtNLq2AU&gs_ssp=eJzj4tVP1zc0zKiyNCguycs1YLRSNaiwNDVMNjRPNTBJtTRKS0oytTKoSDJNSzY3MUwEksappkYmXrIl-QUKqcUlh1eWZCYnKiSVJifmKKQnFmUmJeakZAIAROUbcQ&oq=top+est%C3%A9tica+bucal+garibaldi&gs_lp=Egxnd3Mtd2l6LXNlcnAiHXRvcCBlc3TDqXRpY2EgYnVjYWwgZ2FyaWJhbGRpKgIIADILEC4YgAQYxwEYrwEyBhAAGBYYHjIGEAAYFhgeMgIQJjIIEAAYgAQYogQyBRAAGO8FMgUQABjvBTIIEAAYgAQYogQyGhAuGIAEGMcBGK8BGJcFGNwEGN4EGOAE2AEBSNEdULMHWIsPcAJ4AZABAJgBsQGgAaULqgEDMC45uAEByAEA-AEBmAILoAKGDMICChAAGLADGNYEGEeYAwCIBgGQBgi6BgYIARABGBSSBwMyLjmgB_5esgcDMC45uAf0C8IHBTItOS4yyAdOgAgA&sclient=gws-wiz-serp#lrd=0x951c17e04e92fbb5:0xb5fc741afc73e524,1,,,,"
    },
    {
        "cidade": "SS do Caí",
        "url": "https://www.google.com/search?q=top+est%C3%A9tica+bucal+s%C3%A3o+sebasti%C3%A3o+do+ca%C3%AD&biw=1536&bih=695&sca_esv=1b9fc756e6c3b46d&sxsrf=ANbL-n4V8W9zCgAcRaGCo0xJ4JyF_o2C5A%3A1774363289235&ei=maLCafmEDteq1sQPy4XYoQY&gs_ssp=eJzj4tVP1zc0LMxLKkhON8s1YLRSNaiwNDVMSktJNU42SDZPTjFMszKoSLNMTjVPNU5KTDZMMzU3MfPSLskvUEgtLjm8siQzOVEhqTQ5MUeh-PDifIXi1KTE4pJMEDMlXyE58fBaADyKIyU&oq=top+est%C3%A9tica+bucal+s&gs_lp=Egxnd3Mtd2l6LXNlcnAiFXRvcCBlc3TDqXRpY2EgYnVjYWwgcyoCCAIyChAjGIAEGCcYigUyEBAuGIAEGBQYhwIYxwEYrwEyCxAuGIAEGMcBGK8BMgYQABgWGB4yBhAAGBYYHjIGEAAYFhgeMgYQABgWGB4yBhAAGBYYHjIGEAAYFhgeMgYQABgWGB4yHxAuGIAEGBQYhwIYxwEYrwEYlwUY3AQY3gQY4ATYAQFI1xhQ7AZYiwxwA3gBkAEAmAHOAaAB9QKqAQUwLjEuMbgBAcgBAPgBAZgCBaACogPCAgoQABiwAxjWBBhHwgIIEAAYFhgKGB7CAgIQJsICCBAAGIAEGKIEwgIFEAAY7wWYAwCIBgGQBgi6BgYIARABGBSSBwUzLjEuMaAH-hmyBwUwLjEuMbgHiwPCBwUyLTMuMsgHJIAIAA&sclient=gws-wiz-serp#lrd=0x951bfde3c0c7cd1f:0xf9ce7e3bac1f5746,1,,,,"
    }
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

def salvar_debug(cidade, texto, html):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    base = slug(cidade)

    with open(os.path.join(DEBUG_DIR, f"{base}.txt"), "w", encoding="utf-8") as f:
        f.write(texto or "")

    with open(os.path.join(DEBUG_DIR, f"{base}.html"), "w", encoding="utf-8") as f:
        f.write(html or "")

def normalizar_numero(texto: str):
    if not texto:
        return None
    texto_limpo = texto.replace(".", "").replace(",", "").strip()
    return int(texto_limpo) if texto_limpo.isdigit() else None

def extrair_de_texto(texto: str):
    padroes = [
        r"(\d[\d\.\,]*)\s+avaliaç(?:ão|ões)",
        r"(\d[\d\.\,]*)\s+reviews",
        r"(\d[\d\.\,]*)\s+opiniões",
        r"Com\s+base\s+em\s+(\d[\d\.\,]*)\s+avaliaç(?:ão|ões)",
        r"Based\s+on\s+(\d[\d\.\,]*)\s+reviews",
        r"Avaliaç(?:ão|ões)\s*\(?\s*(\d[\d\.\,]*)\s*\)?",
        r"Reviews\s*\(?\s*(\d[\d\.\,]*)\s*\)?",
    ]
    for padrao in padroes:
        m = re.search(padrao, texto, re.IGNORECASE)
        if m:
            numero = normalizar_numero(m.group(1))
            if numero is not None:
                return numero, padrao
    return None, None

def extrair_por_aria_label(page):
    seletores = [
        '[aria-label*="avalia"]',
        '[aria-label*="review"]',
        '[aria-label*="opini"]',
        'span[aria-label*="avalia"]',
        'span[aria-label*="review"]',
        'div[aria-label*="avalia"]',
        'div[aria-label*="review"]',
    ]

    for seletor in seletores:
        try:
            textos = page.locator(seletor).evaluate_all(
                "(els) => els.map(el => (el.getAttribute('aria-label') || '') + ' ' + (el.innerText || ''))"
            )
            for texto in textos:
                numero, origem = extrair_de_texto(texto)
                if numero is not None:
                    return numero, f"aria:{seletor}|{origem}"
        except Exception:
            pass

    return None, None

def extrair_numero_avaliacoes(page):
    body_text = ""
    html = ""

    try:
        body_text = page.locator("body").inner_text(timeout=10000)
    except Exception:
        pass

    try:
        html = page.content()
    except Exception:
        pass

    numero, origem = extrair_de_texto(body_text)
    if numero is not None:
        return numero, origem, body_text, html

    numero, origem = extrair_por_aria_label(page)
    if numero is not None:
        return numero, origem, body_text, html

    return None, None, body_text, html

def coletar_reviews(page, unidade):
    cidade = unidade["cidade"]
    url = unidade["url"]
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)

        final_url = page.url
        numero, origem_extracao, texto, html = extrair_numero_avaliacoes(page)
        salvar_debug(cidade, texto, html)

        status = "ok" if numero is not None else "nao_encontrado"
        if "/sorry/" in final_url:
            status = "bloqueado_google_sorry"

        return {
            "data_hora": agora,
            "cidade": cidade,
            "origem": "Google",
            "avaliacoes": numero,
            "url_origem": url,
            "url_final": final_url,
            "origem_extracao": origem_extracao,
            "status": status
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
            viewport={"width": 1536, "height": 900},
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
                f"{unidade['cidade']} -> "
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

if __name__ == "__main__":
    main()
