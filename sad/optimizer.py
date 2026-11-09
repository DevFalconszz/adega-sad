"""Otimização do teto de desconto por segmento (seção 4.4 do relatório)."""
import numpy as np
import pandas as pd
from .config import TETOS
from .rules import aplicar_regras
from .simulation import simular


def teto_efetivo(regras_df: pd.DataFrame, teto_segmento) -> np.ndarray:
    """Teto final por venda: regra prioritária de estoque prevalece; senão vale
    o mais restritivo entre a regra comum e o teto escolhido para o segmento."""
    comum = np.minimum(regras_df["teto_comum"].to_numpy(), teto_segmento)
    return np.where(regras_df["prioritaria"], regras_df["teto_prio"].fillna(0).to_numpy(), comum)


def otimizar(df: pd.DataFrame, cfg: dict) -> dict:
    premissas = cfg["premissas_perda_volume"]
    queda_max = cfg["queda_max_receita"] / 100
    regras_df = aplicar_regras(df, cfg)
    seg = df["segmento"].to_numpy()
    segmentos = sorted(set(seg))
    idx = {s: np.where(seg == s)[0] for s in segmentos}

    # Lucro/receita de cada segmento para cada teto candidato
    lucro = {s: {} for s in segmentos}
    receita = {s: {} for s in segmentos}
    for t in TETOS:
        sim = simular(df, teto_efetivo(regras_df, t), premissas)
        for s in segmentos:
            lucro[s][t] = sim["lucro_sim"].to_numpy()[idx[s]].sum()
            receita[s][t] = sim["receita_sim"].to_numpy()[idx[s]].sum()

    escolha = {s: max(TETOS, key=lambda t: (round(lucro[s][t], 6), -t)) for s in segmentos}
    receita_base = df["receita"].sum()
    base_seg = df.groupby("segmento")["receita"].sum().to_dict()
    ajustes = []

    def receita_total():
        return sum(receita[s][escolha[s]] for s in segmentos)

    while receita_total() < (1 - queda_max) * receita_base:
        cand = []
        for s in segmentos:
            i = TETOS.index(escolha[s])
            if i + 1 < len(TETOS) and receita[s][TETOS[i + 1]] > receita[s][escolha[s]]:
                cand.append((base_seg[s] - receita[s][escolha[s]], s))
        if not cand:
            break
        _, s = max(cand)
        escolha[s] = TETOS[TETOS.index(escolha[s]) + 1]
        ajustes.append(s)

    teto_seg_venda = np.array([escolha[s] for s in seg], dtype=float)
    final = teto_efetivo(regras_df, teto_seg_venda)
    sim = simular(df, final, premissas)

    ids_prio = [r["id"] for r in cfg["regras"] if r["tipo"] == "prioritaria"]
    d = df.assign(**sim, regra_id=regras_df["regra_id"], teto_final=final)
    linhas = []
    for s in segmentos:
        g = d.iloc[idx[s]]
        regra_dom = g["regra_id"].value_counts().index[0]
        t = escolha[s]
        just = (f"Teto {t}% maximiza o lucro esperado do segmento"
                if s not in ajustes else f"Teto {t}% (elevado para cumprir a queda máxima de receita)")
        just += f"; regra predominante: {regra_dom}"
        n_prio = int(g["regra_id"].isin(ids_prio).sum())
        if n_prio:
            just += f"; regras de estoque atuam em {n_prio} vendas"
        linhas.append({
            "segmento": s,
            "perfil": g["sensibilidade_preco"].iloc[0], "faixa_margem": g["faixa_margem"].iloc[0],
            "canal": g["canal"].iloc[0], "vendas": len(g),
            "desconto_medio_atual_%": round((g["valor_abatido"].sum() / (g["preco_tabela"] * g["quantidade"]).sum()) * 100, 2),
            "teto_recomendado_%": t,
            "lucro_atual": g["lucro"].sum(), "lucro_esperado": g["lucro_sim"].sum(),
            "diferenca": g["lucro_sim"].sum() - g["lucro"].sum(),
            "receita_atual": g["receita"].sum(), "receita_esperada": g["receita_sim"].sum(),
            "regra_predominante": regra_dom, "justificativa": just,
        })
    return {"tabela": pd.DataFrame(linhas), "tetos": escolha, "teto_final_venda": final,
            "sim": sim, "regras": regras_df, "ajustes": ajustes}
