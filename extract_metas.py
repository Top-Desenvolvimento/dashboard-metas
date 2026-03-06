#!/usr/bin/env python3
"""
Script de extração de metas da Top Estética Bucal.

Objetivos (2026):
- Login automatizado nas 9 unidades
- Extrair metas financeiras e de serviços do mês atual
- Extrair avaliações do Google via links share.google
- Persistir "estado atual" + histórico por mês (para seletor de mês no dashboard)
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import traceback

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


LOGIN_USER = os.environ.get("LOGIN_USER", "MANUS")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "MANUS2026")

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
LOG_PATH = LOG_DIR / "update.log"
DEBUG_DIR = DATA_DIR / "debug"
CURRENT_JSON_PATH = DATA_DIR / "metas_atual.json"
HIST_CSV_PATH = DATA_DIR / "historico_metas.csv"
HIST_DIR = DATA_DIR / "historico"
MESES_DIR = DATA_DIR / "meses"
GOOGLE_BASELINES_PATH = DATA_DIR / "google_baselines.json"
HIST_INDEX_PATH = DATA_DIR / "historico_index.json"


@dataclass(frozen=True)
class Unidade:
    cidade: str
    sistema_url: str
    google_share_url: str


UNIDADES: list[Unidade] = [
    Unidade("Caxias", "http://caxias.topesteticabucal.com.br/sistema", "https://share.google/3f8yPEfrb24AQYYOp"),
    Unidade("Farroupilha", "http://farroupilha.topesteticabucal.com.br/sistema", "https://share.google/ffSPadgdvp8WUEXq0"),
    Unidade("Bento", "http://bento.topesteticabucal.com.br/sistema", "https://share.google/g1snAopsGqM5I8sOl"),
    Unidade("Encantado", "https://encantado.topesteticabucal.com.br/sistema", "https://share.google/sEdZu4jHIPYL77RA6"),
    Unidade("Soledade", "http://soledade.topesteticabucal.com.br/sistema", "https://share.google/5CUABlRksD1cPYWiK"),
    Unidade("Garibaldi", "http://garibaldi.topesteticabucal.com.br/sistema", "https://share.google/rOGEnBONHO2kTYVk3"),
    Unidade("Veranópolis", "http://veranopolis.topesteticabucal.com.br/sistema", "https://share.google/UlnGSp8MES2AnB7Yz"),
    Unidade("SS do Caí", "https://ssdocai.topesteticabucal.com.br/sistema", "https://share.google/33XgmkKW7UnW8o8WB"),
    Unidade("Flores", "https://flores.topesteticabucal.com.br/sistema", "https://share.google/U2cO3MWeXsKQZUenB"),
]

# Fallback (caso não exista baseline mensal cadastrado ainda)
AVALIACOES_INICIAIS_PADRAO: dict[str, int] = {
    "Caxias": 285,
    "Flores": 94,
    "Farroupilha": 173,
    "Bento": 76,
    "Encantado": 206,
    "Soledade": 413,
    "Garibaldi": 128,
    "Veranópolis": 128,
    "SS do Caí": 88,
}

def _now() -> datetime:
    return datetime.now()


def _current_month_key() -> str:
    """
    Mês de referência no formato YYYY-MM.
    - Por padrão: mês atual
    - Se MES_REFERENCIA ou FORCE_MONTH estiver definido (ex.: 2026-02), usa esse.
      Isso permite “fechar” um mês passado (ex.: fevereiro) mesmo já estando em março.
    """
    forced = os.environ.get("MES_REFERENCIA") or os.environ.get("FORCE_MONTH")
    if forced and re.match(r"^\d{4}-\d{2}$", forced.strip()):
        return forced.strip()
    return _now().strftime("%Y-%m")


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    HIST_DIR.mkdir(parents=True, exist_ok=True)
    MESES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def _log(msg: str) -> None:
    line = f"[{_now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def setup_driver() -> webdriver.Chrome:
    """Configura o Chrome em modo headless (robusto para CI e Windows)."""
    chrome_options = Options()
    headless = os.environ.get("HEADLESS", "1").strip().lower() not in ("0", "false", "no")
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1400,900")
    chrome_options.add_argument("--lang=pt-BR")

    try:
        # webdriver-manager evita ficar quebrando por driver desatualizado
        driver_path = ChromeDriverManager().install()
        return webdriver.Chrome(driver_path, options=chrome_options)
    except TypeError:
        # Compatibilidade com algumas versões do selenium que mudaram assinatura
        return webdriver.Chrome(options=chrome_options)

def _find_first(driver: webdriver.Chrome, by_and_selectors: list[tuple[str, str]], timeout_s: int = 10):
    wait = WebDriverWait(driver, timeout_s)
    last_err: Optional[Exception] = None
    for by, selector in by_and_selectors:
        try:
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception as e:
            last_err = e
    raise last_err or TimeoutException("Elemento não encontrado")


def fazer_login(driver: webdriver.Chrome, url: str) -> bool:
    """Faz login no sistema da clínica (tenta múltiplos seletores)."""
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 12)

        username = _find_first(
            driver,
            [
                (By.NAME, "username"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[type='text'][name*='user' i]"),
                (By.CSS_SELECTOR, "input[type='email']"),
            ],
            timeout_s=12,
        )

        password = _find_first(
            driver,
            [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ],
            timeout_s=12,
        )

        username.clear()
        username.send_keys(LOGIN_USER)
        password.clear()
        password.send_keys(LOGIN_PASS)
        password.submit()

        # Confirma que saiu da tela de login (heurística)
        wait.until(lambda d: "login" not in d.current_url.lower())
        time.sleep(1.0)
        return True
    except Exception as e:
        print(f"Erro no login ({url}): {e}")
        return False

def _click_menu(driver: webdriver.Chrome, label: str) -> None:
    """Clica em itens de menu por texto (tenta variações)."""
    xpaths = [
        f"//a[contains(normalize-space(.), '{label}')]",
        f"//button[contains(normalize-space(.), '{label}')]",
        f"//*[self::a or self::button][contains(., '{label}')]",
    ]
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, xp)))
            el.click()
            time.sleep(1.0)
            return
        except Exception:
            continue
    raise TimeoutException(f"Menu '{label}' não encontrado")


def _selecionar_mes_referencia_se_existir(driver: webdriver.Chrome, mes_key: str) -> None:
    """Se existir seletor de mês, seleciona o mês de referência (YYYY-MM)."""
    try:
        mes_num = mes_key.split("-")[1]
    except Exception:
        mes_num = _now().strftime("%m")
    mes_label_pt = dt.strftime("%B").lower()

    # 1) select HTML clássico
    selects = driver.find_elements(By.CSS_SELECTOR, "select")
    for sel in selects:
        try:
            attrs = (sel.get_attribute("id") or "") + " " + (sel.get_attribute("name") or "")
            if "mes" not in attrs.lower() and "month" not in attrs.lower():
                continue
            # tenta setar via JS (mais confiável com frameworks)
            driver.execute_script(
                """
                const sel = arguments[0];
                const candidates = arguments[1];
                const candidatesText = arguments[2];
                const opt = Array.from(sel.options).find(o => candidates.includes(o.value)) ||
                            Array.from(sel.options).find(o => candidatesText.some(t => (o.textContent||'').toLowerCase().includes(t)));
                if (opt) { sel.value = opt.value; sel.dispatchEvent(new Event('change', {bubbles:true})); }
                """,
                sel,
                [mes_num, str(int(mes_num))],
                [mes_label_pt],
            )
            time.sleep(1.0)
            return
        except Exception:
            continue


def _texto_ao_lado(driver: webdriver.Chrome, label: str) -> Optional[str]:
    """Busca um valor associado a um rótulo na página (heurística para tabelas/cards)."""
    xps = [
        # label em célula de tabela -> valor na célula ao lado
        f"//*[self::td or self::th][contains(normalize-space(.), '{label}')]/following-sibling::*[1]",
        # label em div/strong/span -> valor no irmão seguinte
        f"//*[self::div or self::span or self::strong][contains(normalize-space(.), '{label}')]/following-sibling::*[1]",
        # label e valor no mesmo bloco: pega o texto do container
        f"//*[contains(normalize-space(.), '{label}')][1]",
    ]
    for xp in xps:
        try:
            el = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, xp)))
            txt = (el.text or "").strip()
            if txt:
                return txt
        except Exception:
            continue
    return None


def extrair_metas_financeiras(driver: webdriver.Chrome) -> dict[str, str]:
    """Extrai dados de metas financeiras (rótulo -> valor)."""
    try:
        _click_menu(driver, "Metas Financeiras")
    except Exception:
        # alguns sistemas usam só "Metas"
        try:
            _click_menu(driver, "Metas")
        except Exception:
            pass

    _selecionar_mes_referencia_se_existir(driver, _current_month_key())

    orto = _texto_ao_lado(driver, "Ortodontia") or ""
    clin = _texto_ao_lado(driver, "Clínico Geral") or _texto_ao_lado(driver, "Clinico Geral") or ""

    return {"ortodontia": orto, "clinico_geral": clin}

def extrair_metas_servicos(driver: webdriver.Chrome) -> dict[str, str]:
    """Extrai dados de metas de serviços."""
    try:
        _click_menu(driver, "Metas de Serviços")
    except Exception:
        try:
            _click_menu(driver, "Metas Serviços")
        except Exception:
            pass

    _selecionar_mes_referencia_se_existir(driver, _current_month_key())

    prof = _texto_ao_lado(driver, "Profilaxia") or ""
    rest = _texto_ao_lado(driver, "Restauração") or _texto_ao_lado(driver, "Restauracao") or ""

    return {"profilaxia": prof, "restauracao": rest}

def _parse_int(text: str) -> Optional[int]:
    m = re.search(r"(\d{1,3}(?:[\.\s]\d{3})*|\d+)", text)
    if not m:
        return None
    raw = m.group(1).replace(".", "").replace(" ", "")
    try:
        return int(raw)
    except Exception:
        return None


def obter_avaliacoes_google(url: str) -> Optional[int]:
    """Obtém número de avaliações via scraping do share.google (sem API paga)."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text

        # 1) tenta padrões JSON comuns
        for pat in [r'"reviewCount"\s*:\s*(\d+)', r'"ratingCount"\s*:\s*(\d+)']:
            m = re.search(pat, html)
            if m:
                return int(m.group(1))

        soup = BeautifulSoup(html, "html.parser")

        # 2) tenta meta tags
        for meta_key in ["ratingCount", "reviewCount"]:
            meta = soup.find("meta", attrs={"itemprop": meta_key})
            if meta and meta.get("content"):
                val = _parse_int(str(meta.get("content")))
                if val is not None:
                    return val

        # 3) fallback: procura texto "avaliações" / "reviews"
        text = soup.get_text(" ", strip=True).lower()
        for kw in ["avaliações", "avaliacoes", "reviews"]:
            idx = text.find(kw)
            if idx != -1:
                window = text[max(0, idx - 40) : idx + 40]
                val = _parse_int(window)
                if val is not None:
                    return val

        return None
    except Exception as e:
        print(f"Erro ao obter avaliações do Google ({url}): {e}")
        return None

