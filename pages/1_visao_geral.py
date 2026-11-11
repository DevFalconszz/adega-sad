"""01 · Visão geral — o retrato financeiro da política atual."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sad.diagnostico import desconto_por, indicadores
from sad.simulation import resumo
from ui import (
    AMBAR,
    GREEN,
    MUTED,
    OCHRE,
    VERMELHO,
    WINE,
    brl,
    brl_curto,
    card_head,
    eixo_meses,
    get_df,
    get_recomendacao,
    insight,
    mes_ano,
    metric,
    num,
    page_header,
    pct,
    policy_hero,
    section,
    show_fig,
    stat_strip,
    style_fig,
)

df = get_df()
k = indicadores(df)

inicio = mes_ano(df["data_compra"].min())
fim = mes_ano(df["data_compra"].max())
periodo = f"{inicio} – {fim}"
n = len(df)

page_header(
    kicker="01 · Painel executivo",
    title="Visão geral",
    subtitle="O retrato financeiro da política atual — e a melhor política de desconto que o sistema recomenda.",
    meta=[("Base", f"{num(n)} vendas"), ("Período", periodo)],
)

# ---------------------------------------------------------------- melhor política
rec = get_recomendacao()
base = resumo(df)
novo = resumo(df, rec["sim"])
d_lucro = novo["lucro"] - base["lucro"]
d_receita = novo["receita"] - base["receita"]
d_desconto = novo["abatido"] - base["abatido"]
dist = rec["tabela"]["teto_recomendado_%"].value_counts().sort_index()
tetos_txt = " · ".join(f"{int(v)}× {int(t)}%" for t, v in dist.items())
sinal = "+" if d_lucro >= 0 else "−"

policy_hero(
    brl(novo["lucro"]),
    f"<strong>{sinal}{brl(abs(d_lucro))} ({pct(d_lucro / base['lucro'] * 100, 1, True)})</strong> "
    f"de lucro sobre a política atual, com <strong>{pct(abs(d_desconto) / base['abatido'] * 100, 1)} "
    "menos desconto</strong> concedido.",
    [
        ("Receita", pct(d_receita / base["receita"] * 100, 1, True)),
        ("Desconto", pct(d_desconto / base["abatido"] * 100, 1, True)),
        ("Tetos", tetos_txt),
    ],
    "Calculada sobre as <b>7.522 vendas</b> com as <b>5 regras ativas</b> — inclusive as regras de estoque. "
    "Ganho projetado pelo modelo, a validar em piloto.",
)

acao, nota = st.columns([1.05, 3.95], vertical_alignment="center")
with acao:
    if st.button("Ver a política por segmento", type="primary", use_container_width=True):
        st.switch_page("pages/5_recomendacao.py")
with nota:
    st.caption("A recomendação se atualiza sempre que as regras ou as premissas mudam.")

section("O ponto de partida", "A política atual, antes da recomendação")

# ---------------------------------------------------------------- indicadores
ticket = k["receita"] / n if n else 0
margem = k["lucro"] / k["receita"] * 100 if k["receita"] else 0
desc_medio = df.loc[df["desconto_pct"] > 0, "desconto_pct"].mean()

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    metric(
        "Receita total",
        brl(k["receita"]),
        f"Ticket médio de {brl(ticket)}",
    )
with c2:
    metric(
        "Lucro bruto",
        brl(k["lucro"]),
        f"Margem de {pct(margem)} sobre a receita",
        tone="positive",
    )
with c3:
    metric(
        "Desconto concedido",
        brl(k["abatido"]),
        f"{pct(k['itens_desconto_pct'], 0)} dos itens saíram com desconto",
        tone="negative",
    )
with c4:
    metric(
        "Peso no lucro",
        pct(k["abatido_pct_lucro"]),
        "do lucro bruto consumido pelo desconto",
        tone="warning",
    )

insight(
    "Leitura do período",
    f"O desconto concedido equivale a <strong>{pct(k['abatido_pct_lucro'])} do lucro bruto</strong>. "
    f"Quem compra com desconto leva <strong>{num(k['qtd_com'], 2)} unidades</strong>, contra "
    f"<strong>{num(k['qtd_sem'], 2)}</strong> de quem compra sem desconto. "
    "Na prática, o desconto atual compra quase nenhum volume adicional — mas custa caro.",
    tone="negative",
)

# ---------------------------------------------------------------- retrato
section("Onde o desconto está", "Valor abatido por perfil e por canal de venda")

col_a, col_b = st.columns([1.15, 0.85], gap="small")

with col_a:
    with st.container(border=True):
        card_head("Desconto por perfil de cliente", "R$ abatidos no período")
        p = (
            desconto_por(df, "sensibilidade_preco")
            .set_index("sensibilidade_preco")
            .reindex(["Baixa", "Média", "Alta"])
            .reset_index()
        )
        fig = go.Figure(
            go.Bar(
                x=p["abatido"],
                y=p["sensibilidade_preco"],
                orientation="h",
                marker_color=[GREEN, OCHRE, WINE],
                marker_line_width=0,
                text=[brl(v) for v in p["abatido"]],
                textposition="outside",
                textfont=dict(size=10.5, color=MUTED),
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f} abatidos<extra></extra>",
            )
        )
        fig.update_xaxes(showgrid=False, showticklabels=False, showline=False)
        fig.update_yaxes(showgrid=False, autorange="reversed", tickfont=dict(size=11, color="#1D241F"))
        show_fig(fig, height=238, margin=dict(l=58, r=62, t=8, b=4))

with col_b:
    with st.container(border=True):
        card_head("Participação por canal", "no valor total abatido")
        c = desconto_por(df, "canal")
        total = c["abatido"].sum()
        fig = go.Figure(
            go.Pie(
                labels=c["canal"],
                values=c["abatido"],
                hole=0.72,
                sort=False,
                marker=dict(colors=[GREEN, WINE, OCHRE], line=dict(color="#FFFDF8", width=2)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percent}<extra></extra>",
            )
        )
        fig.add_annotation(
            text=f"<b style='font-size:15px'>{brl_curto(total)}</b>"
            "<br><span style='font-size:9px;letter-spacing:.12em'>ABATIDOS</span>",
            showarrow=False,
            font=dict(family="Inter", size=11, color=MUTED),
        )
        style_fig(fig, height=238, margin=dict(l=0, r=0, t=4, b=0))
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5,
                font=dict(size=9.5, color=MUTED),
                itemwidth=30,
            ),
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            theme=None,
            config={"displayModeBar": False, "responsive": True},
        )

# ---------------------------------------------------------------- tendência
section("Evolução no tempo", "Lucro bruto e desconto abatido, mês a mês")

m = (
    df.groupby("ano_mes", as_index=False)
    .agg(lucro=("lucro", "sum"), abatido=("valor_abatido", "sum"))
    .sort_values("ano_mes")
)

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=m["ano_mes"],
        y=m["abatido"],
        name="Desconto abatido",
        marker_color=WINE,
        marker_line_width=0,
        opacity=0.22,
        hovertemplate="Desconto: R$ %{y:,.0f}<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=m["ano_mes"],
        y=m["lucro"],
        name="Lucro bruto",
        mode="lines",
        line=dict(color=GREEN, width=2),
        fill="tozeroy",
        fillcolor="rgba(14,90,58,0.05)",
        hovertemplate="Lucro: R$ %{y:,.0f}<extra></extra>",
    )
)
fig.update_layout(hovermode="x")
tickvals, ticktext = eixo_meses(m["ano_mes"])
fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
fig.update_yaxes(tickprefix="R$ ", tickformat="~s", nticks=4)
show_fig(fig, height=332, legend=True, margin=dict(l=54, r=10, t=28, b=34))
st.caption(
    "O último ponto (ago/2026) cobre apenas os primeiros 15 dias do mês e por isso aparece abaixo dos meses completos."
)

# ---------------------------------------------------------------- faixa
section("Eficiência da operação", "Médias por transação no período")
stat_strip(
    [
        ("Ticket médio", brl(ticket), "por venda"),
        ("Lucro por venda", brl(k["lucro"] / n), "margem de contribuição"),
        ("Desconto médio", pct(desc_medio), "quando há desconto"),
        ("Margem média", pct(margem), "lucro sobre receita"),
    ]
)
