"""03 · Regras e premissas — a base de conhecimento que governa o desconto."""
import copy

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sad.config import PERFIS, TETOS, carregar_config, config_para_yaml
from sad.rules import aplicar_regras
from ui import (
    CAT,
    FAINT,
    GREEN,
    INK,
    LINE,
    MUTED,
    OCHRE,
    SAGE,
    WINE,
    brl,
    card_head,
    chip,
    get_cfg,
    get_df,
    insight,
    metric,
    num,
    page_header,
    pct,
    reset_cfg,
    section,
    show_fig,
    style_fig,
)

df = get_df()
cfg = get_cfg()
regras = cfg.get("regras", [])
padrao = carregar_config()
alterado = config_para_yaml(cfg) != config_para_yaml(padrao)

page_header(
    kicker="03 · Conhecimento",
    title="Regras e premissas",
    subtitle="As condições SE → ENTÃO, os limites e as premissas que transformam estratégia em teto de desconto.",
    meta=[("Regras", f"{len(regras)} ativas"), ("Teto padrão", pct(cfg.get("teto_padrao", 0), 0))],
)


def _limpar_widgets(prefixos: tuple[str, ...] = ()) -> None:
    for chave in list(st.session_state.keys()):
        if chave.startswith(prefixos):
            del st.session_state[chave]


def _resetar() -> None:
    reset_cfg()
    _limpar_widgets(("edit_", "prem_"))
    st.session_state.pop("opt_resultado", None)
    st.session_state.pop("opt_cfg", None)
    st.rerun()


# ---------------------------------------------------------------- ações
ac1, ac2, ac3, ac4 = st.columns([1.25, 1.1, 1.2, 3.0], vertical_alignment="center")
with ac1:
    editar = st.toggle("Modo de edição", key="modo_edicao")
with ac2:
    st.download_button(
        "Exportar YAML",
        data=config_para_yaml(cfg),
        file_name="politica_descontos.yaml",
        mime="application/x-yaml",
    )
with ac3:
    if alterado:
        if st.button("Restaurar padrão", type="secondary"):
            _resetar()

# ---------------------------------------------------------------- KPIs
ativas = sum(1 for r in regras if r.get("ativa", True))
comuns = sum(1 for r in regras if r.get("tipo") == "comum")
prioritarias = sum(1 for r in regras if r.get("tipo") == "prioritaria")

k1, k2, k3, k4 = st.columns(4, gap="small")
with k1:
    metric("Regras ativas", f"{ativas}", f"de {len(regras)} regras configuradas")
with k2:
    metric("Regras comuns", f"{comuns}", "vale sempre a mais restritiva")
with k3:
    metric("Regras prioritárias", f"{prioritarias}", "estoque prevalece sobre tudo", tone="warning")
with k4:
    metric("Teto padrão", pct(cfg.get("teto_padrao", 0), 0), "quando nenhuma regra casa")

if alterado:
    st.caption("A configuração ativa difere da política padrão. Exporte o YAML para preservar as alterações.")

tab_regras, tab_premissas, tab_impacto = st.tabs(
    ["Regras ativas", "Premissas", "Impacto na base"]
)

