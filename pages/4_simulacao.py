"""04 · Simulador — e se mudarmos o teto e as premissas?"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sad.rules import aplicar_regras
from sad.simulation import resumo, simular
from ui import (
    GREEN,
    INK,
    MUTED,
    OCHRE,
    SAGE,
    WINE,
    brl,
    card_head,
    eixo_meses,
    get_cfg,
    get_df,
    insight,
    metric,
    num,
    page_header,
    pct,
    section,
    show_fig,
    style_fig,
)

df = get_df()
cfg = get_cfg()
premissas_base = dict(cfg.get("premissas_perda_volume", {}))

page_header(
    kicker="04 · Simulação",
    title="Simulador",
    subtitle="Mova o teto e as premissas. Veja o efeito no lucro, na receita, no desconto e no volume — em tempo real.",
    meta=[("Base", f"{num(len(df))} vendas"), ("Modelo", "what-if")],
)

# ---------------------------------------------------------------- controles
with st.container(border=True):
    card_head("Parâmetros do cenário", "a comparação é sempre contra a política praticada hoje")

    m1, m2 = st.columns([1.05, 1.35], vertical_alignment="bottom")
    with m1:
        modo = st.segmented_control(
            "Modo de operação",
            ["Teto uniforme", "Regras configuradas"],
            default="Teto uniforme",
            key="sim_modo",
        )
    with m2:
        if modo == "Teto uniforme":
            teto_global = st.slider(
                "Teto uniforme de desconto (%)",
                min_value=0.0,
                max_value=40.0,
                value=float(cfg.get("teto_padrao", 10)),
                step=0.5,
                key="sim_teto",
            )
        else:
            teto_global = None
            st.caption(
                f"Usando as {sum(1 for r in cfg['regras'] if r.get('ativa', True))} regras ativas. "
                "Prioritárias de estoque prevalecem sobre as comuns."
            )

    p1, p2, p3 = st.columns(3)
    with p1:
        perda_baixa = st.slider(
            "Perda de volume · Baixa (%)", 0, 100,
            int(premissas_base.get("Baixa", 0)), 1, key="sim_perda_baixa",
        )
    with p2:
        perda_media = st.slider(
            "Perda de volume · Média (%)", 0, 100,
            int(premissas_base.get("Média", 10)), 1, key="sim_perda_media",
        )
    with p3:
        perda_alta = st.slider(
            "Perda de volume · Alta (%)", 0, 100,
            int(premissas_base.get("Alta", 25)), 1, key="sim_perda_alta",
        )

premissas = {"Baixa": perda_baixa, "Média": perda_media, "Alta": perda_alta}

# ---------------------------------------------------------------- simulação
if modo == "Regras configuradas":
    inferencia = aplicar_regras(df, cfg)
    teto_final = inferencia["teto_regras"].to_numpy(float)
else:
    teto_final = np.full(len(df), float(teto_global or 0))

sim = simular(df, teto_final, premissas)
base = resumo(df)
res = resumo(df, sim)

d_rec = res["receita"] - base["receita"]
d_lucro = res["lucro"] - base["lucro"]
d_desc = res["abatido"] - base["abatido"]
d_vol = res["unidades"] - base["unidades"]

section("Impacto do cenário", "Resultados projetados contra a política atual")

r1, r2, r3, r4 = st.columns(4, gap="small")
with r1:
    metric(
        "Receita simulada",
        brl(res["receita"]),
        f"atual {brl(base['receita'])}",
        tone="positive" if d_rec >= 0 else "negative",
        delta=f"{'+' if d_rec >= 0 else '−'}{brl(abs(d_rec))} ({pct(d_rec / base['receita'] * 100, 1, True)})",
    )
with r2:
    metric(
        "Lucro simulado",
        brl(res["lucro"]),
        f"atual {brl(base['lucro'])}",
        tone="positive" if d_lucro >= 0 else "negative",
        delta=f"{'+' if d_lucro >= 0 else '−'}{brl(abs(d_lucro))} ({pct(d_lucro / base['lucro'] * 100, 1, True)})",
    )
with r3:
    metric(
        "Desconto abatido",
        brl(res["abatido"]),
        f"atual {brl(base['abatido'])}",
        tone="positive" if d_desc <= 0 else "negative",
        delta=f"{'+' if d_desc >= 0 else '−'}{brl(abs(d_desc))} ({pct(d_desc / base['abatido'] * 100, 1, True)})",
    )
with r4:
    metric(
        "Volume esperado",
        f"{num(res['unidades'])} un.",
        f"atual {num(base['unidades'])} un.",
        tone="positive" if d_vol >= 0 else "negative",
        delta=f"{'+' if d_vol >= 0 else '−'}{num(abs(d_vol))} ({pct(d_vol / base['unidades'] * 100, 1, True)})",
    )

if d_lucro >= 0:
    insight(
        "Leitura do cenário",
        f"O cenário <strong>adiciona {brl(d_lucro)} ao lucro</strong> "
        f"({pct(d_lucro / base['lucro'] * 100, 1, True)}) e reduz o desconto abatido em "
        f"<strong>{pct(abs(d_desc) / base['abatido'] * 100, 1)}</strong>. "
        f"O volume esperado varia {pct(d_vol / base['unidades'] * 100, 1, True)}.",
        tone="positive",
    )
else:
    insight(
        "Leitura do cenário",
        f"O cenário <strong>reduz {brl(abs(d_lucro))} do lucro</strong> "
        f"({pct(d_lucro / base['lucro'] * 100, 1, True)}). "
        "A perda de volume ou a estrutura de margem anulam o ganho obtido com a redução do desconto.",
        tone="negative",
    )

# ---------------------------------------------------------------- gráficos
g1, g2 = st.columns(2, gap="small")

with g1:
    with st.container(border=True):
        card_head("Lucro mensal", "política atual × cenário simulado")
        d = df.assign(lucro_sim=sim["lucro_sim"])
        mensal = d.groupby("ano_mes", as_index=False).agg(
            atual=("lucro", "sum"), simulado=("lucro_sim", "sum")
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=mensal["ano_mes"], y=mensal["atual"], name="Atual",
                mode="lines", line=dict(color="#B9B4A7", width=1.6, dash="dot"),
                hovertemplate="Atual: R$ %{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=mensal["ano_mes"], y=mensal["simulado"], name="Simulado",
                mode="lines", line=dict(color=GREEN, width=2),
                fill="tozeroy", fillcolor="rgba(14,90,58,0.05)",
                hovertemplate="Simulado: R$ %{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(hovermode="x")
        tickvals, ticktext = eixo_meses(mensal["ano_mes"])
        fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
        fig.update_yaxes(tickprefix="R$ ", tickformat="~s", nticks=4)
        show_fig(fig, height=304, legend=True, margin=dict(l=54, r=10, t=30, b=32))

with g2:
    with st.container(border=True):
        card_head("Lucro por perfil", "política atual × cenário simulado")
        perf = df.assign(lucro_sim=sim["lucro_sim"]).groupby("sensibilidade_preco", as_index=False).agg(
            atual=("lucro", "sum"), simulado=("lucro_sim", "sum")
        )
        perf = perf.set_index("sensibilidade_preco").reindex(["Baixa", "Média", "Alta"]).reset_index()
        perf = perf.iloc[::-1]
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Atual", x=perf["atual"], y=perf["sensibilidade_preco"], orientation="h",
                marker_color=SAGE, marker_line_width=0,
                hovertemplate="Atual · %{y}: R$ %{x:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Simulado", x=perf["simulado"], y=perf["sensibilidade_preco"], orientation="h",
                marker_color=GREEN, marker_line_width=0,
                hovertemplate="Simulado · %{y}: R$ %{x:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(barmode="group")
        fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
        fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK))
        show_fig(fig, height=304, legend=True, margin=dict(l=54, r=10, t=30, b=32))

# ---------------------------------------------------------------- sensibilidade
section("Sensibilidade", "Como o lucro responde ao teto e à perda de volume")

st_tab, pv_tab = st.tabs(["Teto × lucro", "Perda de volume"])

with st_tab:
    with st.container(border=True):
        card_head("Curva de lucro por teto uniforme", "cada ponto simula toda a base")
        tetos = np.arange(0, 41, 2.5)
        lucros = [resumo(df, simular(df, np.full(len(df), t), premissas))["lucro"] for t in tetos]
        melhor_idx = int(np.argmax(lucros))
        teto_melhor = float(tetos[melhor_idx])
        lucro_melhor = float(lucros[melhor_idx])
        atual = float(teto_global) if modo == "Teto uniforme" else None

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=tetos, y=lucros, mode="lines",
                line=dict(color=GREEN, width=2),
                name="Lucro simulado",
                hovertemplate="Teto %{x:.1f}%<br>Lucro R$ %{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[teto_melhor], y=[lucro_melhor],
                mode="markers", marker=dict(color=GREEN, size=8, symbol="circle"),
                name="Ótimo",
                hovertemplate="Ótimo: %{x:.1f}%<br>R$ %{y:,.0f}<extra></extra>",
            )
        )
        if atual is not None:
            lucro_atual_cenario = float(np.interp(atual, tetos, lucros))
            fig.add_vline(x=atual, line=dict(color=WINE, width=1, dash="dot"))
            fig.add_trace(
                go.Scatter(
                    x=[atual], y=[lucro_atual_cenario],
                    mode="markers", marker=dict(color=WINE, size=7, symbol="diamond"),
                    name="Seu cenário",
                    hovertemplate="Cenário: %{x:.1f}%<br>R$ %{y:,.0f}<extra></extra>",
                )
            )
        fig.update_xaxes(ticksuffix="%")
        fig.update_yaxes(
            tickprefix="R$ ",
            tickformat="~s",
            nticks=4,
            range=[min(lucros) - (max(lucros) - min(lucros)) * 0.25 - 1,
                   max(lucros) + (max(lucros) - min(lucros)) * 0.25 + 1],
        )
        show_fig(fig, height=322, legend=True, margin=dict(l=54, r=24, t=30, b=34))

        insight(
            "Ponto ótimo",
            f"O lucro máximo da curva é <strong>{brl(lucro_melhor)}</strong>, com teto uniforme de "
            f"<strong>{pct(teto_melhor, 1)}</strong>. "
            + (
                f"O cenário selecionado ({pct(atual, 1)}) projeta <strong>{brl(lucro_atual_cenario)}</strong>."
                if atual is not None
                else "Ajuste o modo para comparar com um teto uniforme específico."
            ),
        )

with pv_tab:
    with st.container(border=True):
        card_head("Lucro sob diferentes perdas de volume", "uma curva por perfil de sensibilidade")
        perdas = np.arange(0, 61, 5)
        fig = go.Figure()
        for perfil, cor in [("Baixa", GREEN), ("Média", OCHRE), ("Alta", WINE)]:
            valores = []
            for p in perdas:
                prem = dict(premissas)
                prem[perfil] = float(p)
                valores.append(resumo(df, simular(df, teto_final, prem))["lucro"])
            fig.add_trace(
                go.Scatter(
                    x=perdas, y=valores, mode="lines", name=perfil,
                    line=dict(color=cor, width=2),
                    hovertemplate=f"{perfil}: perda %{{x}}%<br>Lucro R$ %{{y:,.0f}}<extra></extra>",
                )
            )
        fig.update_xaxes(ticksuffix="%")
        fig.update_yaxes(tickprefix="R$ ", tickformat="~s", nticks=4)
        show_fig(fig, height=322, legend=True, margin=dict(l=54, r=10, t=30, b=34))
        st.caption(
            "A curva isola a perda de volume de um perfil, mantendo as premissas dos demais. "
            "Quanto mais inclinada, maior a dependência do desconto para sustentar volume."
        )
