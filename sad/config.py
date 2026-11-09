"""Leitura/gravação da base de regras e premissas (YAML)."""
from pathlib import Path
import copy
import yaml

RAIZ = Path(__file__).resolve().parent.parent
ARQ_REGRAS = RAIZ / "config" / "regras.yaml"
ARQ_BASE = RAIZ / "data" / "Base_Adega_Bom_Sabor_2026.xlsx"

TETOS = [0, 5, 10, 15, 20]
PERFIS = ["Baixa", "Média", "Alta"]
FAIXAS = ["Baixa", "Média", "Alta"]
CANAIS = ["E-commerce", "Loja física", "Clube de assinatura"]


def carregar_config(caminho=ARQ_REGRAS) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


def config_para_yaml(cfg: dict) -> str:
    return yaml.safe_dump(copy.deepcopy(cfg), allow_unicode=True, sort_keys=False)


def salvar_config(cfg: dict, caminho=ARQ_REGRAS) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(config_para_yaml(cfg))
