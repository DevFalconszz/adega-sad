"""Camada de dados: leitura da planilha e relatório de qualidade."""
import pandas as pd
from .config import ARQ_BASE

ABAS = ["Compras", "Produtos", "Clientes", "Estoque"]


def carregar_base(caminho=ARQ_BASE) -> dict:
    """Lê as quatro abas, convertendo datas e tipos."""
    dfs = pd.read_excel(caminho, sheet_name=ABAS)
    dfs["Compras"]["data_compra"] = pd.to_datetime(dfs["Compras"]["data_compra"])
    for c in ["data_adesao_clube", "data_cancelamento_clube", "cliente_desde"]:
        dfs["Clientes"][c] = pd.to_datetime(dfs["Clientes"][c])
    return dfs


def relatorio_qualidade(dfs: dict) -> pd.DataFrame:
    """Verificações de consistência descritas na seção 3.1 do relatório."""
    c, p, cl, e = dfs["Compras"], dfs["Produtos"], dfs["Clientes"], dfs["Estoque"]
    nulos_cl = cl.isna().sum()
    nulos_cl = nulos_cl[nulos_cl > 0]
    m = c.merge(p[["produto_id", "preco_venda"]], on="produto_id", how="left")
    linhas = [
        ("Valores nulos em Compras, Produtos e Estoque",
         int(c.isna().sum().sum() + p.isna().sum().sum() + e.isna().sum().sum())),
        ("Nulos em Clientes (esperados: datas do clube)",
         "; ".join(f"{k}: {v}" for k, v in nulos_cl.items()) or "Nenhum"),
        ("item_id duplicado", int(c["item_id"].duplicated().sum())),
        ("Compras sem cliente correspondente", int((~c["cliente_id"].isin(cl["cliente_id"])).sum())),
        ("Compras sem produto correspondente", int((~c["produto_id"].isin(p["produto_id"])).sum())),
        ("valor_total ≠ preco_unitario × quantidade",
         int(((c["valor_total"] - c["preco_unitario"] * c["quantidade"]).abs() > 0.011).sum())),
        ("preco_unitario ≠ preco_tabela × (1 − desconto)",
         int(((c["preco_unitario"] - c["preco_tabela"] * (1 - c["desconto_pct"] / 100)).abs() > 0.011).sum())),
        ("preco_tabela ≠ preco_venda do cadastro",
         int(((m["preco_tabela"] - m["preco_venda"]).abs() > 0.011).sum())),
    ]
    return pd.DataFrame(linhas, columns=["Verificação", "Resultado"])