def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_google_baseline(mes: str, cidade: str) -> Optional[int]:
    baselines = _load_json(GOOGLE_BASELINES_PATH) or {}
    if isinstance(baselines, dict):
        month_map = baselines.get(mes) or {}
        if isinstance(month_map, dict) and cidade in month_map:
            try:
                return int(month_map[cidade])
            except Exception:
                return None
    return None


def _ensure_google_baseline(mes: str, cidade: str, value: int) -> None:
    baselines = _load_json(GOOGLE_BASELINES_PATH) or {}
    if not isinstance(baselines, dict):
        baselines = {}
    if mes not in baselines or not isinstance(baselines.get(mes), dict):
        baselines[mes] = {}
    if cidade not in baselines[mes]:
        baselines[mes][cidade] = int(value)
        _save_json(GOOGLE_BASELINES_PATH, baselines)


def coletar_dados_todas_cidades() -> dict[str, Any]:
    """Coleta dados de todas as 9 cidades."""
    _ensure_dirs()
    driver = setup_driver()
    dados: dict[str, Any] = {}
    dt = _now()
    mes = _current_month_key()

    try:
        for unidade in UNIDADES:
            cidade = unidade.cidade
            _log(f"Coletando dados de {cidade}...")

            ok = False
            last_err: Optional[Exception] = None
            for attempt in range(1, 4):
                try:
                    if not fazer_login(driver, unidade.sistema_url):
                        raise RuntimeError("Falha no login")

                    metas_financeiras = extrair_metas_financeiras(driver)
                    metas_servicos = extrair_metas_servicos(driver)

                    aval_atual = obter_avaliacoes_google(unidade.google_share_url)
                    aval_atual_int = int(aval_atual) if aval_atual is not None else 0

                    baseline = _get_google_baseline(mes, cidade)
                    if baseline is None:
                        baseline = AVALIACOES_INICIAIS_PADRAO.get(cidade, aval_atual_int)
                        _ensure_google_baseline(mes, cidade, baseline)

                    dados[cidade] = {
                        "metas_financeiras": metas_financeiras,
                        "metas_servicos": metas_servicos,
                        "avaliacoes": {
                            "inicial": int(baseline),
                            "atual": int(aval_atual_int),
                            "novas": int(aval_atual_int) - int(baseline),
                            "mes": mes,
                        },
                        "timestamp": dt.isoformat(timespec="seconds"),
                        "fonte_google": unidade.google_share_url,
                    }
                    ok = True
                    break
                except Exception as e:
                    last_err = e
                    _log(f"Erro em {cidade} (tentativa {attempt}/3): {e}")
                    try:
                        stamp = _now().strftime("%Y-%m-%d_%H%M%S")
                        driver.save_screenshot(str(DEBUG_DIR / f"{cidade}_{stamp}.png"))
                        (DEBUG_DIR / f"{cidade}_{stamp}.html").write_text(driver.page_source, encoding="utf-8")
                    except Exception:
                        pass
                    time.sleep(1.5)

            if not ok:
                _log(f"Falha definitiva ao coletar {cidade}: {last_err}")
                try:
                    (DEBUG_DIR / f"{cidade}_trace.txt").write_text(traceback.format_exc(), encoding="utf-8")
                except Exception:
                    pass
                continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return dados

