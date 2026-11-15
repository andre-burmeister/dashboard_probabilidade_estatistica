"""Extrai a população de cursos presenciais do Censo da Educação Superior 2024."""

from pathlib import Path
import json

import pandas as pd

RAIZ = Path(__file__).resolve().parent
CAMINHO_CSV = (
    RAIZ
    / "brazil_university_dropouts_data_analysis"
    / "dados"
    / "microdados_censo_da_educacao_superior_2024"
    / "dados"
    / "MICRODADOS_CADASTRO_CURSOS_2024.CSV"
)
CAMINHO_PARQUET = RAIZ / "dados" / "populacao_cursos_presenciais_2024.parquet"
CAMINHO_METADADOS = RAIZ / "dados" / "metadados.json"

COLUNAS_CSV = [
    "NO_MUNICIPIO",
    "SG_UF",
    "NO_UF",
    "IN_CAPITAL",
    "TP_MODALIDADE_ENSINO",
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_REDE",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "IN_GRATUITO",
    "CO_IES",
    "NO_CURSO",
    "CO_CURSO",
    "NO_CINE_AREA_GERAL",
    "TP_GRAU_ACADEMICO",
    "QT_MAT",
    "QT_VG_TOTAL",
    "QT_INSCRITO_TOTAL",
]

ORGANIZACAO = {
    1: "Universidade",
    2: "Centro universitário",
    3: "Faculdade",
    4: "Instituto Federal",
    5: "Centro Federal de Educação Tecnológica",
}
CATEGORIA = {
    1: "Pública federal",
    2: "Pública estadual",
    3: "Pública municipal",
    4: "Privada com fins lucrativos",
    5: "Privada sem fins lucrativos",
    7: "Especial",
}
REDE = {1: "Pública", 2: "Privada"}
GRAU = {1: "Bacharelado", 2: "Licenciatura", 3: "Tecnológico"}
GRATUIDADE = {0: "Pago", 1: "Gratuito"}
LOCAL = {0: "Fora da capital", 1: "Capital"}


def _rotulo(serie, mapa):
    return serie.map(mapa).fillna("Não informado")


def preparar():
    """Lê o CSV do Inep, filtra a população e grava o parquet."""
    if not CAMINHO_CSV.exists():
        raise FileNotFoundError(f"CSV do Censo não encontrado: {CAMINHO_CSV}")

    cabecalho = pd.read_csv(CAMINHO_CSV, sep=";", encoding="latin-1", nrows=0)
    bruto = pd.read_csv(
        CAMINHO_CSV,
        sep=";",
        encoding="latin-1",
        usecols=COLUNAS_CSV,
        low_memory=False,
    )
    presencial = (
        bruto["TP_MODALIDADE_ENSINO"].eq(1)
        & bruto["QT_MAT"].gt(0)
        & bruto["QT_VG_TOTAL"].gt(0)
    )
    populacao = bruto.loc[presencial].copy()
    if populacao["CO_CURSO"].duplicated().any():
        raise ValueError("Há curso presencial repetido. A unidade amostral deixaria de ser o curso.")
    if populacao["IN_CAPITAL"].isna().any():
        raise ValueError("Há curso presencial sem o indicador de capital.")

    populacao["QT_INSCRITO_TOTAL"] = populacao["QT_INSCRITO_TOTAL"].fillna(0)
    populacao["inscritos_por_vaga"] = (
        populacao["QT_INSCRITO_TOTAL"] / populacao["QT_VG_TOTAL"]
    )
    populacao["licenciatura"] = populacao["TP_GRAU_ACADEMICO"].eq(2)
    populacao["gratuito"] = populacao["IN_GRATUITO"].eq(1)
    populacao["categoria"] = _rotulo(populacao["TP_CATEGORIA_ADMINISTRATIVA"], CATEGORIA)
    populacao["organizacao"] = _rotulo(populacao["TP_ORGANIZACAO_ACADEMICA"], ORGANIZACAO)
    populacao["rede"] = _rotulo(populacao["TP_REDE"], REDE)
    populacao["grau"] = _rotulo(populacao["TP_GRAU_ACADEMICO"], GRAU)
    populacao["gratuidade"] = _rotulo(populacao["IN_GRATUITO"], GRATUIDADE)
    populacao["local"] = _rotulo(populacao["IN_CAPITAL"], LOCAL)
    populacao["area"] = populacao["NO_CINE_AREA_GERAL"].fillna("Sem área")

    colunas = [
        "CO_CURSO",
        "NO_CURSO",
        "CO_IES",
        "NO_MUNICIPIO",
        "SG_UF",
        "NO_UF",
        "categoria",
        "organizacao",
        "rede",
        "gratuidade",
        "grau",
        "area",
        "local",
        "licenciatura",
        "gratuito",
        "QT_MAT",
        "QT_VG_TOTAL",
        "QT_INSCRITO_TOTAL",
        "inscritos_por_vaga",
    ]
    populacao = populacao[colunas].reset_index(drop=True)
    CAMINHO_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    populacao.to_parquet(CAMINHO_PARQUET, index=False)
    metadados = {
        "arquivo": CAMINHO_CSV.name,
        "n_linhas_arquivo": int(len(bruto)),
        "n_colunas_arquivo": int(len(cabecalho.columns)),
        "n_populacao": int(len(populacao)),
        "n_variaveis_estudo": int(len(populacao.columns)),
    }
    CAMINHO_METADADOS.write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return populacao, metadados


if __name__ == "__main__":
    cursos, metadados = preparar()
    print(json.dumps(metadados, ensure_ascii=False))
    print(
        "licenciatura",
        round(float(cursos["licenciatura"].mean()), 4),
        "gratuito",
        round(float(cursos["gratuito"].mean()), 4),
        "matriculas",
        round(float(cursos["QT_MAT"].mean()), 2),
        "inscritos_por_vaga",
        round(float(cursos["inscritos_por_vaga"].mean()), 3),
    )
