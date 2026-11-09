"""02 · Evidências — o desconto realmente muda o volume comprado?"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sad.data import relatorio_qualidade
from sad.diagnostico import spearman_desconto_quantidade, wilcoxon_por_segmento
from ui import (
    FAINT,
    GREEN,
    INK,
    MUTED,
    OCHRE,
    SAGE,
    WINE,
    brl,
    card_head,
    carregar_dfs,
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

w = wilcoxon_por_segmento(df, ("canal", "sensibilidade_preco", "tipo"))
w.columns = [
    "Canal",
    "Sensibilidade",
    "Tipo",
    "Qtd. média com desc.",
    "Qtd. média sem desc.",
    "Diferença",
    "Estatística",
    "p-valor",
    "Significativo?",
]

sig_count = int((w["Significativo?"] == "Sim").sum())
total = len(w)
sig_pct = sig_count / total * 100 if total else 0
diff_media = float(w["Diferença"].mean())
p_mediana = float(w["p-valor"].median())
rho, rho_p = spearman_desconto_quantidade(df)
rho_txt = f"{rho:.3f}".replace(".", ",")

page_header(
    kicker="02 · Diagnóstico",
    title="Evidências",
    subtitle=(
        "O desconto realmente aumenta o que o cliente leva? "
        f"Testamos a hipótese em {total} interseções de canal, perfil e tipo de produto."
    ),
    meta=[("Método", "Mann-Whitney"), ("Significância", "α = 0,05")],
)

insight(
    "Hipótese testada",
    "A quantidade comprada com desconto é estatisticamente diferente da quantidade sem desconto. "
    "Usamos o teste não paramétrico de <strong>Mann-Whitney (Wilcoxon rank-sum)</strong> em cada um dos "
    f"<strong>{total} interseções</strong>. Um p-valor abaixo de 0,05 indica diferença significativa.",
)

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    metric(
        "Interseções significativas",
        f"{sig_count} de {total}",
        f"{pct(sig_pct)} das interseções",
        tone="positive" if sig_count else "neutral",
    )
with c2:
    metric(
        "Diferença média",
        f"{diff_media:+.2f} un.".replace(".", ",", 1),
        "com desconto menos sem desconto",
        tone="positive" if diff_media > 0 else "negative",
    )
with c3:
    metric(
        "p-valor mediano",
        f"{p_mediana:.3f}".replace(".", ","),
        "abaixo de 0,05 indica efeito real",
    )
with c4:
    metric(
        "Correlação de Spearman",
        rho_txt,
        f"desconto × quantidade · p = {rho_p:.2f}".replace(".", ","),
    )

# ---------------------------------------------------------------- tabela
section("Resultados por interseção", "Canal, sensibilidade e tipo de produto")

tab = w[
    [
        "Canal",
        "Sensibilidade",
        "Tipo",
        "Qtd. média com desc.",
        "Qtd. média sem desc.",
        "Diferença",
        "p-valor",
        "Significativo?",
    ]
].copy()
tab.columns = [
    "Canal",
    "Sensibilidade",
    "Tipo",
    "Com desconto",
    "Sem desconto",
    "Diferença",
    "p-valor",
    "Significativo",
]

for col in ["Com desconto", "Sem desconto", "Diferença"]:
    tab[col] = tab[col].map(lambda v: f"{v:.2f}".replace(".", ","))
tab["p-valor"] = tab["p-valor"].map(lambda v: f"{v:.3f}".replace(".", ","))

st.dataframe(
    tab,
    hide_index=True,
    use_container_width=True,
    height=352,
    column_config={
        "Significativo": st.column_config.TextColumn(width="small"),
    },
)

# ---------------------------------------------------------------- gráficos
section("Comparativo visual", "Quantidade média com e sem desconto")

gs1, gs2 = st.columns(2, gap="small")

with gs1:
    with st.container(border=True):
        card_head("Por sensibilidade a preço", "unidades por transação")
        ws = (
            w.groupby("Sensibilidade", as_index=False)[["Qtd. média com desc.", "Qtd. média sem desc."]]
            .mean(numeric_only=True)
            .set_index("Sensibilidade")
            .reindex(["Baixa", "Média", "Alta"])
            .reset_index()
        )
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Com desconto",
                x=ws["Sensibilidade"],
                y=ws["Qtd. média com desc."],
                marker_color=GREEN,
                marker_line_width=0,
                text=[f"{v:.2f}".replace(".", ",") for v in ws["Qtd. média com desc."]],
                textposition="outside",
                textfont=dict(size=10, color=MUTED),
                hovertemplate="Com desconto: %{y:.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Sem desconto",
                x=ws["Sensibilidade"],
                y=ws["Qtd. média sem desc."],
                marker_color=SAGE,
                marker_line_width=0,
                text=[f"{v:.2f}".replace(".", ",") for v in ws["Qtd. média sem desc."]],
                textposition="outside",
                textfont=dict(size=10, color=MUTED),
                hovertemplate="Sem desconto: %{y:.2f}<extra></extra>",
            )
        )
        show_fig(fig, height=286, legend=True, margin=dict(l=4, r=10, t=30, b=4))

with gs2:
    with st.container(border=True):
        card_head("Por canal de venda", "unidades por transação")
        wc = (
            w.groupby("Canal", as_index=False)[["Qtd. média com desc.", "Qtd. média sem desc."]]
            .mean(numeric_only=True)
        )
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Com desconto",
                x=wc["Canal"],
                y=wc["Qtd. média com desc."],
                marker_color=GREEN,
                marker_line_width=0,
                text=[f"{v:.2f}".replace(".", ",") for v in wc["Qtd. média com desc."]],
                textposition="outside",
                textfont=dict(size=10, color=MUTED),
                hovertemplate="Com desconto: %{y:.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Sem desconto",
                x=wc["Canal"],
                y=wc["Qtd. média sem desc."],
                marker_color=SAGE,
                marker_line_width=0,
                text=[f"{v:.2f}".replace(".", ",") for v in wc["Qtd. média sem desc."]],
                textposition="outside",
                textfont=dict(size=10, color=MUTED),
                hovertemplate="Sem desconto: %{y:.2f}<extra></extra>",
            )
        )
        show_fig(fig, height=286, legend=True, margin=dict(l=4, r=10, t=30, b=4))

# ---------------------------------------------------------------- heatmap
section("Mapa de significância", "p-valor por canal, sensibilidade e tipo de produto")

with st.container(border=True):
    card_head("p-valor por interseção", "verde = diferença significativa · claro = sem evidência")
    matriz = w.pivot_table(index=["Canal", "Sensibilidade"], columns="Tipo", values="p-valor")
    z = matriz.values.astype(float)
    y_labels = [f"{c} · {s}" for c, s in matriz.index]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=list(matriz.columns),
            y=y_labels,
            colorscale=[
                [0.0, "#0E5A3A"],
                [0.05, "#5C9B7B"],
                [0.12, "#CBDCCB"],
                [0.30, "#E9E5D9"],
                [1.0, "#F1EDE3"],
            ],
            zmin=0,
            zmax=0.5,
            hovertemplate="<b>%{y}</b><br>%{x}<br>p = %{z:.3f}<extra></extra>",
            colorbar=dict(
                title=dict(text="p", side="right", font=dict(size=10, color=MUTED)),
                thickness=8,
                len=0.6,
                tickfont=dict(size=9, color=MUTED),
                outlinewidth=0,
            ),
            xgap=2,
            ygap=2,
        )
    )
    style_fig(fig, height=max(380, 36 * len(matriz.index) + 40), margin=dict(l=176, r=8, t=6, b=34))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, tickfont=dict(size=10, color=INK))
    for i, ylab in enumerate(y_labels):
        for j, tipo in enumerate(matriz.columns):
            valor = z[i, j]
            if np.isnan(valor):
                txt, cor = "—", FAINT
            else:
                txt = f"{valor:.3f}".replace(".", ",")
                cor = "#FFFFFF" if valor < 0.05 else INK
            fig.add_annotation(
                x=tipo,
                y=ylab,
                text=txt,
                showarrow=False,
                font=dict(size=9.5, color=cor, family="Inter"),
            )
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False, "responsive": True},
    )

# ---------------------------------------------------------------- conclusão
if sig_count == 0:
    conclusao = (
        f"<strong>Nenhuma das {total} interseções</strong> apresenta diferença estatisticamente significativa. "
        f"Na média, a diferença é de <strong>{diff_media:+.2f} unidade</strong> e a correlação entre desconto e "
        f"quantidade é praticamente nula (<strong>ρ = {rho_txt}</strong>). "
        "A evidência disponível não sustenta que o desconto atual aumente o volume comprado."
    )
    tone = "negative"
elif sig_count / total < 0.5:
    conclusao = (
        f"Apenas <strong>{sig_count} de {total} interseções ({pct(sig_pct)})</strong> mostram diferença "
        f"significativa. A correlação geral entre desconto e quantidade é <strong>ρ = {rho_txt}</strong>. "
        "O efeito existe em poucos contextos e não justifica uma política de desconto ampla."
    )
    tone = "warning"
else:
    conclusao = (
        f"<strong>{sig_count} de {total} interseções ({pct(sig_pct)})</strong> apresentam diferença "
        f"significativa entre comprar com e sem desconto. A correlação geral é <strong>ρ = {rho_txt}</strong>."
    )
    tone = "positive"

insight("Conclusão estatística", conclusao, tone=tone)

# ---------------------------------------------------------------- qualidade
with st.expander("Qualidade e consistência da base"):
    q = relatorio_qualidade(carregar_dfs()).copy()
    q.columns = ["Verificação", "Resultado"]
    st.dataframe(q, hide_index=True, use_container_width=True)
