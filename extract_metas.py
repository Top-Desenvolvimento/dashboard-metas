import os
import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

LOGIN_USER = os.getenv("LOGIN_USER") or os.getenv("SYSTEM_LOGIN")
LOGIN_PASS = os.getenv("LOGIN_PASS") or os.getenv("SYSTEM_PASSWORD")
MES_REFERENCIA = os.getenv("MES_REFERENCIA", "AUTO")

OUTPUT_JSON = "data/metas_atual.json"
OUTPUT_XLSX = "data/metas_top_estetica.xlsx"

CIDADES = [
    {"nome": "Flores", "url": "http://flores.topesteticabucal.com.br/sistema"},
    {"nome": "Caxias", "url": "http://caxias.topesteticabucal.com.br/sistema"},
    {"nome": "Farroupilha", "url": "http://farroupilha.topesteticabucal.com.br/sistema"},
    {"nome": "Bento", "url": "http://bento.topesteticabucal.com.br/sistema"},
    {"nome": "Encantado", "url": "https://encantado.topesteticabucal.com.br/sistema"},
    {"nome": "Soledade", "url": "http://soledade.topesteticabucal.com.br/sistema"},
    {"nome": "Garibaldi", "url": "http://garibaldi.topesteticabucal.com.br/sistema"},
    {"nome": "Veranópolis", "url": "http://veranopolis.topesteticabucal.com.br/sistema"},
    {"nome": "SS do Caí", "url": "https://ssdocai.topesteticabucal.com.br/sistema/"},
]

MAPA_CHAVES = {
    "ortodontia": "ortodontia",
    "orto": "ortodontia",
    "clinico geral": "clinico_geral",
    "clínico geral": "clinico_geral",
    "clinico_geral": "clinico_geral",
    "avaliação": "meta_avaliacao",
    "avaliacao": "meta_avaliacao",
    "meta de avaliação": "meta_avaliacao",
    "meta de avaliacao": "meta_avaliacao",
    "profilaxia": "meta_profilaxia",
    "meta de profilaxia": "meta_profilaxia",
    "restauração": "meta_restauracao",
    "restauracao": "meta_restauracao",
    "meta de restauração": "meta_restauracao",
    "meta de restauracao": "meta_restauracao",
}

INDICADORES_BASE = [
    "ortodontia",
    "clinico_geral",
    "avaliacoes_google",
    "meta_avaliacao",
    "meta_profilaxia",
    "meta_restauracao",
]


