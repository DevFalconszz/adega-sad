"""Base de conhecimento: regras SE -> ENTÃO e mecanismo de inferência.

Entre as regras comuns que se aplicam vale a mais restritiva (menor teto);
as regras prioritárias (estoque) prevalecem sobre todas.
"""
import numpy as np
import pandas as pd

CAMPOS = {"sensibilidade_preco": "Sensibilidade a preço do cliente",
          "faixa_margem": "Faixa de margem do produto",
          "situacao_estoque": "Situação de estoque",
          "canal": "Canal de venda"}


def validar_regras(regras: list) -> list:
    erros, ids = [], set()
    for r in regras:
        if r["id"] in ids:
            erros.append(f"ID de regra duplicado: {r['id']}")
        ids.add(r["id"])
        if r["campo"] not in CAMPOS:
            erros.append(f"{r['id']}: campo inválido '{r['campo']}'")
        if not 0 <= r["teto"] <= 100:
            erros.append(f"{r['id']}: teto fora de 0–100")
        if r["tipo"] not in ("comum", "prioritaria"):
            erros.append(f"{r['id']}: tipo deve ser comum ou prioritaria")
    return erros


def aplicar_regras(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Devolve, por venda: teto_regras, regra_id, prioritaria (bool), teto_comum."""
    n = len(df)
    padrao = float(cfg["teto_padrao"])
    teto_comum = np.full(n, np.inf)
    id_comum = np.array([""] * n, dtype=object)
    teto_prio = np.full(n, np.nan)
    id_prio = np.array([""] * n, dtype=object)
    for r in cfg["regras"]:
        if not r.get("ativa", True):
            continue
        casa = (df[r["campo"]].astype(str) == str(r["valor"])).to_numpy()
        if r["tipo"] == "comum":
            melhor = casa & (r["teto"] < teto_comum)
            teto_comum[melhor] = r["teto"]
            id_comum[melhor] = r["id"]
        else:  # prioritária: em conflito, vale a mais restritiva entre as prioritárias
            melhor = casa & (np.isnan(teto_prio) | (r["teto"] < teto_prio))
            teto_prio[melhor] = r["teto"]
            id_prio[melhor] = r["id"]
    sem_comum = np.isinf(teto_comum)
    teto_comum_final = np.where(sem_comum, padrao, teto_comum)
    id_comum_final = np.where(sem_comum, "Padrão", id_comum)
    tem_prio = ~np.isnan(teto_prio)
    return pd.DataFrame({
        "teto_comum": teto_comum_final,
        "regra_comum": id_comum_final,
        "teto_prio": teto_prio,
        "regra_prio": id_prio,
        "prioritaria": tem_prio,
        "teto_regras": np.where(tem_prio, teto_prio, teto_comum_final),
        "regra_id": np.where(tem_prio, id_prio, id_comum_final),
    }, index=df.index)