def salvar_json(dados: dict[str, Any]) -> None:
    """Salva dados do estado atual em JSON."""
    _ensure_dirs()
    _save_json(CURRENT_JSON_PATH, dados)
    print(f"JSON salvo em: {CURRENT_JSON_PATH}")

def salvar_csv(dados: dict[str, Any]) -> None:
    """Salva histórico em CSV (append)."""
    _ensure_dirs()
    rows: list[dict[str, Any]] = []
    for cidade, info in dados.items():
        rows.append(
            {
                "cidade": cidade,
                "timestamp": info.get("timestamp", ""),
                "mes": info.get("avaliacoes", {}).get("mes", ""),
                "ortodontia": info.get("metas_financeiras", {}).get("ortodontia", ""),
                "clinico_geral": info.get("metas_financeiras", {}).get("clinico_geral", ""),
                "profilaxia": info.get("metas_servicos", {}).get("profilaxia", ""),
                "restauracao": info.get("metas_servicos", {}).get("restauracao", ""),
                "avaliacoes_inicial": info.get("avaliacoes", {}).get("inicial", ""),
                "avaliacoes_atual": info.get("avaliacoes", {}).get("atual", ""),
                "avaliacoes_novas": info.get("avaliacoes", {}).get("novas", ""),
            }
        )

    df = pd.DataFrame(rows)
    if HIST_CSV_PATH.exists():
        df.to_csv(HIST_CSV_PATH, mode="a", header=False, index=False)
    else:
        df.to_csv(HIST_CSV_PATH, index=False)
    print(f"CSV atualizado em: {HIST_CSV_PATH}")