def normalizar_texto(texto: str) -> str:
    texto = (texto or "").strip().lower()
    trocas = {
        "ã": "a", "á": "a", "à": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for a, b in trocas.items():
        texto = texto.replace(a, b)
    return re.sub(r"\s+", " ", texto)


def garantir_indicadores_vazios():
    base = {}
    for chave in INDICADORES_BASE:
        base[chave] = {
            "meta": "-",
            "ate_o_momento": "-",
            "falta": "-",
            "progresso": "-"
        }
    return base


def inferir_chave_indicador(nome_linha: str):
    nome = normalizar_texto(nome_linha)

    if nome in MAPA_CHAVES:
        return MAPA_CHAVES[nome]

    for trecho, chave in MAPA_CHAVES.items():
        if trecho in nome:
            return chave

    return None


def obter_mes_referencia(page):
    try:
        valor = page.evaluate("""() => {
            const select = document.getElementById('mes_ano');
            if (!select) return null;
            const selected = select.options[select.selectedIndex];
            if (!selected) return null;
            return selected.value || selected.text || null;
        }""")
        if not valor:
            return datetime.now().strftime("%Y-%m")
        valor = str(valor).strip()

        # tenta converter MM/YYYY em YYYY-MM
        m = re.match(r"^(\d{2})/(\d{4})$", valor)
        if m:
            return f"{m.group(2)}-{m.group(1)}"

        # já está em YYYY-MM
        m = re.match(r"^(\d{4})-(\d{2})$", valor)
        if m:
            return valor

        return datetime.now().strftime("%Y-%m")
    except Exception:
        return datetime.now().strftime("%Y-%m")


def login(page, base_url):
    page.goto(base_url, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    page.fill("#usuario", LOGIN_USER)
    page.fill("#senha", LOGIN_PASS)
    page.click("input[type='submit']")
    page.wait_for_timeout(4000)


def abrir_metas(page, base_url):
    metas_url = base_url.rstrip("/") + "/index2.php?conteudo=lista_metas"
    if base_url.endswith("/sistema/"):
        metas_url = base_url + "index2.php?conteudo=lista_metas"

    page.goto(metas_url, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # tenta novamente se redirecionou
    if "index.php?redir=" in page.url:
        page.wait_for_timeout(2000)
        page.goto(metas_url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)


def extrair_tabelas(page):
    return page.evaluate("""() => {
        const tables = Array.from(document.querySelectorAll('table'));
        return tables.map(table => {
            return Array.from(table.querySelectorAll('tr')).map(tr => {
                return Array.from(tr.querySelectorAll('td, th')).map(td => td.innerText.trim());
            });
        });
    }""")


def processar_tabela_em_indicadores(tabela):
    indicadores = {}

    for i in range(0, len(tabela), 3):
        if i + 2 >= len(tabela):
            continue

        cab = tabela[i]
        dados = tabela[i + 2]

        if not cab or not dados:
            continue

        nome = cab[0].strip() if cab else ""
        chave = inferir_chave_indicador(nome)

        if not chave:
            continue

        if len(dados) < 5:
            continue

        indicadores[chave] = {
            "meta": dados[1].strip() if len(dados) > 1 else "-",
            "ate_o_momento": dados[2].strip() if len(dados) > 2 else "-",
            "falta": dados[3].strip() if len(dados) > 3 else "-",
            "progresso": dados[4].strip() if len(dados) > 4 else "-",
        }

    return indicadores


def extrair_cidade(page, cidade_info):
    nome = cidade_info["nome"]
    base_url = cidade_info["url"]

    print(f"Coletando {nome}...")

    try:
        login(page, base_url)
        abrir_metas(page, base_url)

        tabelas = extrair_tabelas(page)
        mes_referencia = obter_mes_referencia(page)

        indicadores = garantir_indicadores_vazios()

        if len(tabelas) > 0:
            indicadores.update(processar_tabela_em_indicadores(tabelas[0]))

        if len(tabelas) > 1:
            indicadores.update(processar_tabela_em_indicadores(tabelas[1]))

        return {
            "mes_referencia": mes_referencia,
            "indicadores": indicadores,
            "_status": "ok"
        }

    except PlaywrightTimeoutError:
        print(f"Timeout em {nome}")
        return {
            "mes_referencia": datetime.now().strftime("%Y-%m"),
            "indicadores": garantir_indicadores_vazios(),
            "_status": "timeout"
        }
    except Exception as e:
        print(f"Erro em {nome}: {e}")
        return {
            "mes_referencia": datetime.now().strftime("%Y-%m"),
            "indicadores": garantir_indicadores_vazios(),
            "_status": f"erro: {str(e)}"
        }


def salvar_excel_placeholder():
    # Mantém o botão de download da dashboard sem quebrar.
    # Se você já tem uma geração Excel mais completa, dá para recolocar depois.
    if not os.path.exists(OUTPUT_XLSX):
        with open(OUTPUT_XLSX, "wb") as f:
            f.write(b"")


def main():
    print("=" * 55)
    print("Iniciando coleta de dados - Top Estética Bucal")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Mês de referência: {datetime.now().strftime('%Y-%m') if MES_REFERENCIA == 'AUTO' else MES_REFERENCIA}")
    print("=" * 55)

    if not LOGIN_USER or not LOGIN_PASS:
        raise ValueError("LOGIN_USER ou LOGIN_PASS não configurados.")

    os.makedirs("data", exist_ok=True)

    resultado = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            locale="pt-BR",
            viewport={"width": 1440, "height": 900}
        )
        page = context.new_page()

        for cidade in CIDADES:
            resultado[cidade["nome"]] = extrair_cidade(page, cidade)

        context.close()
        browser.close()

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    salvar_excel_placeholder()

    print(f"Arquivo gerado: {OUTPUT_JSON}")
    print("Coleta finalizada com sucesso.")


if __name__ == "__main__":
    main()
