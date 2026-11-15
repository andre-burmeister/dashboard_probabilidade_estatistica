"""Tamanho amostral, amostra aleatória simples e inferência para proporção e média."""

from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy import stats

import preparar_dados

CONFIANCA = 0.95
Z = float(stats.norm.ppf((1 + CONFIANCA) / 2))
ERRO = 0.02
P_PLANEJAMENTO = 0.50
SEMENTE = 2024
ALPHA = 0.05
VALOR_NULO = 0.50

FONTE_NOME = "Censo da Educação Superior 2024"
FONTE_URL = (
    "https://www.gov.br/inep/pt-br/areas-de-atuacao/"
    "pesquisas-estatisticas-e-indicadores/censo-da-educacao-superior"
)

HIPOTESES = [
    {
        "id": "licenciatura",
        "coluna": "licenciatura",
        "tipo": "proporcao",
        "nome": "Licenciatura",
        "pergunta": "A proporção de cursos de licenciatura é 50%?",
        "justificativa": (
            "A hipótese nula divide a oferta ao meio entre licenciaturas e os "
            "demais graus, bacharelado e tecnológico. A alternativa é bilateral."
        ),
        "valor_nulo": 0.50,
        "h0": r"$p = 0{,}50$",
        "h1": r"$p \neq 0{,}50$",
        "texto_nulo": "50%",
        "percentual": True,
        "casas": 2,
        "unidade": "",
    },
    {
        "id": "gratuito",
        "coluna": "gratuito",
        "tipo": "proporcao",
        "nome": "Curso gratuito",
        "pergunta": "A proporção de cursos gratuitos é 50%?",
        "justificativa": (
            "A hipótese nula divide a oferta ao meio entre cursos gratuitos e pagos. "
            "A alternativa é bilateral."
        ),
        "valor_nulo": 0.50,
        "h0": r"$p = 0{,}50$",
        "h1": r"$p \neq 0{,}50$",
        "texto_nulo": "50%",
        "percentual": True,
        "casas": 2,
        "unidade": "",
    },
    {
        "id": "matriculas",
        "coluna": "QT_MAT",
        "tipo": "media",
        "nome": "Matrículas no curso",
        "pergunta": "O curso presencial tem, em média, 100 matrículas?",
        "justificativa": (
            "Cem matrículas é uma referência redonda, próxima da mediana. "
            "A hipótese pergunta se a média, sensível aos cursos grandes, fica nesse patamar. "
            "A alternativa é bilateral."
        ),
        "valor_nulo": 100,
        "h0": r"$\mu = 100$",
        "h1": r"$\mu \neq 100$",
        "texto_nulo": "100 matrículas",
        "percentual": False,
        "casas": 1,
        "unidade": "matrículas",
    },
    {
        "id": "inscritos_por_vaga",
        "coluna": "inscritos_por_vaga",
        "tipo": "media",
        "nome": "Inscritos por vaga",
        "pergunta": "Há, em média, 1 inscrito por vaga?",
        "justificativa": (
            "Um inscrito por vaga é o equilíbrio entre a procura e a oferta do curso. "
            "A média usa os inscritos divididos pelas vagas de cada curso. "
            "A alternativa é bilateral."
        ),
        "valor_nulo": 1,
        "h0": r"$\mu = 1$",
        "h1": r"$\mu \neq 1$",
        "texto_nulo": "1 inscrito por vaga",
        "percentual": False,
        "casas": 2,
        "unidade": "inscritos por vaga",
    },
]

QUALITATIVAS = [
    ("categoria", "Categoria administrativa"),
    ("organizacao", "Organização acadêmica"),
    ("rede", "Rede"),
    ("gratuidade", "Gratuidade"),
    ("grau", "Grau acadêmico"),
    ("area", "Área do conhecimento"),
    ("local", "Localização"),
    ("NO_UF", "Unidade federativa"),
]

QUANTITATIVAS = [
    {"coluna": "QT_MAT", "nome": "Matrículas no curso", "casas": 1, "casas_mediana": 0},
    {"coluna": "inscritos_por_vaga", "nome": "Inscritos por vaga", "casas": 2, "casas_mediana": 2},
]


def carregar_populacao():
    """Devolve a população e os metadados do arquivo original."""
    if not preparar_dados.CAMINHO_PARQUET.exists():
        preparar_dados.preparar()
    populacao = pd.read_parquet(preparar_dados.CAMINHO_PARQUET)
    metadados = json.loads(
        Path(preparar_dados.CAMINHO_METADADOS).read_text(encoding="utf-8")
    )
    return populacao, metadados