def gerar_excel(dados: dict[str, Any]) -> None:
    """Gera planilha Excel formatada."""
    _ensure_dirs()
    output_path = DATA_DIR / "metas_top_estetica.xlsx"

    df_financeiro: list[dict[str, Any]] = []
    df_servicos: list[dict[str, Any]] = []
    df_avaliacoes: list[dict[str, Any]] = []

    for cidade, info in dados.items():
        df_financeiro.append(
            {
                "Cidade": cidade,
                "Ortodontia": info.get("metas_financeiras", {}).get("ortodontia", ""),
                "Clínico Geral": info.get("metas_financeiras", {}).get("clinico_geral", ""),
            }
        )
        df_servicos.append(
            {
                "Cidade": cidade,
                "Profilaxia": info.get("metas_servicos", {}).get("profilaxia", ""),
                "Restauração": info.get("metas_servicos", {}).get("restauracao", ""),
            }
        )
        df_avaliacoes.append(
            {
                "Cidade": cidade,
                "Avaliações Iniciais": info.get("avaliacoes", {}).get("inicial", ""),
                "Avaliações Atuais": info.get("avaliacoes", {}).get("atual", ""),
                "Novas Avaliações": info.get("avaliacoes", {}).get("novas", ""),
            }
        )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(df_financeiro).to_excel(writer, sheet_name="Metas Financeiras", index=False)
        pd.DataFrame(df_servicos).to_excel(writer, sheet_name="Metas Serviços", index=False)
        pd.DataFrame(df_avaliacoes).to_excel(writer, sheet_name="Avaliações Google", index=False)

    print(f"Excel gerado em: {output_path}")


