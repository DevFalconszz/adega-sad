"""Sistema visual, estado compartilhado e utilitários do SAD.

A interface foi desenhada para ser silenciosa: tipografia editorial, hairlines,
muito respiro e apenas dois acentos de marca — verde-garrafa e vinho.
"""
from __future__ import annotations

import copy
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sad.config import carregar_config, config_para_yaml
from sad.data import carregar_base
from sad.features import montar_dataset, reclassificar
from sad.optimizer import otimizar

# ------------------------------------------------------------------ tokens
INK = "#1D241F"
MUTED = "#70766D"
FAINT = "#9A9E96"
CREAM = "#F7F5F0"
CARD = "#FFFDF8"
LINE = "#E5E1D7"
GREEN = "#0E5A3A"
GREEN_2 = "#2F7D5B"
GREEN_SOFT = "#E7EFE7"
WINE = "#8F2437"
WINE_SOFT = "#F6E8EA"
OCHRE = "#A96A1E"
OCHRE_SOFT = "#F6EEDF"
SLATE = "#6B7A6F"
SAGE = "#B9C9B7"

# aliases usados pelas páginas
VERDE = GREEN
VERDE_ESCURO = GREEN
VERDE_CLARO = GREEN_2
VERMELHO = WINE
AMBAR = OCHRE
AZUL = SLATE
ROXO = "#5C4B51"
CIANO = "#4F7A78"
CINZA = SLATE
TEXTO = INK
MUTED_COR = MUTED

CAT = [GREEN, WINE, OCHRE, SLATE, SAGE, "#5C4B51", "#4F7A78"]
FONT = "Inter, system-ui, -apple-system, sans-serif"


