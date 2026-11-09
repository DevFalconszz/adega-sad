"""Modelo de simulação what-if (seção 4.3 do relatório)."""
import numpy as np
import pandas as pd


def simular(df: pd.DataFrame, teto, premissas: dict) -> pd.DataFrame:
    """Reprocessa cada venda sob um teto de desconto (escalar ou vetor por venda).

    d_novo = min(d_original, teto)
    q_esp  = q * (1 - (d_orig - d_novo)/d_orig * P_perfil/100)
    lucro  = (p_tabela*(1 - d_novo) - custo) * q_esp
    """
    d0 = df["desconto_pct"].to_numpy(float)
    d1 = np.minimum(d0, teto) if teto is not None else d0.copy()
    P = df["sensibilidade_preco"].map(premissas).to_numpy(float)
    reducao = np.divide(d0 - d1, d0, out=np.zeros_like(d0), where=d0 > 0)
    q = df["quantidade"].to_numpy(float)
    q_esp = q * (1 - reducao * P / 100)
    preco = df["preco_tabela"].to_numpy(float) * (1 - d1 / 100)
    out = pd.DataFrame(index=df.index)
    out["desconto_novo"] = d1
    out["qtd_esperada"] = q_esp
    out["receita_sim"] = preco * q_esp
    out["lucro_sim"] = (preco - df["custo_unitario"].to_numpy(float)) * q_esp
    out["abatido_sim"] = (df["preco_tabela"].to_numpy(float) - preco) * q_esp
    return out


def resumo(df: pd.DataFrame, sim: pd.DataFrame | None = None) -> dict:
    """Indicadores totais. Sem `sim`, usa o histórico real (política atual)."""
    if sim is None:
        return {"lucro": df["lucro"].sum(), "receita": df["receita"].sum(),
                "abatido": df["valor_abatido"].sum(), "unidades": float(df["quantidade"].sum())}
    return {"lucro": sim["lucro_sim"].sum(), "receita": sim["receita_sim"].sum(),
            "abatido": sim["abatido_sim"].sum(), "unidades": sim["qtd_esperada"].sum()}


def sensibilidade_perda_volume(df: pd.DataFrame, teto, passo=1, maximo=100):
    """Lucro da política proposta quando TODOS os perfis perdem P% do volume
    ao ter o desconto retirado. Retorna (tabela, ponto de break-even em %)."""
    base = df["lucro"].sum()
    linhas = []
    for p in range(0, maximo + 1, passo):
        s = simular(df, teto, {"Alta": p, "Média": p, "Baixa": p})
        linhas.append((p, s["lucro_sim"].sum(), base))
    t = pd.DataFrame(linhas, columns=["perda_volume_pct", "lucro_politica", "lucro_atual"])
    pior = t[t["lucro_politica"] < t["lucro_atual"]]
    if pior.empty:
        return t, None
    p2 = pior.iloc[0]
    ant = t.iloc[max(pior.index[0] - 1, 0)]
    a, b = ant["lucro_politica"] - ant["lucro_atual"], p2["lucro_politica"] - p2["lucro_atual"]
    be = ant["perda_volume_pct"] + (a / (a - b)) * passo if a != b else p2["perda_volume_pct"]
    return t, float(be)
