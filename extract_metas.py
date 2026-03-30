import os
import json
import re
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

LOGIN_USER = os.getenv("LOGIN_USER") or os.getenv("SYSTEM_LOGIN")
LOGIN_PASS = os.getenv("LOGIN_PASS") or os.getenv("SYSTEM_PASSWORD")
MES_REFERENCIA = os.getenv("MES_REFERENCIA", "AUTO")

OUTPUT_JSON = "data/metas_atual.json"
OUTPUT_XLSX = "data/metas_top_estetica.xlsx"

TZ = ZoneInfo("America/Sao_Paulo") if ZoneInfo else None

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

MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

MESES_PT_REV = {
    "janeiro": "01",
    "fevereiro": "02",
    "março": "03",
    "marco": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12",
}


def agora():
    if TZ:
        return datetime.now(TZ)
    return datetime.now()


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


def obter_mes_tela():
    """
    Retorna o mês no formato exibido no select do sistema.
    Exemplos:
    - Março / 2026
    - Abril / 2026
    """
    if MES_REFERENCIA and MES_REFERENCIA != "AUTO":
        texto = MES_REFERENCIA.strip()

        # Já veio no formato da tela
        if " / " in texto:
            return texto

        # Veio em MM/YYYY
        mm_yyyy = re.match(r"^(\d{2})/(\d{4})$", texto)
        if mm_yyyy:
            mes_num = int(mm_yyyy.group(1))
            ano = mm_yyyy.group(2)
            return f"{MESES_PT[mes_num]} / {ano}"

        # Veio em YYYY-MM
        yyyy_mm = re.match(r"^(\d{4})-(\d{2})$", texto)
        if yyyy_mm:
            ano = yyyy_mm.group(1)
            mes_num = int(yyyy_mm.group(2))
            return f"{MESES_PT[mes_num]} / {ano}"

        return texto

    dt = agora()
    return f"{MESES_PT[dt.month]} / {dt.year}"


def obter_mes_referencia_json():
    """
    Retorna o mês em YYYY-MM para salvar no JSON.
    """
    if MES_REFERENCIA and MES_REFERENCIA != "AUTO":
        texto = MES_REFERENCIA.strip()

        # YYYY-MM
        if re.match(r"^\d{4}-\d{2}$", texto):
            return texto

        # MM/YYYY
        mm_yyyy = re.match(r"^(\d{2})/(\d{4})$", texto)
        if mm_yyyy:
            return f"{mm_yyyy.group(2)}-{mm_yyyy.group(1)}"

        # Nome do mês / ano
        mes_nome = re.match(r"^([A-Za-zÀ-ÿçÇ]+)\s*/\s*(\d{4})$", texto)
        if mes_nome:
            nome = normalizar_texto(mes_nome.group(1))
            ano = mes_nome.group(2)
            mes = MESES_PT_REV.get(nome)
            if mes:
                return f"{ano}-{mes}"

    return agora().strftime("%Y-%m")


def converter_mes_para_json(valor):
    """
    Converte o valor/texto selecionado no sistema para YYYY-MM.
    """
    if not valor:
        return obter_mes_referencia_json()

    texto = str(valor).strip()

    # Se for value em YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", texto):
        return texto

    # Se for value em MM/YYYY
    mm_yyyy = re.match(r"^(\d{2})/(\d{4})$", texto)
    if mm_yyyy:
        return f"{mm_yyyy.group(2)}-{mm_yyyy.group(1)}"

    # Se vier como "Março / 2026"
    mes_nome = re.match(r"^([A-Za-zÀ-ÿçÇ]+)\s*/\s*(\d{4})$", texto)
    if mes_nome:
        nome = normalizar_texto(mes_nome.group(1))
        ano = mes_nome.group(2)
        mes = MESES_PT_REV.get(nome)
        if mes:
            return f"{ano}-{mes}"

    return obter_mes_referencia_json()


def obter_mes_referencia(page):
    try:
        valor = page.evaluate("""() => {
            const select = document.getElementById('mes_ano');
            if (!select) return null;
            const selected = select.options[select.selectedIndex];
            if (!selected) return null;

            return {
                value: selected.value || null,
                text: selected.text || null
            };
        }""")

        if not valor:
            return obter_mes_referencia_json()

        return converter_mes_para_json(valor.get("value") or valor.get("text"))
    except Exception:
        return obter_mes_referencia_json()


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


def selecionar_mes_e_buscar(page):
    """
    Seleciona o Mês/Ano no select #mes_ano e clica em Buscar.
    """
    mes_tela = obter_mes_tela()
    print(f"📅 Selecionando mês/ano: {mes_tela}")

    select_mes = page.locator("#mes_ano")

    if select_mes.count() == 0:
        raise RuntimeError("Não encontrei o select #mes_ano na tela de metas.")

    select_mes.wait_for(state="visible", timeout=15000)

    # tenta selecionar pelo texto visível do option
    try:
        select_mes.select_option(label=mes_tela)
    except Exception:
        # fallback: varre opções e tenta encontrar equivalente
        options = select_mes.locator("option").all_text_contents()
        alvo = None
        for op in options:
            if normalizar_texto(op) == normalizar_texto(mes_tela):
                alvo = op.strip()
                break

        if not alvo:
            raise RuntimeError(
                f"Não encontrei o mês '{mes_tela}' no select. Opções disponíveis: {options}"
            )

        select_mes.select_option(label=alvo)

    # clica em Buscar
    botao_buscar = page.get_by_role("button", name="Buscar")
    if botao_buscar.count() == 0:
        botao_buscar = page.locator("text=Buscar").first

    if botao_buscar.count() == 0:
        raise RuntimeError("Não encontrei o botão Buscar na tela de metas.")

    botao_buscar.click()

    # espera estabilizar
    page.wait_for_timeout(3000)

    # pequena confirmação de que o select permaneceu no mês certo
    mes_confirmado = page.evaluate("""() => {
        const select = document.getElementById('mes_ano');
        if (!select) return null;
        const selected = select.options[select.selectedIndex];
        return selected ? (selected.text || selected.value || null) : null;
    }""")
    print(f"✅ Mês selecionado após busca: {mes_confirmado}")


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
        selecionar_mes_e_buscar(page)

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
            "mes_referencia": obter_mes_referencia_json(),
            "indicadores": garantir_indicadores_vazios(),
            "_status": "timeout"
        }
    except Exception as e:
        print(f"Erro em {nome}: {e}")
        return {
            "mes_referencia": obter_mes_referencia_json(),
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
    print(f"Data/Hora: {agora().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Mês de referência (tela): {obter_mes_tela()}")
    print(f"Mês de referência (json): {obter_mes_referencia_json()}")
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
