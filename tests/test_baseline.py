"""Confere os números do relatório técnico (baseline, diagnóstico, cenários)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from sad.config import carregar_config
from sad.data import carregar_base, relatorio_qualidade
from sad.diagnostico import indicadores, spearman_desconto_quantidade, welch_por_perfil
from sad.features import montar_dataset
from sad.optimizer import otimizar
from sad.rules import aplicar_regras
from sad.simulation import resumo, sensibilidade_perda_volume, simular


@pytest.fixture(scope="module")
def dfs():
    return carregar_base()


@pytest.fixture(scope="module")
def df(dfs):
    return montar_dataset(dfs)


@pytest.fixture(scope="module")
def cfg():
    return carregar_config()


@pytest.fixture(scope="module")
def rec(df, cfg):
    return otimizar(df, cfg)


def test_volumes_das_bases(dfs):
    assert len(dfs["Compras"]) == 7522 and len(dfs["Produtos"]) == 180
    assert len(dfs["Clientes"]) == 600 and len(dfs["Estoque"]) == 180


def test_qualidade_sem_inconsistencias(dfs):
    q = relatorio_qualidade(dfs).set_index("Verificação")["Resultado"]
    assert q["Valores nulos em Compras, Produtos e Estoque"] == 0
    assert q["item_id duplicado"] == 0
    assert q["valor_total ≠ preco_unitario × quantidade"] == 0
    assert q["preco_tabela ≠ preco_venda do cadastro"] == 0


def test_baseline(df):
    k = indicadores(df)
    assert round(k["receita"]) == 1_146_077
    assert round(k["lucro"]) == 396_510
    assert round(k["abatido"]) == 61_029
    assert round(k["itens_desconto_pct"]) == 47
    assert round(k["qtd_com"], 2) == 1.91 and round(k["qtd_sem"], 2) == 1.89
    assert round(k["abatido_pct_lucro"]) == 15


def test_desconto_baixa_sensibilidade(df):
    b = df[df["sensibilidade_preco"] == "Baixa"]["valor_abatido"].sum()
    assert round(b) == 24_226


def test_welch_e_spearman(df):
    w = welch_por_perfil(df).set_index("Sensibilidade")["p-valor"]
    assert round(w["Alta"], 2) == 0.81 and round(w["Média"], 2) == 0.62 and round(w["Baixa"], 2) == 0.33
    rho, _ = spearman_desconto_quantidade(df)
    assert round(rho, 3) == 0.006


def test_27_segmentos(df):
    assert df["segmento"].nunique() == 27


def test_regras_padrao(df, cfg):
    r = aplicar_regras(df, cfg)
    res = resumo(df, simular(df, r["teto_regras"].to_numpy(), cfg["premissas_perda_volume"]))
    assert round(res["lucro"]) == 425_539
    assert round(res["receita"]) == 1_163_140
    assert round(res["abatido"]) == 25_466
    assert round(res["unidades"]) == 14_099


def test_recomendacao(df, rec):
    res = resumo(df, rec["sim"])
    assert round(res["lucro"]) == 431_012
    assert round(res["receita"]) == 1_157_785
    assert round(res["abatido"]) == 12_820
    assert round(res["unidades"]) == 13_880
    assert not rec["ajustes"]  # restrição de receita não acionada


def test_recomendacao_por_perfil(rec):
    t = rec["tabela"].groupby("perfil")["diferenca"].sum()
    assert round(t["Baixa"]) == 21_226 and round(t["Média"]) == 9_652 and round(t["Alta"]) == 3_624
    tab = rec["tabela"]
    assert (tab[tab["perfil"].isin(["Baixa", "Média"])]["teto_recomendado_%"] == 0).all()
    assert tab[tab["perfil"] == "Alta"]["teto_recomendado_%"].max() == 5
    x = tab[(tab["perfil"] == "Alta") & (tab["faixa_margem"] == "Baixa") & (tab["canal"] == "Loja física")]
    assert x["teto_recomendado_%"].iloc[0] == 0


def test_regras_de_estoque_prevalecem(df, cfg):
    r = aplicar_regras(df, cfg)
    abaixo = df["situacao_estoque"] == "Abaixo do mínimo"
    excesso = df["situacao_estoque"] == "Excesso"
    assert (r.loc[abaixo, "teto_regras"] == 0).all() and (r.loc[abaixo, "regra_id"] == "R5").all()
    assert (r.loc[excesso, "teto_regras"] == 20).all() and (r.loc[excesso, "regra_id"] == "R4").all()


def test_desconto_nunca_aumenta(df, rec):
    assert (rec["sim"]["desconto_novo"] <= df["desconto_pct"] + 1e-9).all()


def test_restricao_de_receita_acionada(df, cfg):
    cfg2 = {**cfg, "queda_max_receita": -10.0}  # exige +10% de receita: inatingível -> teto sobe
    r = otimizar(df, cfg2)
    assert len(r["ajustes"]) > 0


def test_breakeven_politica_recomendada(df, rec):
    _, be = sensibilidade_perda_volume(df, rec["teto_final_venda"])
    assert 28 < be < 31