# ================================================================ TAB 1
with tab_regras:
    if editar:
        with st.container(border=True):
            card_head("Editar regras", "alterações valem para toda a aplicação nesta sessão")
            with st.form("form_regras", border=False):
                for i, r in enumerate(regras):
                    c_nome, c_ativa, c_teto = st.columns([4.2, 1.1, 1.7], vertical_alignment="center")
                    with c_nome:
                        st.html(
                            f"<div class='rule-id'>{r.get('id')} · {r.get('tipo', 'comum').upper()}</div>"
                            f"<div class='rule-name'>{r.get('nome', 'Regra')}</div>"
                            f"<div class='rule-condition'><code>{r.get('campo')} = {r.get('valor')}</code></div>"
                        )
                    with c_ativa:
                        st.toggle(
                            "Ativa",
                            value=bool(r.get("ativa", True)),
                            key=f"edit_ativa_{r.get('id')}",
                        )
                    with c_teto:
                        st.slider(
                            "Teto (%)",
                            min_value=0,
                            max_value=30,
                            value=int(r.get("teto", 0)),
                            step=1,
                            key=f"edit_teto_{r.get('id')}",
                        )
                salvar_regras = st.form_submit_button("Aplicar alterações", type="primary")

        if salvar_regras:
            novo = copy.deepcopy(cfg)
            for r in novo["regras"]:
                rid = r.get("id")
                r["ativa"] = bool(st.session_state.get(f"edit_ativa_{rid}", r.get("ativa", True)))
                r["teto"] = int(st.session_state.get(f"edit_teto_{rid}", r.get("teto", 0)))
            from ui import set_cfg

            set_cfg(novo)
            st.session_state.pop("opt_resultado", None)
            st.session_state.pop("opt_cfg", None)
            st.rerun()

    section("Regras de desconto", "Condições, tetos e prioridade de aplicação")

    for i, r in enumerate(regras):
        ativa = r.get("ativa", True)
        tipo = r.get("tipo", "comum")
        cor = WINE if tipo == "prioritaria" else GREEN
        with st.expander(f"{r.get('id')} — {r.get('nome', 'Regra')}", expanded=(i == 0)):
            flags = chip("Ativa", "positive") if ativa else chip("Inativa", "neutral")
            flags += " " + (
                chip("Prioritária", "negative") if tipo == "prioritaria" else chip("Comum", "neutral")
            )
            st.html(
                f"""
                <div class="rule-hero">
                    <div>
                        <div class="micro-label">Condição</div>
                        <div class="rule-condition" style="margin-top:.4rem">SE <code>{r.get('campo')} = {r.get('valor')}</code>
                        ENTÃO o teto de desconto é limitado a <strong style="color:{cor}">{r.get('teto')}%</strong>.</div>
                        <div class="rule-flags">{flags}</div>
                    </div>
                    <div class="rule-teto">
                        <div class="rule-teto-value">{r.get('teto')}%</div>
                        <div class="rule-teto-label">teto máximo</div>
                    </div>
                </div>
                """
            )
            if tipo == "prioritaria":
                st.caption("Regra de estoque: prevalece sobre todas as regras comuns.")
            elif not ativa:
                st.caption("Regra inativa: não participa da inferência.")

    with st.container(border=True):
        card_head("Como a inferência decide", "lógica de combinação entre regras")
        linhas = []
        for r in regras:
            if not r.get("ativa", True):
                continue
            marca = "  <span style='color:#8F2437;font-weight:600'>[prioritária]</span>" if r.get("tipo") == "prioritaria" else ""
            linhas.append(
                f"SE  ({r.get('campo')} = {r.get('valor')})  →  teto {r.get('teto')}%{marca}"
            )
        formula_html = "<br>\n                ".join(linhas)
        st.html(
            f"""
            <div class="formula">
                {formula_html}
                <br><br>
                Entre as regras comuns, vence o <strong>menor teto</strong>.<br>
                Regras prioritárias de estoque <strong>prevalecem</strong> sobre as demais.
            </div>
            """
        )
        st.caption("Campos disponíveis: sensibilidade_preco · faixa_margem · situacao_estoque · canal")

