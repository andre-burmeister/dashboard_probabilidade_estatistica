"""Base, população e amostra do Censo da Educação Superior 2024."""

from pathlib import Path

import streamlit as st

import analise
from interface import aplicar_estilo, carregar_estudo, markdown

st.set_page_config(
    page_title="Censo 2024: população e amostra",
    page_icon="📊",
    layout="wide",
)


def pagina_inicial():
    aplicar_estilo()
    _populacao, _amostra, plano, metadados = carregar_estudo()

    st.title("Cursos presenciais de graduação em 2024")
    markdown(f"""
        O objetivo é aplicar amostragem, intervalo de confiança e teste de hipótese
        ao Censo da Educação Superior, e comparar a estimativa da amostra com o
        parâmetro calculado na população inteira.

        ### Base de dados

        A fonte é o [{analise.FONTE_NOME}]({analise.FONTE_URL}), do Inep.
        O censo registra, todo ano, as instituições e os cursos de graduação do país.
        A coleta usa o cadastro do Sistema e-MEC.
        O arquivo `{metadados['arquivo']}` tem
        **{analise.formatar_inteiro(metadados['n_linhas_arquivo'])}** linhas e
        **{analise.formatar_inteiro(metadados['n_colunas_arquivo'])}** variáveis.
        Cada linha é um registro de curso ou de local de oferta, não um aluno.

        O objetivo desta análise é descrever a oferta presencial e, a partir de uma
        amostra aleatória simples, estimar duas proporções e duas médias de curso.

        ### População e unidade amostral

        A unidade amostral é o **curso**. A população reúne os cursos de graduação
        presenciais com ao menos um aluno matriculado em 2024
        (`TP_MODALIDADE_ENSINO = 1` e `QT_MAT > 0`):
        **{analise.formatar_inteiro(plano['N'])} cursos**. Cada elemento da população
        é um curso presencial com matrícula. A proporção de mulheres do curso é
        `QT_MAT_FEM / QT_MAT`, e o curso sem matrícula fica de fora porque essa
        razão não existe quando o denominador é zero.

        ### Variáveis

        

        Quatro variáveis entram na inferência. Duas são características do curso:
        grau de licenciatura e gratuidade.
        Duas descrevem o tamanho e a composição do curso: o número de matrículas
        e a proporção de mulheres nas matrículas (`QT_MAT_FEM / QT_MAT`).
    """)
    variaveis = [
        {
            "Parâmetro": "Licenciatura",
            "Tipo": "Proporção",
            "Definição": "Curso com grau acadêmico de licenciatura",
            "Definição por variável": "TP_GRAU_ACADEMICO = 2",
        },
        {
            "Parâmetro": "Curso gratuito",
            "Tipo": "Proporção",
            "Definição": "Curso gratuito",
            "Definição por variável": "TP_GRATUIDADE = 1",
        },
        {
            "Parâmetro": "Matrículas no curso",
            "Tipo": "Média",
            "Definição": "Número de alunos matriculados no curso",
            "Definição por variável": "QT_MAT",
        },
        {
            "Parâmetro": "Proporção de mulheres",
            "Tipo": "Média",
            "Definição": "Mulheres matriculadas divididas pelas matrículas do curso",
            "Definição por variável": "QT_MAT_FEM / QT_MAT",
        },
    ]
    st.dataframe(variaveis, hide_index=True, width="stretch")

    z = round(plano["z"], 2)
    p = round(plano["p"], 2)
    erro = round(plano["erro"], 2)
    n0 = z**2 * p * (1 - p) / erro**2
    n_ajustado = n0 / (1 + (n0 - 1) / plano["N"])

    markdown(fr"""
        ### Dimensionamento da amostra

        Uma única amostra aleatória simples serve às quatro inferências.
        O tamanho foi calculado para uma proporção e para as médias utilizando a fórmula:

        $$
        n_0 = \frac{{z^2\, p\,(1-p)}}{{E^2}}
        \qquad
        n = \left\lceil \frac{{n_0}}{{1 + \frac{{(n_0 - 1)}}{{N}}}} \right\rceil
        $$
        
        Onde:

        - $p = {analise.formatar_decimal(plano['p'], 2)}$ é a **Proporção de planejamento** (no cálculo do tamanho, 0,50 maximiza $p(1-p)$ e produz a maior amostra).
        - $z = {analise.formatar_decimal(plano['z'], 2)}$ é o valor crítico da distribuição normal padrão para o **nível de confiança de {analise.formatar_percentual(plano['confianca'], 0)}**. O nível de significância dos testes é {analise.formatar_percentual(plano['alpha'], 0)}, o complemento dessa confiança.
        - $E = {analise.formatar_percentual(plano['erro'], 0)}$ é a **Margem de erro** (fixa antes de ver a amostra).
        - $N = {analise.formatar_inteiro(plano['N'])}$ é o **Tamanho da população** (a população tem tamanho conhecido e a amostra sai sem reposição, então o tamanho é ajustado por $N$).

        $$
        n_0 = \frac{{{analise.formatar_decimal(z, 2)}^{{2}} \times {analise.formatar_decimal(p, 2)} \times (1-{analise.formatar_decimal(p, 2)})}}{{{analise.formatar_decimal(erro, 2)}^{{2}}}} = {analise.formatar_decimal(n0, 2)}
        $$

        $$
        n = \left\lceil \frac{{{analise.formatar_decimal(n0, 2)}}}{{1 + \frac{{{analise.formatar_decimal(n0 - 1, 2)}}}{{{analise.formatar_inteiro(plano['N'])}}}}} \right\rceil = \left\lceil {analise.formatar_decimal(n_ajustado, 2)} \right\rceil = {analise.formatar_inteiro(plano['n'])}
        $$

        O tamanho da amostra resultante é de **{analise.formatar_inteiro(plano['n'])}** cursos.

        A confiança de {analise.formatar_percentual(plano['confianca'], 0)} e a margem de {analise.formatar_percentual(plano['erro'], 0)} foram escolhidas para gerar uma amostra menor, com possíveis diferenças mais marcantes em relação à população. Com menos cursos, a variabilidade amostral aumenta e a estimativa pode se afastar mais do parâmetro. Essa distância é o que os painéis seguintes comparam.


        O sorteio da amostra é realizado utilizando o `numpy.random.Generator`, iniciado com a semente
        **{plano['semente']}**, tira {analise.formatar_inteiro(plano['n'])} índices distintos, sem reposição. Cada curso tem a mesma probabilidade de entrar. A mesma semente reproduz a mesma amostra.

        Os três painéis usam esta população e esta amostra.
        O primeiro descreve a população. O segundo repete a descrição na amostra
        e mostra a diferença. O terceiro calcula os intervalos e os testes
        só com a amostra, e compara o resultado com o parâmetro populacional.
    """)


navegacao = st.navigation(
    [
        st.Page(pagina_inicial, title="Base e amostra", default=True),
        st.Page(
            Path(__file__).parent / "pages" / "1_Populacao.py",
            title="População",
        ),
        st.Page(
            Path(__file__).parent / "pages" / "2_Amostra.py",
            title="Amostra",
        ),
        st.Page(
            Path(__file__).parent / "pages" / "3_Inferencia.py",
            title="Inferência",
        ),
    ]
)
navegacao.run()
