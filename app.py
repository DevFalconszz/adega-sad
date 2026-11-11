"""SAD de Política de Descontos · Adega Bom Sabor.

Sistema de Apoio à Decisão — POC acadêmica (UEG / Trindade).
Execução:  streamlit run app.py
"""
import streamlit as st

from ui import inject_css

# ------------------------------------------------------------------ página
st.set_page_config(
    page_title="Adega Bom Sabor · Política de Descontos",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "SAD de Política de Descontos — Adega Bom Sabor. "
        "Projeto final de Sistemas de Apoio à Decisão, UEG / Trindade, 2026."
    },
)

inject_css()

# ------------------------------------------------------------------ navegação
paginas = [
    st.Page("pages/1_visao_geral.py", title="Visão geral", default=True),
    st.Page("pages/2_evidencias.py", title="Evidências"),
    st.Page("pages/3_regras_premissas.py", title="Regras"),
    st.Page("pages/4_simulacao.py", title="Simulador"),
    st.Page("pages/5_recomendacao.py", title="Melhor política"),
]

st.logo("assets/marca.svg", size="large")
nav = st.navigation(paginas, position="top")
nav.run()

# ------------------------------------------------------------------ rodapé
st.html(
    """
    <div style="margin-top:4.5rem;padding-top:1.25rem;border-top:1px solid #E5E1D7;
                display:flex;justify-content:space-between;align-items:center;gap:1rem;
                color:#9A9E96;font-size:.66rem;letter-spacing:.02em">
        <span>Adega Bom Sabor · Sistema de Apoio à Decisão</span>
        <span>UEG Trindade · POC 2026 · v2.1</span>
    </div>
    """
)