# ================================================================ TAB 2
with tab_premissas:
    faixas = cfg.get("faixas_margem", {})
    premissas = cfg.get("premissas_perda_volume", {})

    if editar:
        with st.container(border=True):
            card_head("Editar premissas", "parâmetros globais do modelo")
            with st.form("form_premissas", border=False):
                e1, e2, e3, e4 = st.columns(4)
                with e1:
                    teto_padrao = st.slider(
                        "Teto padrão (%)", 0, 30, int(cfg.get("teto_padrao", 0)), 1,
                        key="prem_teto_padrao",
                    )
                with e2:
                    queda = st.slider(
                        "Queda máx. de receita (%)", 0, 20, int(cfg.get("queda_max_receita", 5)), 1,
                        key="prem_queda",
                    )
                with e3:
                    baixa_ate = st.slider(
                        "Margem baixa até (%)", 10, 60, int(faixas.get("baixa_ate", 35)), 1,
                        key="prem_baixa",
                    )
                with e4:
                    alta_acima = st.slider(
                        "Margem alta acima de (%)", 20, 80, int(faixas.get("alta_acima", 42)), 1,
                        key="prem_alta",
                    )

                p1, p2, p3 = st.columns(3)
                with p1:
                    perda_alta = st.slider(
                        "Perda de volume · Alta (%)", 0, 100, int(premissas.get("Alta", 25)), 1,
                        key="prem_perda_alta",
                    )
                with p2:
                    perda_media = st.slider(
                        "Perda de volume · Média (%)", 0, 100, int(premissas.get("Média", 10)), 1,
                        key="prem_perda_media",
                    )
                with p3:
                    perda_baixa = st.slider(
                        "Perda de volume · Baixa (%)", 0, 100, int(premissas.get("Baixa", 0)), 1,
                        key="prem_perda_baixa",
                    )

                salvar_premissas = st.form_submit_button("Aplicar premissas", type="primary")

        if salvar_premissas:
            if baixa_ate >= alta_acima:
                st.error("A faixa de margem baixa precisa terminar antes do início da faixa alta.")
            else:
                novo = copy.deepcopy(cfg)
                novo["teto_padrao"] = int(teto_padrao)
                novo["queda_max_receita"] = int(queda)
                novo["faixas_margem"] = {"baixa_ate": int(baixa_ate), "alta_acima": int(alta_acima)}
                novo["premissas_perda_volume"] = {
                    "Alta": int(perda_alta),
                    "Média": int(perda_media),
                    "Baixa": int(perda_baixa),
                }
                from ui import set_cfg

                set_cfg(novo)
                st.session_state.pop("opt_resultado", None)
                st.session_state.pop("opt_cfg", None)
                st.rerun()

    section("Limites do modelo", "Os parâmetros que delimitam qualquer decisão de desconto")
    p1, p2, p3, p4 = st.columns(4, gap="small")
    with p1:
        metric("Teto padrão", pct(cfg.get("teto_padrao", 0), 0), "quando nenhuma regra se aplica")
    with p2:
        metric("Queda máxima de receita", pct(cfg.get("queda_max_receita", 5), 0), "restrição do otimizador", tone="warning")
    with p3:
        metric("Margem baixa", f"até {pct(faixas.get('baixa_ate', 35), 0)}", "produto de margem enxuta")
    with p4:
        metric("Margem alta", f"> {pct(faixas.get('alta_acima', 42), 0)}", "produto de margem elevada")

    cp1, cp2 = st.columns([1.05, 0.95], gap="small")

    with cp1:
        with st.container(border=True):
            card_head("Perda de volume por perfil", "se o desconto for retirado por completo")
            ordem = ["Baixa", "Média", "Alta"]
            valores = [premissas.get(p, 0) for p in ordem]
            fig = go.Figure(
                go.Bar(
                    x=ordem,
                    y=valores,
                    marker_color=[GREEN, OCHRE, WINE],
                    marker_line_width=0,
                    text=[f"{v}%" for v in valores],
                    textposition="outside",
                    textfont=dict(size=10.5, color=MUTED),
                    hovertemplate="<b>%{x}</b><br>Perda de volume: %{y}%<extra></extra>",
                )
            )
            fig.update_yaxes(range=[0, max(valores) * 1.25 if max(valores) else 10])
            show_fig(fig, height=272, margin=dict(l=42, r=10, t=18, b=4))

    with cp2:
        with st.container(border=True):
            card_head("Faixas de margem", "classificação usada pelas regras")
            baixa = faixas.get("baixa_ate", 0)
            alta = faixas.get("alta_acima", 0)
            st.html(
                f"""
                <div style="display:flex;flex-direction:column;gap:.55rem;padding:.35rem 0 .15rem">
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:.65rem .8rem;border-radius:9px;background:{GREEN}12">
                        <span style="font-size:.76rem;color:{MUTED}">Margem baixa</span>
                        <span style="font-size:.8rem;font-weight:600;color:{GREEN}">&lt; {pct(baixa, 0)}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:.65rem .8rem;border-radius:9px;background:#F3F0E8">
                        <span style="font-size:.76rem;color:{MUTED}">Margem média</span>
                        <span style="font-size:.8rem;font-weight:600;color:{INK}">{pct(baixa, 0)} – {pct(alta, 0)}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:.65rem .8rem;border-radius:9px;background:{WINE}0D">
                        <span style="font-size:.76rem;color:{MUTED}">Margem alta</span>
                        <span style="font-size:.8rem;font-weight:600;color:{WINE}">&gt; {pct(alta, 0)}</span>
                    </div>
                </div>
                """
            )
            st.caption(
                "Tetos avaliados pelo otimizador: " + " · ".join(f"{t}%" for t in TETOS)
            )

    with st.expander("Configuração completa em YAML"):
        st.code(config_para_yaml(cfg), language="yaml")

