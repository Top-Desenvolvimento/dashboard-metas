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
HISTORICO_DIR = "data/historico"
GOOGLE_MANUAL_FILE = "data/google_manual.json"

TZ = ZoneInfo("America/Sao_Paulo") if ZoneInfo else None

CIDADES = [
    {"nome": "Flores", "url": "http://flores.topesteticabucal.com.br/sistema"},
    {"nome": "Caxias", "url": "http://caxias.topesteticabucal.com.br/sistema"},
    {"nome": "Farroupilha", "url": "http://farroupilha.topesteticabucal.com.br/sistema"},
    {"nome": "Bento", "url": "http://bento.topesteticabucal.com.br/sistema"},
    {"nome": "Encantado", "url": "https://encantado.topesteticabucal.com.br/sistema"},
    {"nome": "Soledade", "url": "http://soledade.topesteticabucal.com.br/sistema"},
    {"nome": "Veranópolis", "url": "http://veranopolis.topesteticabucal.com.br/sistema"},
]

MAPA_CHAVES = {
    "ortodontia": "ortodontia",
    "orto": "ortodontia",
    "clinico geral": "clinico_geral",
    "clínico geral": "clinico_geral",
    "clinico_geral": "clinico_geral",
    # Avaliação Google — deve vir antes de avaliação genérica
    "avaliacao google": "avaliacoes_google",
    "avaliação google": "avaliacoes_google",
    "meta avaliacao google": "avaliacoes_google",
    "meta avaliação google": "avaliacoes_google",
    # Meta de Avaliação (serviço)
    "avaliação": "meta_avaliacao",
    "avaliacao": "meta_avaliacao",
    "meta de avaliação": "meta_avaliacao",
    "meta de avaliacao": "meta_avaliacao",
    "meta avaliacao": "meta_avaliacao",
    "meta avaliação": "meta_avaliacao",
    # Profilaxia
    "profilaxia": "meta_profilaxia",
    "meta de profilaxia": "meta_profilaxia",
    # Restauração
    "restauração": "meta_restauracao",
    "restauracao": "meta_restauracao",
    "meta de restauração": "meta_restauracao",
    "meta de restauracao": "meta_restauracao",
    # Colagens
    "colagem aparelho convencional": "colagem_convencional",
    "colagem convencional": "colagem_convencional",
    "colagem aparelho estetico/autoligado": "colagem_estetico",
    "colagem aparelho estetico autoligado": "colagem_estetico",
    "colagem estetico/autoligado": "colagem_estetico",
    "colagem estetico autoligado": "colagem_estetico",
    "colagem estetico": "colagem_estetico",
}

INDICADORES_BASE = [
    "ortodontia",
    "clinico_geral",
    "avaliacoes_google",
    "meta_avaliacao",
    "meta_profilaxia",
    "meta_restauracao",
    "colagem_convencional",
    "colagem_estetico",
]

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

MESES_PT_REV = {
    "janeiro": "01", "fevereiro": "02", "marco": "03",