def salvar_historico_por_mes(dados: dict[str, Any]) -> None:
    """Salva snapshot JSON em pasta por mês e atualiza arquivo do mês + índice."""
    _ensure_dirs()
    dt = _now()
    mes = _mes_key(dt)
    stamp = dt.strftime("%Y-%m-%d_%H%M%S")

    month_dir = HIST_DIR / mes
    month_dir.mkdir(parents=True, exist_ok=True)
    snap_path = month_dir / f"metas_{stamp}.json"
    _save_json(snap_path, dados)

    # "estado do mês" (última coleta) para o seletor de mês no dashboard
    month_current_path = MESES_DIR / f"{mes}.json"
    _save_json(month_current_path, {"mes": mes, "atualizado_em": dt.isoformat(timespec="seconds"), "dados": dados})

    # índice
    idx = _load_json(HIST_INDEX_PATH) or {}
    if not isinstance(idx, dict):
        idx = {}
    if "meses" not in idx or not isinstance(idx.get("meses"), list):
        idx["meses"] = []
    if mes not in idx["meses"]:
        idx["meses"].append(mes)
        idx["meses"] = sorted(idx["meses"])
    idx["ultimo_update"] = dt.isoformat(timespec="seconds")
    _save_json(HIST_INDEX_PATH, idx)

def main() -> None:
    print("=" * 60)
    print("Iniciando coleta de dados - Top Estética Bucal")
    print(f"Data/Hora: {_now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)

    try:
        dados = coletar_dados_todas_cidades()
    except (WebDriverException, TimeoutException) as e:
        print(f"Falha crítica do navegador: {e}")
        raise

    if not dados:
        print("\n✗ Nenhum dado foi coletado!")
        raise SystemExit(1)

    salvar_json(dados)
    salvar_historico_por_mes(dados)
    salvar_csv(dados)
    gerar_excel(dados)

    print("\n✓ Coleta concluída com sucesso!")
    print(f"Total de cidades processadas: {len(dados)}")

if __name__ == '__main__':
    main()