# ================================================================ TAB 3
with tab_impacto:
    inferencia = aplicar_regras(df, cfg)
    df_r = df.assign(
        teto_regras=inferencia["teto_regras"],
        regra_id=inferencia["regra_id"],
        prioritaria=inferencia["prioritaria"],
    )

    limitadas = int((df_r["desconto_pct"] > df_r["teto_regras"]).sum())
    redutor = df_r.loc[df_r["desconto_pct"] > df_r["teto_regras"], "valor_abatido"].sum()
    teto_medio = df_r["teto_regras"].mean()
    prio = int(df_r["prioritaria"].sum())

    section("Efeito sobre a base real", "O que as regras fariam com as 7.522 vendas históricas")

    i1, i2, i3, i4 = st.columns(4, gap="small")
    with i1:
        metric("Teto médio aplicado", pct(teto_medio), "média ponderada por venda")
    with i2:
        metric(
            "Vendas limitadas",
            num(limitadas),
            f"{pct(limitadas / len(df_r) * 100)} da base",
            tone="warning",
        )
    with i3:
        metric("Desconto evitável", brl(redutor), "excedente acima do teto", tone="negative")
    with i4:
        metric(
            "Vendas sob regra de estoque",
            num(prio),
            f"{pct(prio / len(df_r) * 100)} da base",
        )

    ig1, ig2 = st.columns(2, gap="small")

    with ig1:
        with st.container(border=True):
            card_head("Distribuição por regra", "vendas em que cada regra prevaleceu")
            contagem = df_r["regra_id"].value_counts().reset_index()
            contagem.columns = ["Regra", "Vendas"]
            tipo_por_id = {r.get("id"): r.get("tipo", "comum") for r in regras}
            cores = [WINE if tipo_por_id.get(r) == "prioritaria" else GREEN for r in contagem["Regra"]]
            fig = go.Figure(
                go.Bar(
                    x=contagem["Vendas"],
                    y=contagem["Regra"],
                    orientation="h",
                    marker_color=cores,
                    marker_line_width=0,
                    text=[num(v) for v in contagem["Vendas"]],
                    textposition="outside",
                    textfont=dict(size=10, color=MUTED),
                    cliponaxis=False,
                    hovertemplate="<b>%{y}</b><br>%{x} vendas<extra></extra>",
                )
            )
            fig.update_xaxes(showgrid=False, showticklabels=False)
            fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK))
            show_fig(fig, height=292, margin=dict(l=56, r=54, t=8, b=4))

    with ig2:
        with st.container(border=True):
            card_head("Teto efetivo", "sensibilidade × canal")
            pivot = df_r.pivot_table(
                index="sensibilidade_preco",
                columns="canal",
                values="teto_regras",
                aggfunc="mean",
            ).reindex(index=PERFIS)
            fig = go.Figure(
                go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns,
                    y=pivot.index,
                    colorscale=[
                        [0.0, "#F2EFE6"],
                        [0.35, "#C7D8C7"],
                        [0.7, "#6FA789"],
                        [1.0, "#0E5A3A"],
                    ],
                    text=[[pct(v) for v in row] for row in pivot.values],
                    texttemplate="%{text}",
                    textfont={"size": 10.5, "color": INK},
                    hovertemplate="<b>%{y} · %{x}</b><br>Teto médio: %{z:.1f}%<extra></extra>",
                    colorbar=dict(
                        title=dict(text="%", side="right", font=dict(size=10, color=MUTED)),
                        thickness=8,
                        len=0.6,
                        tickfont=dict(size=9, color=MUTED),
                        outlinewidth=0,
                    ),
                    xgap=2,
                    ygap=2,
                )
            )
            style_fig(fig, height=316, margin=dict(l=64, r=6, t=6, b=30))
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK))
            st.plotly_chart(
                fig,
                use_container_width=True,
                theme=None,
                config={"displayModeBar": False, "responsive": True},
            )

    section("Detalhe por segmento", "Vendas, desconto praticado, teto aplicado e lucro")
    detalhe = (
        df_r.groupby("segmento", as_index=False)
        .agg(
            vendas=("item_id", "count"),
            desconto_medio=("desconto_pct", "mean"),
            teto_medio=("teto_regras", "mean"),
            lucro=("lucro", "sum"),
        )
        .sort_values("vendas", ascending=False)
    )
    detalhe["desconto_medio"] = detalhe["desconto_medio"].map(pct)
    detalhe["teto_medio"] = detalhe["teto_medio"].map(pct)
    detalhe["lucro"] = detalhe["lucro"].map(brl)
    detalhe.columns = ["Segmento", "Vendas", "Desconto médio", "Teto médio", "Lucro"]
    st.dataframe(detalhe, hide_index=True, use_container_width=True, height=350)
