"""Tamanho amostral, amostra aleatória simples e inferência para proporção e média."""

from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy import stats

import preparar_dados

CONFIANCA = 0.95
Z = float(stats.norm.ppf((1 + CONFIANCA) / 2))
ERRO = 0.04
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
        "pergunta": "A proporção de cursos de licenciatura é 20%?",
        "justificativa": (
            "A hipótese nula fixa a proporção de licenciaturas em 20%. "
            "A alternativa é bilateral: $H_0$ é rejeitada se a proporção amostral "
            "ficar suficientemente acima ou abaixo de 20%."
        ),
        "valor_nulo": 0.20,
        "h0": r"$p = 0{,}20$",
        "h1": r"$p \neq 0{,}20$",
        "texto_nulo": "20%",
        "lado": "bilateral",
        "percentual": True,
        "casas": 2,
        "unidade": "",
    },
    {
        "id": "gratuito",
        "coluna": "gratuito",
        "tipo": "proporcao",
        "nome": "Curso gratuito",
        "pergunta": "A proporção de cursos gratuitos é 30%?",
        "justificativa": (
            "A hipótese nula fixa a proporção de cursos gratuitos em 30%. "
            "A alternativa é bilateral: $H_0$ é rejeitada se a proporção amostral "
            "ficar suficientemente acima ou abaixo de 30%."
        ),
        "valor_nulo": 0.30,
        "h0": r"$p = 0{,}30$",
        "h1": r"$p \neq 0{,}30$",
        "texto_nulo": "30%",
        "lado": "bilateral",
        "percentual": True,
        "casas": 2,
        "unidade": "",
    },
    {
        "id": "matriculas",
        "coluna": "QT_MAT",
        "tipo": "media",
        "nome": "Matrículas no curso",
        "pergunta": "O número médio de matrículas está abaixo de 150?",
        "justificativa": (
            "A hipótese nula afirma que o curso presencial tem, em média, menos de 150 matrículas. "
            "A alternativa é que a média é de pelo menos 150. "
            "O teste é unilateral e usa o limite 150: $H_0$ só é rejeitada se a média amostral "
            "ficar suficientemente acima desse valor."
        ),
        "valor_nulo": 150,
        "h0": r"$\mu < 150$",
        "h1": r"$\mu \geq 150$",
        "texto_nulo": "150 matrículas",
        "lado": "maior",
        "percentual": False,
        "casas": 1,
        "unidade": "matrículas",
    },
    {
        "id": "mulheres",
        "coluna": "proporcao_mulheres",
        "tipo": "media",
        "nome": "Proporção de mulheres",
        "pergunta": "O curso presencial tem, em média, metade das matrículas de mulheres?",
        "justificativa": (
            "Metade é a paridade entre mulheres e homens nas matrículas do curso. "
            "A média usa QT_MAT_FEM / QT_MAT, e cada curso pesa igual. "
            "A alternativa é bilateral."
        ),
        "valor_nulo": 0.50,
        "h0": r"$\mu = 0{,}50$",
        "h1": r"$\mu \neq 0{,}50$",
        "texto_nulo": "50%",
        "lado": "bilateral",
        "percentual": True,
        "casas": 1,
        "unidade": "pontos percentuais",
    },
]

QUALITATIVAS = [
    ("licenciatura_curso", "Licenciatura"),
    ("gratuidade", "Gratuidade"),
]

QUALITATIVAS_EXTRA = [
    ("area", "Área do conhecimento"),
    ("grau", "Grau acadêmico"),
    ("organizacao", "Organização acadêmica"),
]

QUANTITATIVAS = [
    {"coluna": "QT_MAT", "nome": "Matrículas no curso", "casas": 1, "casas_mediana": 0},
    {
        "coluna": "proporcao_mulheres",
        "nome": "Proporção de mulheres",
        "casas": 1,
        "casas_mediana": 1,
        "percentual": True,
        "teto": 1,
    },
]

