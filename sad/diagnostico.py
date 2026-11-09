"""Diagnóstico estatístico: o desconto muda o volume comprado? (seção 3.3)"""
import pandas as pd
from scipy import stats


def indicadores(df: pd.DataFrame) -> dict:
    com, sem = df[df["tem_desconto"]], df[~df["tem_desconto"]]
    lucro = df["lucro"].sum()
    return {
        "receita": df["receita"].sum(), "lucro": lucro,
        "abatido": df["valor_abatido"].sum(),
        "abatido_pct_lucro": df["valor_abatido"].sum() / lucro * 100 if lucro else 0.0,
        "itens_desconto_pct": df["tem_desconto"].mean() * 100 if len(df) else 0.0,
        "qtd_com": com["quantidade"].mean() if len(com) else float("nan"),
        "qtd_sem": sem["quantidade"].mean() if len(sem) else float("nan"),
        "itens": len(df),
    }


def welch_por_perfil(df: pd.DataFrame) -> pd.DataFrame:
    """Teste t de Welch: quantidade média com vs. sem desconto, por perfil."""
    linhas = []
    for perfil in ["Alta", "Média", "Baixa"]:
        g = df[df["sensibilidade_preco"] == perfil]
        com, sem = g.loc[g["tem_desconto"], "quantidade"], g.loc[~g["tem_desconto"], "quantidade"]
        if len(com) > 1 and len(sem) > 1:
            t, p = stats.ttest_ind(com, sem, equal_var=False)
        else:
            t, p = float("nan"), float("nan")
        linhas.append({"Sensibilidade": perfil, "Itens com desc.": len(com), "Itens sem desc.": len(sem),
                       "Qtd. média com desc.": com.mean(), "Qtd. média sem desc.": sem.mean(),
                       "Estatística t": t, "p-valor": p,
                       "Diferença significativa (5%)": "Sim" if p < 0.05 else "Não"})
    return pd.DataFrame(linhas)


def spearman_desconto_quantidade(df: pd.DataFrame):
    rho, p = stats.spearmanr(df["desconto_pct"], df["quantidade"])
    return float(rho), float(p)


def desconto_por(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    g = df.groupby(coluna).agg(itens=("item_id", "count"), receita=("receita", "sum"), lucro=("lucro", "sum"),
                               abatido=("valor_abatido", "sum"), pct_itens_desc=("tem_desconto", "mean"),
                               qtd_media=("quantidade", "mean")).reset_index()
    g["pct_itens_desc"] *= 100
    g["abatido_pct_total"] = g["abatido"] / g["abatido"].sum() * 100 if g["abatido"].sum() else 0
    return g


def wilcoxon_por_segmento(df: pd.DataFrame, colunas: tuple) -> pd.DataFrame:
    """Teste de Wilcoxon: quantidade com vs. sem desconto, por segmentos múltiplos."""
    linhas = []
    grupos = df.groupby(list(colunas))
    
    for nome_grupo, g in grupos:
        com = g.loc[g["tem_desconto"], "quantidade"]
        sem = g.loc[~g["tem_desconto"], "quantidade"]
        
        # Precisa de pelo menos 2 observações em cada grupo
        if len(com) > 1 and len(sem) > 1:
            try:
                # Wilcoxon rank-sum test (Mann-Whitney U)
                stat, p = stats.mannwhitneyu(com, sem, alternative='two-sided')
            except Exception:
                stat, p = float("nan"), float("nan")
        else:
            stat, p = float("nan"), float("nan")
        
        # Construir linha de resultado
        if isinstance(nome_grupo, tuple):
            resultado = list(nome_grupo)
        else:
            resultado = [nome_grupo]
        
        resultado.extend([
            com.mean(),
            sem.mean(),
            com.mean() - sem.mean(),
            stat,
            p,
            "Sim" if p < 0.05 else "Não"
        ])
        
        linhas.append(resultado)
    
    return pd.DataFrame(linhas)