def tamanho_amostral(tamanho_populacao, z=Z, erro=ERRO, proporcao=P_PLANEJAMENTO):
    """Tamanho de amostra para proporção, com correção de população finita.

    n0 = z² p (1 − p) / E²
    n = n0 / (1 + (n0 − 1) / N), arredondado para cima.
    """
    n0 = z**2 * proporcao * (1 - proporcao) / erro**2
    n = int(np.ceil(n0 / (1 + (n0 - 1) / tamanho_populacao)))
    n = min(n, int(tamanho_populacao))
    return {
        "N": int(tamanho_populacao),
        "confianca": CONFIANCA,
        "z": float(z),
        "erro": float(erro),
        "p": float(proporcao),
        "alpha": ALPHA,
        "n0": float(n0),
        "n": n,
        "semente": SEMENTE,
    }


def fator_finito(tamanho_populacao, tamanho_amostra):
    """sqrt((N − n) / (N − 1)), a correção do erro-padrão."""
    return float(
        np.sqrt((tamanho_populacao - tamanho_amostra) / (tamanho_populacao - 1))
    )


def amostrar(populacao, tamanho, semente=SEMENTE):
    """Amostra aleatória simples, sem reposição. Cada curso tem a mesma chance."""
    gerador = np.random.default_rng(semente)
    indices = gerador.choice(len(populacao), size=tamanho, replace=False)
    return populacao.iloc[np.sort(indices)].reset_index(drop=True)


def frequencia(dados, coluna):
    contagem = dados[coluna].value_counts(dropna=False)
    tabela = contagem.rename_axis(coluna).reset_index(name="cursos")
    tabela["proporcao"] = tabela["cursos"] / len(dados)
    return tabela.sort_values(["proporcao", coluna], ascending=[False, True])


def medidas(dados, coluna):
    serie = dados[coluna].astype(float)
    return {
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "desvio": float(serie.std(ddof=1)),
        "minimo": float(serie.min()),
        "maximo": float(serie.max()),
        "assimetria": float(serie.skew()),
    }


def _decisao(parametro, valor_nulo, valor_p, alpha, texto_nulo):
    populacao_difere = abs(parametro - valor_nulo) > 1e-9
    rejeita = valor_p < alpha
    if populacao_difere and rejeita:
        acordo = (
            f"A população também difere de {texto_nulo}. "
            "A decisão do teste coincide com o parâmetro populacional."
        )
    elif populacao_difere and not rejeita:
        acordo = (
            f"A população difere de {texto_nulo}, mas esta amostra não rejeitou $H_0$. "
            "A diferença ficou dentro da variabilidade amostral."
        )
    elif not populacao_difere and rejeita:
        acordo = (
            f"Na população o parâmetro é {texto_nulo} e o teste rejeitou $H_0$. "
            "Esta amostra produziu um falso positivo."
        )
    else:
        acordo = f"Na população o parâmetro é {texto_nulo} e o teste não rejeitou $H_0$."
    return rejeita, acordo


def inferir_proporcao(populacao, amostra, coluna, valor_nulo=VALOR_NULO, alpha=ALPHA, z=Z, texto_nulo="50%"):
    """Intervalo de Wald e teste z bilateral, com população finita."""
    tamanho_populacao = len(populacao)
    tamanho_amostra = len(amostra)
    sucessos = int(amostra[coluna].sum())
    estimativa = sucessos / tamanho_amostra
    parametro = float(populacao[coluna].mean())
    fpc = fator_finito(tamanho_populacao, tamanho_amostra)
    erro_padrao = float(np.sqrt(estimativa * (1 - estimativa) / tamanho_amostra) * fpc)
    erro_padrao_h0 = float(np.sqrt(valor_nulo * (1 - valor_nulo) / tamanho_amostra) * fpc)
    inferior = estimativa - z * erro_padrao
    superior = estimativa + z * erro_padrao
    estatistica = (estimativa - valor_nulo) / erro_padrao_h0
    valor_p = float(min(1.0, 2 * stats.norm.sf(abs(estatistica))))
    rejeita, acordo = _decisao(parametro, valor_nulo, valor_p, alpha, texto_nulo)
    n_p = tamanho_amostra * estimativa
    n_q = tamanho_amostra * (1 - estimativa)
    n_p0 = tamanho_amostra * valor_nulo
    condicoes_ok = n_p >= 10 and n_q >= 10 and n_p0 >= 10
    return {
        "tipo": "proporcao",
        "coluna": coluna,
        "parametro": parametro,
        "estimativa": float(estimativa),
        "inferior": float(inferior),
        "superior": float(superior),
        "erro_padrao": erro_padrao,
        "erro_padrao_h0": erro_padrao_h0,
        "estatistica_nome": "z",
        "estatistica": float(estatistica),
        "valor_p": valor_p,
        "alpha": alpha,
        "critico": z,
        "rejeita": rejeita,
        "acordo": acordo,
        "cobre": bool(inferior <= parametro <= superior),
        "fpc": fpc,
        "sucessos": sucessos,
        "n": tamanho_amostra,
        "N": tamanho_populacao,
        "graus_liberdade": None,
        "desvio": None,
        "condicoes_ok": condicoes_ok,
        "condicoes": (
            fr"A aproximação normal usa $n\hat{{p}}$ = {formatar_inteiro(n_p)}, "
            fr"$n(1-\hat{{p}})$ = {formatar_inteiro(n_q)} "
            fr"e, sob $H_0$, $np_0$ = {formatar_inteiro(n_p0)}. "
            + (
                "Os três valores passam de 10."
                if condicoes_ok
                else "Algum produto fica abaixo de 10, e a aproximação fica frágil."
            )
        ),
    }