QUANTITATIVAS_EXTRA = [
    {
        "coluna": "proporcao_25_mais",
        "nome": "Ingressantes com 25 anos ou mais",
        "casas": 1,
        "casas_mediana": 1,
        "percentual": True,
        "teto": 1,
        "motivo": "não houve ingressante em 2024",
    },
    {
        "coluna": "proporcao_preta_parda",
        "nome": "Pretos ou pardos nas matrículas",
        "casas": 1,
        "casas_mediana": 1,
        "percentual": True,
        "teto": 1,
        "motivo": "nenhuma matrícula tem cor declarada",
    },
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
    serie = dados[coluna].dropna().astype(float)
    return {
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "desvio": float(serie.std(ddof=1)),
        "minimo": float(serie.min()),
        "maximo": float(serie.max()),
        "assimetria": float(serie.skew()),
    }


def _decisao(parametro, valor_nulo, valor_p, alpha, texto_nulo, lado="bilateral"):
    rejeita = valor_p < alpha
    if lado == "maior":
        h0_verdadeira = parametro < valor_nulo
        if h0_verdadeira and rejeita:
            acordo = (
                f"Na população a média está abaixo de {texto_nulo} e o teste rejeitou $H_0$. "
                "Esta amostra produziu um falso positivo."
            )
        elif h0_verdadeira and not rejeita:
            acordo = (
                f"Na população a média está abaixo de {texto_nulo} "
                "e o teste não rejeitou $H_0$."
            )
        elif rejeita:
            acordo = (
                f"Na população a média não está abaixo de {texto_nulo}. "
                "A decisão do teste coincide com o parâmetro populacional."
            )
        else:
            acordo = (
                f"Na população a média não está abaixo de {texto_nulo}, "
                "mas esta amostra não rejeitou $H_0$. "
                "A diferença ficou dentro da variabilidade amostral."
            )
        return rejeita, acordo
    populacao_difere = abs(parametro - valor_nulo) > 1e-9
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


def inferir_proporcao(populacao, amostra, coluna, valor_nulo=VALOR_NULO, alpha=ALPHA, z=Z, texto_nulo="50%", lado="bilateral"):
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
    rejeita, acordo = _decisao(parametro, valor_nulo, valor_p, alpha, texto_nulo, lado)
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


def inferir_media(populacao, amostra, coluna, valor_nulo=VALOR_NULO, alpha=ALPHA, texto_nulo="", lado="bilateral"):
    """Intervalo t bilateral e teste t, com população finita no erro-padrão."""
    tamanho_populacao = len(populacao)
    valores = amostra[coluna].to_numpy(dtype=float)
    tamanho_amostra = len(valores)
    estimativa = float(valores.mean())
    desvio = float(valores.std(ddof=1))
    parametro = float(populacao[coluna].mean())
    fpc = fator_finito(tamanho_populacao, tamanho_amostra)
    graus = tamanho_amostra - 1
    erro_padrao = float(desvio / np.sqrt(tamanho_amostra) * fpc)
    critico_intervalo = float(stats.t.ppf(1 - alpha / 2, graus))
    inferior = estimativa - critico_intervalo * erro_padrao
    superior = estimativa + critico_intervalo * erro_padrao
    estatistica = (estimativa - valor_nulo) / erro_padrao
    if lado == "maior":
        valor_p = float(stats.t.sf(estatistica, graus))
        critico = float(stats.t.ppf(1 - alpha, graus))
    elif lado == "menor":
        valor_p = float(stats.t.cdf(estatistica, graus))
        critico = float(stats.t.ppf(alpha, graus))
    else:
        valor_p = float(min(1.0, 2 * stats.t.sf(abs(estatistica), graus)))
        critico = critico_intervalo
    rejeita, acordo = _decisao(parametro, valor_nulo, valor_p, alpha, texto_nulo, lado)
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
            + (
                "A assimetria é moderada, e a média fica perto da mediana."
                if abs(assimetria) < 1
                else "A assimetria é alta, e a média se afasta da mediana."
            )
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
                lado=hipotese.get("lado", "bilateral"),
            )
        else:
            resultado = inferir_media(
                populacao,
                amostra,
                hipotese["coluna"],
                valor_nulo=hipotese["valor_nulo"],
                texto_nulo=hipotese["texto_nulo"],
                lado=hipotese.get("lado", "bilateral"),
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
                "lado": hipotese.get("lado", "bilateral"),
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
