"""05 · Otimização — o teto de desconto que maximiza lucro por segmento."""
import copy

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sad.config import config_para_yaml
from sad.simulation import resumo
from ui import (
    GREEN,
    INK,
    MUTED,
    OCHRE,
    WINE,
    _otimizar_cache,
    brl,
    card_head,
    empty_state,
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
cfg_base = get_cfg()

page_header(
    kicker="05 · Recomendação",
    title="Otimização",
    subtitle="O algoritmo testa cada teto em cada um dos 27 segmentos e devolve a política de maior lucro dentro da restrição de receita.",
    meta=[("Segmentos", "27"), ("Tetos", "0 · 5 · 10 · 15 · 20%")],
)

# ---------------------------------------------------------------- parâmetros
with st.container(border=True):
    card_head("Parâmetros da otimização", "a política recomendada respeita estes limites")

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        queda_max = st.slider(
            "Queda máxima de receita (%)",
            min_value=0,
            max_value=20,
            value=int(cfg_base.get("queda_max_receita", 5)),
            step=1,
            help="A receita total não pode cair mais do que este percentual.",
        )
    with q2:
        perda_alta = st.slider(
            "Perda de volume · Alta (%)", 0, 100,
            int(cfg_base["premissas_perda_volume"].get("Alta", 25)), 1,
        )
    with q3:
        perda_media = st.slider(
            "Perda de volume · Média (%)", 0, 100,
            int(cfg_base["premissas_perda_volume"].get("Média", 10)), 1,
        )
    with q4:
        perda_baixa = st.slider(
            "Perda de volume · Baixa (%)", 0, 100,
            int(cfg_base["premissas_perda_volume"].get("Baixa", 0)), 1,
        )

    acao, nota = st.columns([1, 3.4], vertical_alignment="center")
    with acao:
        rodar = st.button("Otimizar política", type="primary", use_container_width=True)
    with nota:
        st.caption(
            "As regras ativas e as faixas de margem da página Regras entram na otimização."
        )

cfg_exec = copy.deepcopy(cfg_base)
cfg_exec["queda_max_receita"] = int(queda_max)
cfg_exec["premissas_perda_volume"] = {
    "Alta": int(perda_alta),
    "Média": int(perda_media),
    "Baixa": int(perda_baixa),
}

if rodar:
    with st.spinner("Avaliando tetos nos 27 segmentos…"):
        resultado = _otimizar_cache(
            config_para_yaml(cfg_exec),
            cfg_exec["faixas_margem"]["baixa_ate"],
            cfg_exec["faixas_margem"]["alta_acima"],
        )
    st.session_state["opt_resultado"] = resultado
    st.session_state["opt_cfg"] = copy.deepcopy(cfg_exec)

resultado = st.session_state.get("opt_resultado")
cfg_resultado = st.session_state.get("opt_cfg", cfg_exec)

# ---------------------------------------------------------------- estado inicial
if not resultado:
    st.html(
        """
        <div style="border:1px solid #E5E1D7;border-radius:14px;background:#FFFDF8;padding:1.4rem 1.5rem;margin-top:1.4rem">
            <div class="step-grid">
                <div class="step">
                    <div class="step-num">01</div>
                    <div class="step-title">Maximiza o lucro</div>
                    <div class="step-text">Testa 0, 5, 10, 15 e 20% em cada um dos 27 segmentos e escolhe o maior lucro esperado.</div>
                </div>
                <div class="step">
                    <div class="step-num">02</div>
                    <div class="step-title">Protege a receita</div>
                    <div class="step-text">Se a receita cair além do limite, eleva o teto do segmento com maior perda até cumprir a restrição.</div>
                </div>
                <div class="step">
                    <div class="step-num">03</div>
                    <div class="step-title">Respeita as regras</div>
                    <div class="step-text">As regras de estoque continuam prevalecendo sobre qualquer teto recomendado.</div>
                </div>
            </div>
        </div>
        """
    )

else:
    # ---------------------------------------------------------------- resultado
    tabela = resultado["tabela"].copy()
    base = resumo(df)
    sim = resultado["sim"]
    novo = resumo(df, sim)

    d_lucro = novo["lucro"] - base["lucro"]
    d_receita = novo["receita"] - base["receita"]
    d_desconto = novo["abatido"] - base["abatido"]
    roi = d_lucro / abs(d_desconto) if abs(d_desconto) > 0 else 0.0

    alterado = (
        int(cfg_resultado.get("queda_max_receita", 0)) != int(queda_max)
        or cfg_resultado.get("premissas_perda_volume") != cfg_exec["premissas_perda_volume"]
    )
    if alterado:
        st.caption("Os parâmetros mudaram desde a última execução. Rode a otimização novamente para atualizar a política.")

    section(
        "Política recomendada",
        f"Otimizada com queda máxima de {pct(cfg_resultado.get('queda_max_receita', 5), 0)} "
        f"· {len(resultado['ajustes'])} segmento(s) ajustado(s) pela restrição",
    )

    o1, o2, o3, o4 = st.columns(4, gap="small")
    with o1:
        metric(
            "Lucro esperado",
            brl(novo["lucro"]),
            f"atual {brl(base['lucro'])}",
            tone="positive" if d_lucro >= 0 else "negative",
            delta=f"{'+' if d_lucro >= 0 else '−'}{brl(abs(d_lucro))} ({pct(d_lucro / base['lucro'] * 100, 1, True)})",
        )
    with o2:
        metric(
            "Receita esperada",
            brl(novo["receita"]),
            f"atual {brl(base['receita'])}",
            tone="positive" if d_receita >= 0 else "negative",
            delta=f"{'+' if d_receita >= 0 else '−'}{brl(abs(d_receita))} ({pct(d_receita / base['receita'] * 100, 1, True)})",
        )
    with o3:
        metric(
            "Desconto abatido",
            brl(novo["abatido"]),
            f"atual {brl(base['abatido'])}",
            tone="positive" if d_desconto <= 0 else "negative",
            delta=f"{'+' if d_desconto >= 0 else '−'}{brl(abs(d_desconto))} ({pct(d_desconto / base['abatido'] * 100, 1, True)})",
        )
    with o4:
        metric(
            "Retorno por R$ evitado",
            f"{roi:.1f}×".replace(".", ",") if roi else "—",
            "lucro adicional por real de desconto não concedido",
        )

    if d_lucro > 0:
        insight(
            "Resultado da otimização",
            f"A política recomendada adiciona <strong>{brl(d_lucro)} ao lucro</strong> "
            f"({pct(d_lucro / base['lucro'] * 100, 1, True)}) e evita "
            f"<strong>{brl(abs(d_desconto))}</strong> em desconto. "
            f"A receita varia {pct(d_receita / base['receita'] * 100, 1, True)}. "
            + (
                "Nenhum segmento precisou ser ajustado para cumprir a restrição de receita."
                if not resultado["ajustes"]
                else f"{len(resultado['ajustes'])} segmento(s) tiveram o teto elevado para cumprir a restrição."
            ),
            tone="positive",
        )
    else:
        insight(
            "Resultado da otimização",
            "A política encontrada não supera o lucro atual com as premissas informadas. "
            "Revise a perda de volume e a restrição de receita antes de aplicar.",
            tone="warning",
        )

    # ---------------------------------------------------------------- gráficos
    section("Onde o lucro aparece", "Ganho por segmento e distribuição dos tetos")

    v1, v2 = st.columns([1.2, 0.8], gap="small")

    with v1:
        with st.container(border=True):
            card_head("Top 10 segmentos por ganho", "Δ lucro esperado contra a política atual")
            top = tabela.nlargest(10, "diferenca").iloc[::-1].copy()

            def _rotulo(seg: str) -> str:
                partes = [p.strip() for p in seg.split("|")]
                if len(partes) == 3:
                    perfil, margem, canal = partes
                    margem = margem.replace("margem ", "")
                    canal = {"Clube de assinatura": "Clube", "Loja física": "Loja", "E-commerce": "E-com."}.get(canal, canal)
                    return f"{perfil} · {margem} · {canal}"
                return seg

            top["rotulo"] = top["segmento"].map(_rotulo)
            fig = go.Figure(
                go.Bar(
                    x=top["diferenca"],
                    y=top["rotulo"],
                    orientation="h",
                    marker_color=[GREEN if v >= 0 else WINE for v in top["diferenca"]],
                    marker_line_width=0,
                    text=[f"{'+' if v >= 0 else '−'}{brl(abs(v))}" for v in top["diferenca"]],
                    textposition="outside",
                    textfont=dict(size=9.5, color=MUTED),
                    cliponaxis=False,
                    hovertemplate="<b>%{y}</b><br>Δ lucro: R$ %{x:,.0f}<extra></extra>",
                )
            )
            fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
            fig.update_yaxes(showgrid=False, tickfont=dict(size=9.5, color=INK))
            show_fig(fig, height=360, margin=dict(l=150, r=70, t=8, b=4))

    with v2:
        with st.container(border=True):
            card_head("Distribuição dos tetos", "segmentos por teto recomendado")
            dist = tabela["teto_recomendado_%"].value_counts().sort_index()
            tetos = [int(t) for t in dist.index]
            counts = list(dist.values)
            cores = ["#3E8765", "#9FC0A8", "#6FA789", "#C7D8C7", GREEN][: len(tetos)]
            fig = go.Figure(
                go.Bar(
                    x=[f"{t}%" for t in tetos],
                    y=counts,
                    marker_color=cores,
                    marker_line_width=0,
                    text=counts,
                    textposition="outside",
                    textfont=dict(size=10.5, color=MUTED),
                    hovertemplate="Teto %{x}: %{y} segmento(s)<extra></extra>",
                )
            )
            fig.update_xaxes(type="category")
            fig.update_yaxes(range=[0, max(counts) * 1.25 if counts else 1])
            show_fig(fig, height=360, margin=dict(l=34, r=10, t=8, b=28))

    # ---------------------------------------------------------------- tabela
    section("Política por segmento", "Os 27 segmentos, com desconto praticado e teto recomendado")

    visao = tabela[
        [
            "segmento",
            "vendas",
            "desconto_medio_atual_%",
            "teto_recomendado_%",
            "lucro_atual",
            "lucro_esperado",
            "diferenca",
            "regra_predominante",
        ]
    ].copy()
    visao["desconto_medio_atual_%"] = visao["desconto_medio_atual_%"].map(pct)
    visao["teto_recomendado_%"] = visao["teto_recomendado_%"].map(pct)
    for c in ["lucro_atual", "lucro_esperado"]:
        visao[c] = visao[c].map(brl)
    visao["diferenca"] = visao["diferenca"].map(
        lambda v: ("+" if v >= 0 else "−") + brl(abs(v))
    )
    visao.columns = [
        "Segmento",
        "Vendas",
        "Desconto atual",
        "Teto recomendado",
        "Lucro atual",
        "Lucro esperado",
        "Δ Lucro",
        "Regra predominante",
    ]
    st.dataframe(visao, hide_index=True, use_container_width=True, height=390)

    with st.expander("Justificativas dos principais segmentos"):
        for _, row in tabela.sort_values("diferenca", ascending=False).head(8).iterrows():
            cor = GREEN if row["diferenca"] >= 0 else WINE
            st.html(
                f"""
                <div style="padding:.7rem .2rem;border-bottom:1px solid #EEEAE0">
                    <div style="display:flex;justify-content:space-between;gap:1rem;align-items:baseline">
                        <span style="font-size:.78rem;font-weight:600;color:#1D241F">{row['segmento']}</span>
                        <span style="font-size:.72rem;color:{cor};white-space:nowrap;font-weight:600">
                            teto {int(row['teto_recomendado_%'])}% · {'+' if row['diferenca'] >= 0 else '−'}{brl(abs(row['diferenca']))}
                        </span>
                    </div>
                    <div style="font-size:.72rem;color:#70766D;line-height:1.5;margin-top:.2rem">{row['justificativa']}</div>
                </div>
                """
            )

    # ---------------------------------------------------------------- exportação
    section("Levar a política adiante", "Exporte o resultado para aplicar em produção")

    x1, x2, x3 = st.columns([1, 1, 2], gap="small")
    with x1:
        st.download_button(
            "Baixar CSV por segmento",
            data=tabela.to_csv(index=False).encode("utf-8-sig"),
            file_name="politica_otimizada.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with x2:
        export = {
            "configuracao": cfg_resultado,
            "tetos_recomendados": {
                row["segmento"]: row["teto_recomendado_%"] for _, row in tabela.iterrows()
            },
        }
        st.download_button(
            "Baixar YAML da política",
            data=config_para_yaml(export),
            file_name="politica_otimizada.yaml",
            mime="application/x-yaml",
            use_container_width=True,
        )
    with x3:
        st.caption("O YAML preserva as regras, premissas e o teto recomendado para cada segmento.")

    with st.expander("Plano de implementação em produção"):
        st.html(
            """
            <div class="step-grid">
                <div class="step">
                    <div class="step-num">FASE 1 · 1–2 SEMANAS</div>
                    <div class="step-title">Validar em piloto</div>
                    <div class="step-text">Aplicar em um segmento com cerca de 10% dos clientes, monitorar lucro, receita, volume e satisfação, e rodar um teste A/B contra a política atual.</div>
                </div>
                <div class="step">
                    <div class="step-num">FASE 2 · 2–4 SEMANAS</div>
                    <div class="step-title">Expandir com dados reais</div>
                    <div class="step-text">Levar a política aos segmentos de maior ganho projetado e recalibrar as premissas de perda de volume com o que for observado.</div>
                </div>
                <div class="step">
                    <div class="step-num">FASE 3 · SEMANA 5+</div>
                    <div class="step-title">Operar com alertas</div>
                    <div class="step-text">Aplicar em todos os segmentos, acompanhar desvios de lucro e receita e revisar a política a cada trimestre.</div>
                </div>
            </div>
            """
        )