def inferir_media(populacao, amostra, coluna, valor_nulo=VALOR_NULO, alpha=ALPHA, texto_nulo=""):
    """Intervalo t e teste t bilateral, com população finita no erro-padrão."""
    tamanho_populacao = len(populacao)
    valores = amostra[coluna].to_numpy(dtype=float)
    tamanho_amostra = len(valores)
    estimativa = float(valores.mean())
    desvio = float(valores.std(ddof=1))
    parametro = float(populacao[coluna].mean())
    fpc = fator_finito(tamanho_populacao, tamanho_amostra)
    graus = tamanho_amostra - 1
    erro_padrao = float(desvio / np.sqrt(tamanho_amostra) * fpc)
    critico = float(stats.t.ppf(1 - alpha / 2, graus))
    inferior = estimativa - critico * erro_padrao
    superior = estimativa + critico * erro_padrao
    estatistica = (estimativa - valor_nulo) / erro_padrao
    valor_p = float(min(1.0, 2 * stats.t.sf(abs(estatistica), graus)))
    rejeita, acordo = _decisao(parametro, valor_nulo, valor_p, alpha, texto_nulo)
    assimetria = float(pd.Series(valores).skew())
    return {
        "tipo": "media",
        "coluna": coluna,
        "parametro": parametro,
        "estimativa": estimativa,
        "inferior": float(inferior),
        "superior": float(superior),
        "erro_padrao": erro_padrao,
        "erro_padrao_h0": erro_padrao,
        "estatistica_nome": "t",
        "estatistica": float(estatistica),
        "valor_p": valor_p,
        "alpha": alpha,
        "critico": critico,
        "rejeita": rejeita,
        "acordo": acordo,
        "cobre": bool(inferior <= parametro <= superior),
        "fpc": fpc,
        "sucessos": None,
        "n": tamanho_amostra,
        "N": tamanho_populacao,
        "graus_liberdade": graus,
        "desvio": desvio,
        "condicoes_ok": tamanho_amostra >= 30,
        "condicoes": (
            f"A amostra tem {formatar_inteiro(tamanho_amostra)} cursos e a assimetria amostral é "
            f"{formatar_decimal(assimetria, 2)}. "
            "Com esse tamanho, a média amostral se aproxima da normal e o intervalo $t$ se aplica. "
            "Se a assimetria é alta, a média fica acima da mediana."
        ),
    }


def inferir(populacao, amostra):
    """As quatro inferências do trabalho, na ordem das hipóteses."""
    resultados = []
    for hipotese in HIPOTESES:
        if hipotese["tipo"] == "proporcao":
            resultado = inferir_proporcao(
                populacao,
                amostra,
                hipotese["coluna"],
                valor_nulo=hipotese["valor_nulo"],
                texto_nulo=hipotese["texto_nulo"],
            )
        else:
            resultado = inferir_media(
                populacao,
                amostra,
                hipotese["coluna"],
                valor_nulo=hipotese["valor_nulo"],
                texto_nulo=hipotese["texto_nulo"],
            )
        resultado.update(
            {
                "id": hipotese["id"],
                "nome": hipotese["nome"],
                "pergunta": hipotese["pergunta"],
                "justificativa": hipotese["justificativa"],
                "h0": hipotese["h0"],
                "h1": hipotese["h1"],
                "valor_nulo": hipotese["valor_nulo"],
                "texto_nulo": hipotese["texto_nulo"],
                "percentual": hipotese["percentual"],
                "casas": hipotese["casas"],
                "unidade": hipotese["unidade"],
            }
        )
        resultados.append(resultado)
    return resultados


def formatar_inteiro(valor):
    return f"{int(round(valor)):,}".replace(",", ".")


def formatar_decimal(valor, casas=2):
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor, casas=1):
    return formatar_decimal(valor * 100, casas) + "%"


def formatar_parametro(valor, percentual, casas):
    if percentual:
        return formatar_percentual(valor, casas)
    return formatar_decimal(valor, casas)


def formatar_valor_p(valor):
    if valor < 0.0001:
        mantissa, expoente = f"{valor:.2e}".split("e")
        algarismos = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
        return f"{mantissa.replace('.', ',')} × 10{str(int(expoente)).translate(algarismos)}"
    return formatar_decimal(valor, 4)


def formatar_pontos(diferenca, casas=1):
    """Diferença em pontos percentuais, com sinal."""
    pontos = diferenca * 100
    sinal = "+" if pontos > 0 else ""
    return f"{sinal}{formatar_decimal(pontos, casas)} p.p."