# ------------------------------------------------------------------ números
def brl(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def brl_curto(v: float) -> str:
    """Valor compacto para espaços estreitos: R$ 1,15 mi."""
    sinal = "-" if v < 0 else ""
    v = abs(float(v))
    if v >= 1_000_000:
        return f"{sinal}R$ {v / 1_000_000:.2f} mi".replace(".", ",")
    if v >= 1_000:
        return f"{sinal}R$ {v / 1_000:.0f} mil"
    return f"{sinal}R$ {v:.0f}"


def pct(v: float, casas: int = 1, sinal: bool = False) -> str:
    if v is None or pd.isna(v):
        return "—"
    s = f"{v:+.{casas}f}%" if sinal else f"{v:.{casas}f}%"
    return s.replace(".", ",")


def num(v: float, casas: int = 0) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def delta_txt(v: float, formato=brl, casas: int = 1) -> str:
    sinal = "+" if v >= 0 else "−"
    valor = formato(abs(v)) if formato is brl else f"{abs(v):.{casas}f}".replace(".", ",")
    return f"{sinal}{valor}"


MESES_CURTOS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def mes_ano(dt) -> str:
    """Mês abreviado em português, independente do locale do processo."""
    return f"{MESES_CURTOS[dt.month - 1]}/{dt.year}"


def mes_curto(dt) -> str:
    return f"{MESES_CURTOS[dt.month - 1]}/{dt.year % 100:02d}"


def eixo_meses(datas, alvo: int = 7) -> tuple[list, list]:
    """Poucos rótulos legíveis em português para uma série mensal."""
    datas = list(datas)
    passo = max(1, len(datas) // alvo)
    marcas = datas[::passo]
    return marcas, [mes_curto(d) for d in marcas]


# ------------------------------------------------------------------ dados
@st.cache_data(show_spinner=False)
def _dataset_base() -> pd.DataFrame:
    return montar_dataset(carregar_base())


@st.cache_data(show_spinner=False)
def carregar_dfs() -> dict:
    return carregar_base()


def get_cfg() -> dict:
    if "cfg" not in st.session_state:
        st.session_state["cfg"] = carregar_config()
    return st.session_state["cfg"]


def set_cfg(cfg: dict) -> None:
    st.session_state["cfg"] = copy.deepcopy(cfg)


def reset_cfg() -> None:
    set_cfg(carregar_config())


def get_df() -> pd.DataFrame:
    """Dataset integrado, com faixas de margem conforme a configuração ativa."""
    cfg = get_cfg()
    f = cfg["faixas_margem"]
    return reclassificar(_dataset_base(), f["baixa_ate"], f["alta_acima"])


@st.cache_data(show_spinner=False)
def _otimizar_cache(cfg_yaml: str, baixa_ate: float, alta_acima: float):
    import yaml

    cfg = yaml.safe_load(cfg_yaml)
    df = reclassificar(_dataset_base(), baixa_ate, alta_acima)
    return otimizar(df, cfg)


def get_recomendacao() -> dict:
    cfg = get_cfg()
    f = cfg["faixas_margem"]
    return _otimizar_cache(config_para_yaml(cfg), f["baixa_ate"], f["alta_acima"])


def get_cfg_yaml(cfg: dict | None = None) -> str:
    return config_para_yaml(cfg or get_cfg())


# ------------------------------------------------------------------ estilo
def inject_css() -> None:
    st.html(
        """
<style>
:root {
    --bg: #F7F5F0;
    --card: #FFFDF8;
    --ink: #1D241F;
    --muted: #70766D;
    --faint: #9A9E96;
    --line: #E5E1D7;
    --line-soft: #EEEAE0;
    --green: #0E5A3A;
    --green-2: #2F7D5B;
    --green-soft: #E7EFE7;
    --wine: #8F2437;
    --wine-soft: #F6E8EA;
    --ochre: #A96A1E;
    --ochre-soft: #F6EEDF;
    --serif: Georgia, 'Times New Roman', serif;
    --sans: Inter, system-ui, -apple-system, sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--ink);
    font-family: var(--sans);
    -webkit-font-smoothing: antialiased;
}

[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"] {
    background: var(--bg);
}

[data-testid="stMainBlockContainer"], .block-container {
    max-width: 1240px;
    padding: 2.6rem 2.2rem 7rem;
    margin: 0 auto;
}

/* ---------------- header + navegação ---------------- */
[data-testid="stHeader"] {
    background: rgba(247, 245, 240, 0.92) !important;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--line);
    height: 64px;
}
[data-testid="stToolbar"] { background: transparent; }
[data-testid="stAppDeployButton"], #MainMenu, [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeaderLogo"] {
    width: 144px;
    height: 32px;
    margin-left: 2px;
}
[data-testid="stTopNav"] {
    margin-left: auto;
    margin-right: 1.1rem;
    gap: 2px;
}
[data-testid="stTopNavLink"] {
    border-radius: 999px;
    padding: 0.38rem 0.72rem;
    transition: background 140ms ease, color 140ms ease;
}
[data-testid="stTopNavLink"] p {
    font-family: var(--sans);
    font-size: 0.79rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.005em;
    color: var(--muted) !important;
}
[data-testid="stTopNavLink"]:hover { background: #EFECE3; }
[data-testid="stTopNavLink"]:hover p { color: var(--ink) !important; }
[data-testid="stTopNavLink"][aria-current="page"] { background: #ECE8DE; }
[data-testid="stTopNavLink"][aria-current="page"] p { color: var(--ink) !important; font-weight: 600 !important; }

/* ---------------- tipografia ---------------- */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--sans) !important;
    color: var(--ink) !important;
    letter-spacing: -0.025em;
}
p, li, span, label, div { font-family: var(--sans); }
[data-testid="stMarkdownContainer"] p { line-height: 1.65; }
a { color: var(--green); text-decoration: none; }
::selection { background: #D7E5D7; color: var(--ink); }

/* ---------------- cabeçalho de página ---------------- */
.page-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 2rem;
    padding: 0.4rem 0 1.5rem;
    margin-bottom: 2.1rem;
    border-bottom: 1px solid var(--line);
}
.page-kicker {
    color: var(--green);
    font-size: 0.66rem;
    font-weight: 650;
    letter-spacing: 0.17em;
    text-transform: uppercase;
    margin-bottom: 0.85rem;
}
.page-head h1 {
    font-family: var(--serif) !important;
    font-size: clamp(2.15rem, 4vw, 3rem) !important;
    line-height: 1.04;
    font-weight: 400 !important;
    letter-spacing: -0.035em !important;
    margin: 0;
    color: var(--ink) !important;
}
.page-head .page-sub {
    color: var(--muted);
    font-size: 0.94rem;
    line-height: 1.6;
    max-width: 610px;
    margin: 0.8rem 0 0;
}
.page-meta {
    display: flex;
    gap: 2rem;
    padding-bottom: 0.2rem;
    flex-shrink: 0;
}
.page-meta .meta-label {
    color: var(--faint);
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.22rem;
}
.page-meta .meta-value {
    color: var(--ink);
    font-size: 0.8rem;
    font-weight: 500;
    white-space: nowrap;
}

/* ---------------- seções ---------------- */
.section-head {
    display: flex;
    align-items: flex-end;
    gap: 1.1rem;
    margin: 2.5rem 0 1.05rem;
}
.section-head h2 {
    font-size: 0.92rem !important;
    font-weight: 650 !important;
    letter-spacing: -0.01em !important;
    margin: 0;
    white-space: nowrap;
}
.section-head p {
    color: var(--faint);
    font-size: 0.76rem;
    margin: 0.16rem 0 0;
    line-height: 1.4;
}
.section-line {
    flex: 1;
    height: 1px;
    background: var(--line);
    margin-bottom: 0.28rem;
}

/* ---------------- cards de indicador ---------------- */
.metric-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1.05rem 1.15rem 1rem;
    height: 100%;
    min-height: 118px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.metric-top { display: flex; align-items: center; justify-content: space-between; gap: .6rem; }
.metric-label {
    color: var(--muted);
    font-size: 0.64rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.metric-dot { width: 6px; height: 6px; border-radius: 999px; background: var(--line); flex-shrink: 0; }
.metric-dot.positive { background: var(--green-2); }
.metric-dot.negative { background: var(--wine); }
.metric-dot.warning { background: var(--ochre); }
.metric-value {
    color: var(--ink);
    font-size: clamp(1.45rem, 2.2vw, 1.82rem);
    font-weight: 500;
    letter-spacing: -0.04em;
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
    margin: 0.55rem 0 0.35rem;
}
.metric-value.positive { color: var(--green); }
.metric-value.negative { color: var(--wine); }
.metric-value.warning { color: var(--ochre); }
.metric-note { color: var(--faint); font-size: 0.72rem; line-height: 1.35; }
.metric-note b, .metric-note strong { color: var(--muted); font-weight: 600; }
.text-positive { color: var(--green); font-weight: 600; }
.text-negative { color: var(--wine); font-weight: 600; }
.text-warning { color: var(--ochre); font-weight: 600; }

/* ---------------- faixa de estatísticas ---------------- */
.stat-strip {
    display: flex;
    align-items: stretch;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
}
.stat-cell { flex: 1; padding: 1rem 1.2rem; border-right: 1px solid var(--line-soft); }
.stat-cell:last-child { border-right: 0; }
.stat-label { color: var(--faint); font-size: 0.63rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; }
.stat-value { color: var(--ink); font-size: 1.18rem; font-weight: 550; letter-spacing: -0.025em; margin-top: 0.32rem; font-variant-numeric: tabular-nums; }
.stat-note { color: var(--faint); font-size: 0.66rem; margin-top: 0.15rem; }

/* ---------------- leitura / destaque ---------------- */
.insight {
    background: #EFECE3;
    border-radius: 14px;
    padding: 1.15rem 1.3rem;
    margin: 1.1rem 0 0.25rem;
}
.insight.positive { background: var(--green-soft); }
.insight.negative { background: var(--wine-soft); }
.insight.warning { background: var(--ochre-soft); }
.insight-title {
    color: var(--green);
    font-size: 0.61rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.48rem;
}
.insight.negative .insight-title { color: var(--wine); }
.insight.warning .insight-title { color: var(--ochre); }
.insight p { color: var(--ink); font-size: 0.875rem; line-height: 1.65; margin: 0; }
.insight p strong { font-weight: 650; }

/* ---------------- títulos dentro de cards ---------------- */
.card-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; margin-bottom: 0.15rem; }
.card-title { color: var(--ink); font-size: 0.82rem; font-weight: 600; letter-spacing: -0.005em; }
.card-caption { color: var(--faint); font-size: 0.68rem; }

/* ---------------- containers nativos ---------------- */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 14px !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line) !important;
    background: var(--card) !important;
    border-radius: 14px !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent !important;
}

/* ---------------- abas ---------------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    border-bottom: 1px solid var(--line);
    background: transparent;
    margin-bottom: 0.4rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    padding: 0.6rem 0 0.75rem !important;
    color: var(--muted);
    font-size: 0.8rem;
    font-weight: 500;
    border: none !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--ink); }
.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    font-weight: 600 !important;
    box-shadow: inset 0 -2px 0 var(--green);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.1rem; }

/* ---------------- botões ---------------- */
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button {
    border-radius: 999px !important;
    font-family: var(--sans) !important;
    font-size: 0.79rem !important;
    font-weight: 550 !important;
    padding: 0.52rem 1.15rem !important;
    min-height: 2.35rem;
    transition: all 140ms ease !important;
    box-shadow: none !important;
}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: var(--green) !important;
    border: 1px solid var(--green) !important;
    color: #F7F5F0 !important;
}
.stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    background: #0B4A30 !important;
    border-color: #0B4A30 !important;
}
.stButton button[kind="secondary"], .stDownloadButton button {
    background: transparent !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
}
.stButton button[kind="secondary"]:hover, .stDownloadButton button:hover {
    background: #EFECE3 !important;
    border-color: #D9D4C8 !important;
}

/* ---------------- widgets ---------------- */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
    border-radius: 9px !important;
    background: var(--card) !important;
    border-color: var(--line) !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {
    border-color: var(--green) !important;
    box-shadow: 0 0 0 1px var(--green) !important;
}
[data-testid="stWidgetLabel"] p {
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    font-weight: 550 !important;
}
[data-testid="stSlider"] { padding-top: 0.15rem; }
[data-testid="stSlider"] [role="slider"] {
    width: 15px !important;
    height: 15px !important;
    border: 2px solid var(--card) !important;
    box-shadow: 0 0 0 1px var(--green) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div { background: var(--green) !important; }

/* ---------------- expanders ---------------- */
[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    background: var(--card) !important;
    overflow: hidden;
    margin-bottom: 0.55rem;
}
[data-testid="stExpander"] summary {
    padding: 0.78rem 1rem !important;
    font-size: 0.8rem !important;
    font-weight: 550 !important;
    color: var(--ink) !important;
}
[data-testid="stExpander"] summary:hover { background: #F4F1E9; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { padding: 0 1rem 0.9rem; }

/* ---------------- tabelas ---------------- */
[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    font-size: 0.67rem !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted) !important;
}

/* ---------------- alertas ---------------- */
[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--card);
    color: var(--ink);
    font-size: 0.8rem;
}

/* ---------------- código ---------------- */
pre, code, .stCode { border-radius: 10px !important; font-family: ui-monospace, SFMono-Regular, Menlo, monospace !important; }
[data-testid="stCode"] { border: 1px solid var(--line); }

/* ---------------- gráficos ---------------- */
[data-testid="stPlotlyChart"] { margin: 0.1rem 0 0; }
.js-plotly-plot .plotly .modebar { display: none !important; }

/* ---------------- regras ---------------- */
.rule-hero { display: flex; align-items: flex-start; justify-content: space-between; gap: 1.5rem; }
.rule-id { color: var(--green); font-size: 0.63rem; font-weight: 700; letter-spacing: 0.14em; margin-bottom: 0.3rem; }
.rule-name { color: var(--ink); font-size: 0.88rem; font-weight: 600; line-height: 1.35; }
.rule-condition { margin-top: 0.75rem; color: var(--muted); font-size: 0.75rem; }
.rule-condition code {
    background: #F3F0E8; color: var(--ink); padding: 0.14rem 0.4rem;
    border-radius: 5px; font-size: 0.72rem;
}
.rule-teto { text-align: right; flex-shrink: 0; }
.rule-teto-value {
    color: var(--ink); font-size: 2rem; font-weight: 450; letter-spacing: -0.05em;
    line-height: 1; font-variant-numeric: tabular-nums;
}
.rule-teto-label { color: var(--faint); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.28rem; }
.rule-flags { margin-top: 0.7rem; display: flex; gap: 0.4rem; flex-wrap: wrap; }
.formula {
    background: #F3F0E8; border-radius: 10px; padding: 0.8rem 1rem;
    color: var(--ink); font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.72rem; line-height: 1.7; overflow-x: auto;
}
.micro-label { color: var(--faint); font-size: 0.61rem; font-weight: 650; letter-spacing: 0.11em; text-transform: uppercase; }

/* ---------------- melhor política ---------------- */
.policy-hero {
    background: radial-gradient(125% 165% at 100% 0%, #1B6C4D 0%, #0E5A3A 55%, #0A4530 100%);
    border-radius: 16px;
    padding: 1.5rem 1.7rem 1.25rem;
    display: grid;
    grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
    gap: 1.4rem 2.2rem;
    color: #F7F5F0;
    margin: 0 0 0.9rem;
}
.policy-kicker {
    color: rgba(247, 245, 240, 0.66);
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}
.policy-value {
    font-family: var(--serif);
    font-size: clamp(2.3rem, 4vw, 3rem);
    line-height: 1;
    letter-spacing: -0.035em;
    color: #FFFDF8;
}
.policy-delta {
    color: rgba(247, 245, 240, 0.84);
    font-size: 0.8rem;
    margin-top: 0.55rem;
    line-height: 1.55;
    max-width: 400px;
}
.policy-delta strong { color: #FFFDF8; font-weight: 650; }
.policy-facts {
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    gap: 1.5rem;
}
.policy-fact { border-left: 1px solid rgba(247, 245, 240, 0.18); padding-left: 1rem; }
.policy-fact-label {
    color: rgba(247, 245, 240, 0.58);
    font-size: 0.58rem;
    font-weight: 650;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    margin-bottom: 0.32rem;
}
.policy-fact-value {
    color: #FFFDF8;
    font-size: 1.02rem;
    font-weight: 500;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.policy-note {
    grid-column: 1 / -1;
    border-top: 1px solid rgba(247, 245, 240, 0.14);
    padding-top: 0.8rem;
    font-size: 0.72rem;
    color: rgba(247, 245, 240, 0.64);
    line-height: 1.55;
}
.policy-note b { color: rgba(247, 245, 240, 0.92); font-weight: 600; }

/* ---------------- passos ---------------- */
.step-grid { display: flex; gap: 2rem; }
.step { flex: 1; }
.step-num { color: var(--green); font-size: 0.61rem; font-weight: 700; letter-spacing: 0.16em; margin-bottom: 0.5rem; }
.step-title { color: var(--ink); font-size: 0.8rem; font-weight: 600; margin-bottom: 0.25rem; }
.step-text { color: var(--muted); font-size: 0.73rem; line-height: 1.55; }

/* ---------------- misc ---------------- */
hr, [data-testid="stDivider"] { border-color: var(--line) !important; }
[data-testid="stSpinner"] { color: var(--green); }
[data-testid="stCaptionContainer"] p { color: var(--faint); font-size: 0.72rem; }
img { max-width: 100%; }
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #D6D1C6; border-radius: 999px; border: 2px solid var(--bg); }
::-webkit-scrollbar-thumb:hover { background: #C4BEB0; }

/* ---------------- responsivo ---------------- */
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"], .block-container { padding: 1.7rem 1.15rem 5rem; }
    .page-head { flex-direction: column; align-items: flex-start; gap: 1.2rem; }
    .page-meta { gap: 1.4rem; }
    .stat-strip { flex-wrap: wrap; }
    .stat-cell { flex: 1 1 50%; border-bottom: 1px solid var(--line-soft); }
    .policy-hero { grid-template-columns: 1fr; }
    .policy-facts { justify-content: flex-start; flex-wrap: wrap; gap: 1rem 1.4rem; }
    [data-testid="stHeaderLogo"] { width: 118px; }
    [data-testid="stTopNav"] { margin-right: 0.2rem; }
}
</style>
"""
    )


# ------------------------------------------------------------------ componentes
def page_header(
    kicker: str,
    title: str,
    subtitle: str,
    meta: list[tuple[str, str]] | None = None,
) -> None:
    meta_html = ""
    if meta:
        meta_html = (
            "<div class='page-meta'>"
            + "".join(
                f"<div><div class='meta-label'>{escape(str(k))}</div>"
                f"<div class='meta-value'>{escape(str(v))}</div></div>"
                for k, v in meta
            )
            + "</div>"
        )
    st.html(
        f"""
        <div class="page-head">
            <div>
                <div class="page-kicker">{escape(kicker)}</div>
                <h1>{escape(title)}</h1>
                <p class="page-sub">{escape(subtitle)}</p>
            </div>
            {meta_html}
        </div>
        """
    )


def section(title: str, caption: str = "") -> None:
    cap = f"<p>{escape(caption)}</p>" if caption else ""
    st.html(
        f"""
        <div class="section-head">
            <div><h2>{escape(title)}</h2>{cap}</div>
            <div class="section-line"></div>
        </div>
        """
    )


def metric_card(
    label: str,
    value: str,
    note: str = "",
    tone: str = "neutral",
    delta: str | None = None,
) -> str:
    """HTML de um card de indicador. `tone`: neutral | positive | negative | warning."""
    dot = "" if tone == "neutral" else f" {tone}"
    value_cls = "" if tone == "neutral" else f" {tone}"
    if delta:
        note = f"<span class='text-{tone}'>{delta}</span> · {note}" if tone != "neutral" else f"{delta} · {note}"
    note_html = f"<div class='metric-note'>{note}</div>" if note else "<div class='metric-note'>&nbsp;</div>"
    return f"""
    <div class="metric-card">
        <div class="metric-top">
            <span class="metric-label">{label}</span>
            <span class="metric-dot{dot}"></span>
        </div>
        <div class="metric-value{value_cls}">{value}</div>
        {note_html}
    </div>
    """


def metric(label: str, value: str, note: str = "", tone: str = "neutral", delta: str | None = None) -> None:
    st.html(metric_card(label, value, note, tone, delta))


def stat_strip(items: list[tuple[str, str, str]]) -> None:
    html = "".join(
        f"<div class='stat-cell'><div class='stat-label'>{lbl}</div>"
        f"<div class='stat-value'>{val}</div><div class='stat-note'>{note}</div></div>"
        for lbl, val, note in items
    )
    st.html(f"<div class='stat-strip'>{html}</div>")


def insight(title: str, body: str, tone: str = "neutral") -> None:
    cls = "" if tone == "neutral" else f" {tone}"
    st.html(
        f"""
        <div class="insight{cls}">
            <div class="insight-title">{escape(title)}</div>
            <p>{body}</p>
        </div>
        """
    )


def policy_hero(
    value: str,
    delta_html: str,
    facts: list[tuple[str, str]],
    note_html: str,
    title: str = "A melhor política",
) -> None:
    """Faixa de destaque com a recomendação do otimizador: o ponto do sistema."""
    facts_html = "".join(
        f"<div class='policy-fact'><div class='policy-fact-label'>{lbl}</div>"
        f"<div class='policy-fact-value'>{val}</div></div>"
        for lbl, val in facts
    )
    st.html(
        f"""
        <div class="policy-hero">
            <div>
                <div class="policy-kicker">{title}</div>
                <div class="policy-value">{value}</div>
                <div class="policy-delta">{delta_html}</div>
            </div>
            <div class="policy-facts">{facts_html}</div>
            <div class="policy-note">{note_html}</div>
        </div>
        """
    )


def card_head(title: str, caption: str = "") -> None:
    cap = f"<span class='card-caption'>{escape(caption)}</span>" if caption else ""
    st.html(f"<div class='card-head'><span class='card-title'>{escape(title)}</span>{cap}</div>")


def chip(text: str, tone: str = "neutral") -> str:
    palette = {
        "positive": (GREEN, GREEN_SOFT),
        "negative": (WINE, WINE_SOFT),
        "warning": (OCHRE, OCHRE_SOFT),
        "neutral": (MUTED, "#F1EEE6"),
    }
    fg, bg = palette.get(tone, palette["neutral"])
    return (
        f"<span style='display:inline-block;background:{bg};color:{fg};border-radius:999px;"
        f"padding:.16rem .55rem;font-size:.64rem;font-weight:600;letter-spacing:.04em;"
        f"white-space:nowrap'>{text}</span>"
    )


def empty_state(title: str, body: str) -> None:
    st.html(
        f"""
        <div style="border:1px dashed #D8D2C4;border-radius:14px;padding:2.4rem 1.6rem;
                    text-align:center;background:rgba(255,253,248,.45)">
            <div style="font-size:.88rem;font-weight:600;color:{INK};margin-bottom:.4rem">{escape(title)}</div>
            <div style="font-size:.76rem;color:{MUTED};line-height:1.6;max-width:430px;margin:0 auto">{body}</div>
        </div>
        """
    )


# ------------------------------------------------------------------ plotly
def style_fig(
    fig: go.Figure,
    height: int = 330,
    *,
    legend: bool = False,
    margin: dict | None = None,
    y_title: str | None = None,
    x_title: str | None = None,
) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margin or dict(l=6, r=10, t=14, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=11.5, color=MUTED),
        colorway=CAT,
        hoverlabel=dict(
            bgcolor=INK,
            bordercolor=INK,
            font=dict(color="#F7F5F0", family=FONT, size=11.5),
        ),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10.5, color=MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        bargap=0.45,
        bargroupgap=0.12,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
        automargin=True,
        tickfont=dict(size=10.5, color=MUTED),
        title=dict(text=x_title, font=dict(size=10.5, color=FAINT)) if x_title else None,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#ECE9E0",
        gridwidth=1,
        zeroline=False,
        showline=False,
        ticks="",
        automargin=True,
        tickfont=dict(size=10.5, color=MUTED),
        title=dict(text=y_title, font=dict(size=10.5, color=FAINT)) if y_title else None,
    )
    return fig


def show_fig(fig: go.Figure, height: int = 330, **kwargs) -> None:
    style_fig(fig, height=height, **kwargs)
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False, "responsive": True},
    )
