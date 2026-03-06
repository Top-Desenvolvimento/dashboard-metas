import os
import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime

USERNAME = os.getenv("SYSTEM_LOGIN")
PASSWORD = os.getenv("SYSTEM_PASSWORD")

CSV_HISTORY_PATH = os.path.join("data", "historico_metas.csv")
JSON_CURRENT_PATH = os.path.join("data", "current_metas.json")

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

def extract_city_data(page, cidade_info):
    nome = cidade_info["nome"]
    base_url = cidade_info["url"]

    try:
        page.goto(base_url, timeout=30000)
        page.fill("#usuario", USERNAME)
        page.fill("#senha", PASSWORD)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle", timeout=15000)

        metas_url = base_url.rstrip("/") + "/index2.php?conteudo=lista_metas"
        if base_url.endswith("/sistema/"):
            metas_url = base_url + "index2.php?conteudo=lista_metas"

        page.goto(metas_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)

        data = page.evaluate("""() => {
            const tables = Array.from(document.querySelectorAll('table'));
            return tables.map(table =>
                Array.from(table.querySelectorAll('tr')).map(tr =>
                    Array.from(tr.querySelectorAll('td, th')).map(td => td.innerText.trim())
                )
            );
        }""")

        mes_ano = page.evaluate("""() => {
            const select = document.getElementById('mes_ano');
            if (select) {
                const selected = select.options[select.selectedIndex];
                return selected ? selected.text : 'N/A';
            }
            return 'N/A';
        }""")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = []

        if len(data) > 0:
            t1 = data[0]
            for i in range(0, len(t1), 3):
                if i + 2 < len(t1) and len(t1[i + 2]) >= 5 and len(t1[i]) > 0:
                    rows.append({
                        "Data/Hora": timestamp,
                        "Cidade": nome,
                        "Mês/Ano": mes_ano,
                        "Tipo": "Financeiro",
                        "Nome": t1[i][0],
                        "Meta": t1[i + 2][1],
                        "Realizado": t1[i + 2][2],
                        "Falta": t1[i + 2][3],
                        "Progresso": t1[i + 2][4],
                    })

        if len(data) > 1:
            t2 = data[1]
            for i in range(0, len(t2), 3):
                if i + 2 < len(t2) and len(t2[i + 2]) >= 5 and len(t2[i]) > 0:
                    rows.append({
                        "Data/Hora": timestamp,
                        "Cidade": nome,
                        "Mês/Ano": mes_ano,
                        "Tipo": "Serviços",
                        "Nome": t2[i][0],
                        "Meta": t2[i + 2][1],
                        "Realizado": t2[i + 2][2],
                        "Falta": t2[i + 2][3],
                        "Progresso": t2[i + 2][4],
                    })

        return rows

    except Exception as e:
        print(f"Erro ao extrair dados de {nome}: {e}")
        return []

def main():
    if not USERNAME or not PASSWORD:
        raise ValueError("SYSTEM_LOGIN e SYSTEM_PASSWORD não definidos.")

    os.makedirs("data", exist_ok=True)
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for cidade in CIDADES:
            print(f"Extraindo: {cidade['nome']}")
            rows = extract_city_data(page, cidade)
            all_rows.extend(rows)

        context.close()
        browser.close()

    if not all_rows:
        raise RuntimeError("Nenhum dado foi extraído.")

    df = pd.DataFrame(all_rows)

    df.to_json(JSON_CURRENT_PATH, orient="records", force_ascii=False, indent=2)

    if os.path.exists(CSV_HISTORY_PATH):
        old_df = pd.read_csv(CSV_HISTORY_PATH)
        history_df = pd.concat([old_df, df], ignore_index=True)
    else:
        history_df = df.copy()

    history_df.to_csv(CSV_HISTORY_PATH, index=False)

    print(f"Snapshot salvo em {JSON_CURRENT_PATH}")
    print(f"Histórico salvo em {CSV_HISTORY_PATH}")

if __name__ == "__main__":
    main()
