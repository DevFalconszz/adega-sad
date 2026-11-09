"""Integração das bases e colunas derivadas (seção 3.2 do relatório)."""
import numpy as np
import pandas as pd


def faixa_margem(margem_pct, baixa_ate=35, alta_acima=42):
    return np.select([margem_pct < baixa_ate, margem_pct > alta_acima], ["Baixa", "Alta"], default="Média")


def situacao_estoque(atual, minimo, maximo):
    return np.select([atual < minimo, atual > maximo], ["Abaixo do mínimo", "Excesso"], default="Normal")


def montar_dataset(dfs: dict, baixa_ate=35, alta_acima=42) -> pd.DataFrame:
    """Uma linha por item vendido, com custo, perfil, estoque e métricas."""
    c, p, cl, e = dfs["Compras"], dfs["Produtos"], dfs["Clientes"], dfs["Estoque"]
    df = (c.merge(p[["produto_id", "nome_produto", "tipo", "custo_unitario", "preco_venda", "margem_pct"]],
                  on="produto_id", how="left")
           .merge(cl[["cliente_id", "sensibilidade_preco"]], on="cliente_id", how="left")
           .merge(e[["produto_id", "estoque_atual", "estoque_minimo", "estoque_maximo"]],
                  on="produto_id", how="left"))
    df["receita"] = df["valor_total"]
    # Preço efetivo = preço de tabela x (1 - desconto), igual ao usado na simulação
    # (a base arredonda preco_unitario em centavos; a diferença total é < R$ 1).
    preco_efetivo = df["preco_tabela"] * (1 - df["desconto_pct"] / 100)
    df["valor_abatido"] = (df["preco_tabela"] - preco_efetivo) * df["quantidade"]
    df["lucro"] = (preco_efetivo - df["custo_unitario"]) * df["quantidade"]
    df["margem_tabela"] = (df["preco_tabela"] - df["custo_unitario"]) / df["preco_tabela"] * 100
    df["tem_desconto"] = df["desconto_pct"] > 0
    df = reclassificar(df, baixa_ate, alta_acima)
    df["ano_mes"] = df["data_compra"].dt.to_period("M").dt.to_timestamp()
    return df


def reclassificar(df: pd.DataFrame, baixa_ate=35, alta_acima=42) -> pd.DataFrame:
    """Recalcula faixa de margem, situação de estoque e segmento (27 segmentos)."""
    df = df.copy()
    df["faixa_margem"] = faixa_margem(df["margem_pct"], baixa_ate, alta_acima)
    df["situacao_estoque"] = situacao_estoque(df["estoque_atual"], df["estoque_minimo"], df["estoque_maximo"])
    df["segmento"] = df["sensibilidade_preco"] + " | margem " + df["faixa_margem"] + " | " + df["canal"]
    return df
