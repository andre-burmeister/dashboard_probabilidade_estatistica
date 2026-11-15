"""Gráficos e blocos compartilhados pelos três painéis."""

import re
import textwrap

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import analise

COR_TEXTO = "#14222b"
COR_POP = "#0e7c74"
COR_AMO = "#c2410c"
COR_NULO = "#57534e"

ESTILO = """
<style>
.block-container { padding-top: 1.6rem; padding-left: 1.6rem; padding-right: 1.6rem; max-width: 100%; }
h1 { letter-spacing: -0.03em; font-weight: 650; }
[data-testid="stMetric"] {
    background: light-dark(#ffffff, #262730);
    border: 1px solid light-dark(rgba(20, 34, 43, 0.08), rgba(250, 250, 250, 0.12));
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
}
[data-testid="stVegaLiteChart"] [fill="#14222b"] {
    fill: light-dark(#14222b, #fafafa) !important;
}
[data-testid="stVegaLiteChart"] [stroke="#14222b"] {
    stroke: light-dark(#14222b, #fafafa) !important;
}
.katex-display > .katex > .katex-html {
    width: fit-content;
    margin-left: auto;
    margin-right: auto;
}
@media (max-width: 640px) {
    .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
}
</style>
"""


def _bloco_markdown(bloco):
    linhas = [linha.strip() for linha in bloco.splitlines() if linha.strip()]
    partes = []
    atual = []

    def despejar():
        if not atual:
            return
        if any(linha.startswith("- ") for linha in atual):
            itens = []
            item = []
            for linha in atual:
                if linha.startswith("- ") and item:
                    itens.append(" ".join(item))
                    item = [linha]
                else:
                    item.append(linha)
            if item:
                itens.append(" ".join(item))
            partes.append("\n".join(itens))
        else:
            partes.append(" ".join(atual))
        atual.clear()

    for linha in linhas:
        if linha.startswith("#"):
            despejar()
            partes.append(linha)
        else:
            atual.append(linha)
    despejar()
    return "\n\n".join(partes)


def em_markdown(conteudo):
    """Junta linhas de um parágrafo e tira a indentação do código.

    Uma linha em branco abre outro parágrafo. Uma linha que começa com "#"
    é um título. Uma linha que começa com "- " abre um item de lista; as
    linhas seguintes entram nesse item.
    """
    bruto = textwrap.dedent(conteudo).strip()
    blocos = re.split(r"\n\s*\n", bruto)
    return "\n\n".join(_bloco_markdown(bloco) for bloco in blocos if bloco.strip())


def markdown(conteudo):
    st.markdown(em_markdown(conteudo))


def aplicar_estilo():
    st.markdown(ESTILO, unsafe_allow_html=True)


@st.cache_data
def carregar_estudo():
    populacao, metadados = analise.carregar_populacao()
    plano = analise.tamanho_amostral(len(populacao))
    amostra = analise.amostrar(populacao, plano["n"])
    return populacao, amostra, plano, metadados


def _configurar(grafico):
    return (
        grafico.configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelFontSize=12,
            titleFontSize=13,
            labelColor=COR_TEXTO,
            titleColor=COR_TEXTO,
            labelLimit=280,
            gridColor="#e6e0d6",
            domainColor="#4e4842",
            tickColor="#4e4842",
        )
        .configure_legend(
            labelColor=COR_TEXTO,
            titleColor=COR_TEXTO,
            orient="top",
            labelFontSize=12,
        )
        .configure_title(fontSize=16, fontWeight=600, anchor="start", color=COR_TEXTO)
    )


def _escala_grupo():
    return alt.Scale(domain=["População", "Amostra"], range=[COR_POP, COR_AMO])


def mostrar(grafico):
    st.altair_chart(grafico, width="stretch")


def grafico_barras(tabela, coluna, titulo):
    grafico = (
        alt.Chart(tabela)
        .mark_bar(color=COR_POP, cornerRadiusEnd=3)
        .encode(
            y=alt.Y(f"{coluna}:N", sort="-x", title=None),
            x=alt.X(
                "proporcao:Q",
                title="Proporção dos cursos",
                axis=alt.Axis(format="%"),
            ),
            tooltip=[
                alt.Tooltip(f"{coluna}:N", title="Categoria"),
                alt.Tooltip("cursos:Q", title="Cursos", format=",.0f"),
                alt.Tooltip("proporcao:Q", title="Proporção", format=".1%"),
            ],
        )
        .properties(title=titulo, height=alt.Step(26), width="container")
    )
    return _configurar(grafico)


def grafico_barras_comparacao(longo, coluna, titulo):
    ordem = (
        longo.loc[longo["grupo"] == "População"]
        .sort_values("proporcao", ascending=False)[coluna]
        .tolist()
    )
    grafico = (
        alt.Chart(longo)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            y=alt.Y(f"{coluna}:N", sort=ordem, title=None),
            x=alt.X(
                "proporcao:Q",
                title="Proporção dos cursos",
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color("grupo:N", title=None, scale=_escala_grupo()),
            yOffset="grupo:N",
            tooltip=[
                alt.Tooltip(f"{coluna}:N", title="Categoria"),
                alt.Tooltip("grupo:N", title="Grupo"),
                alt.Tooltip("proporcao:Q", title="Proporção", format=".1%"),
            ],
        )
        .properties(title=titulo, height=alt.Step(32), width="container")
    )
    return _configurar(grafico)


def _faixas(serie, limite, bins=30):
    """Conta a proporção dos cursos em cada faixa. Valores acima do limite ficam de fora."""
    contagem, bordas = np.histogram(serie, bins=bins, range=(0, limite))
    return bordas[:-1], bordas[1:], contagem / len(serie)


def _formato_eixo(coluna):
    if coluna == "QT_MAT":
        return ",.0f"
    if coluna == "inscritos_por_vaga":
        return ",.1f"
    return ".0%"


def grafico_histograma(dados, coluna, titulo, eixo_x):
    limite = float(dados[coluna].quantile(0.99))
    inicio, fim, proporcao = _faixas(dados[coluna].astype(float), limite)
    plot = pd.DataFrame({"inicio": inicio, "fim": fim, "proporcao": proporcao})
    formato = _formato_eixo(coluna)
    grafico = (
        alt.Chart(plot)
        .mark_bar(color=COR_POP)
        .encode(
            x=alt.X("inicio:Q", title=eixo_x, axis=alt.Axis(format=formato)),
            x2="fim:Q",
            y=alt.Y("proporcao:Q", title="Proporção dos cursos", axis=alt.Axis(format="%")),
            tooltip=[
                alt.Tooltip("inicio:Q", title="De", format=formato),
                alt.Tooltip("fim:Q", title="Até", format=formato),
                alt.Tooltip("proporcao:Q", title="Proporção", format=".1%"),
            ],
        )
        .properties(title=titulo, height=280, width="container")
    )
    return _configurar(grafico)


def grafico_histograma_comparacao(populacao, amostra, coluna, titulo, eixo_x):
    limite = float(populacao[coluna].quantile(0.99))
    quadros = []
    for grupo, dados in (("População", populacao), ("Amostra", amostra)):
        inicio, fim, proporcao = _faixas(dados[coluna].astype(float), limite)
        quadros.append(
            pd.DataFrame(
                {
                    "centro": (inicio + fim) / 2,
                    "proporcao": proporcao,
                    "grupo": grupo,
                }
            )
        )
    plot = pd.concat(quadros, ignore_index=True)
    formato = _formato_eixo(coluna)
    grafico = (
        alt.Chart(plot)
        .mark_line(interpolate="step", strokeWidth=2)
        .encode(
            x=alt.X("centro:Q", title=eixo_x, axis=alt.Axis(format=formato)),
            y=alt.Y("proporcao:Q", title="Proporção dos cursos", axis=alt.Axis(format="%")),
            color=alt.Color("grupo:N", title=None, scale=_escala_grupo()),
            tooltip=[
                alt.Tooltip("grupo:N", title="Grupo"),
                alt.Tooltip("centro:Q", title=eixo_x, format=formato),
                alt.Tooltip("proporcao:Q", title="Proporção", format=".1%"),
            ],
        )
        .properties(title=titulo, height=280, width="container")
    )
    return _configurar(grafico)


def nota_cauda(dados, coluna, nome, referencia=None):
    base = referencia if referencia is not None else dados
    limite = float(base[coluna].quantile(0.99))
    acima = int((dados[coluna] > limite).sum())
    if acima == 0:
        return ""
    return em_markdown(f"""
        O eixo de {nome[0].lower()}{nome[1:]} vai até o percentil 99 da população
        ({analise.formatar_decimal(limite, 1)}).
        {analise.formatar_inteiro(acima)} cursos deste grupo ficam acima disso;
        o maior valor é {analise.formatar_decimal(dados[coluna].max(), 1)}.
    """)


def grafico_intervalos(resultados, valor_nulo, formato, titulo_eixo):
    plot = pd.DataFrame(
        {
            "nome": [item["nome"] for item in resultados],
            "estimativa": [item["estimativa"] for item in resultados],
            "inferior": [item["inferior"] for item in resultados],
            "superior": [item["superior"] for item in resultados],
            "populacao": [item["parametro"] for item in resultados],
        }
    )
    ordem = plot["nome"].tolist()
    menor = min(valor_nulo, float(plot["inferior"].min()), float(plot["populacao"].min()))
    maior = max(valor_nulo, float(plot["superior"].max()), float(plot["populacao"].max()))
    folga = max((maior - menor) * 0.15, abs(valor_nulo) * 0.02, 0.02)
    escala = alt.Scale(domain=[menor - folga, maior + folga], nice=False)
    eixo = dict(scale=escala, axis=alt.Axis(format=formato))
    base = alt.Chart(plot).encode(y=alt.Y("nome:N", sort=ordem, title=None))
    intervalo = base.mark_rule(color=COR_POP, strokeWidth=4).encode(
        x=alt.X("inferior:Q", title=titulo_eixo, **eixo),
        x2="superior:Q",
    )
    estimativa = base.mark_point(filled=True, size=90, color=COR_POP).encode(
        x=alt.X("estimativa:Q", **eixo),
        tooltip=[
            alt.Tooltip("nome:N", title="Parâmetro"),
            alt.Tooltip("estimativa:Q", title="Estimativa", format=formato),
            alt.Tooltip("inferior:Q", title="Limite inferior", format=formato),
            alt.Tooltip("superior:Q", title="Limite superior", format=formato),
            alt.Tooltip("populacao:Q", title="População", format=formato),
        ],
    )
    populacao = base.mark_point(shape="diamond", filled=True, size=90, color=COR_AMO).encode(
        x=alt.X("populacao:Q", **eixo)
    )
    nulo = (
        alt.Chart(pd.DataFrame({"valor": [valor_nulo]}))
        .mark_rule(strokeDash=[6, 4], color=COR_NULO)
        .encode(x=alt.X("valor:Q", scale=escala))
    )
    grafico = (nulo + intervalo + estimativa + populacao).properties(
        title="Estimativa, intervalo de 95% e parâmetro populacional",
        height=alt.Step(46),
        width="container",
    )
    return _configurar(grafico)


def _tabela_medidas(dados):
    linhas = []
    for variavel in analise.QUANTITATIVAS:
        item = analise.medidas(dados, variavel["coluna"])
        linhas.append(
            {
                "Variável": variavel["nome"],
                "Média": analise.formatar_decimal(item["media"], variavel["casas"]),
                "Mediana": analise.formatar_decimal(item["mediana"], variavel["casas_mediana"]),
                "Desvio-padrão": analise.formatar_decimal(item["desvio"], variavel["casas"]),
                "Mínimo": analise.formatar_decimal(item["minimo"], variavel["casas_mediana"]),
                "Máximo": analise.formatar_decimal(item["maximo"], variavel["casas"]),
                "Assimetria": analise.formatar_decimal(item["assimetria"], 2),
            }
        )
    return pd.DataFrame(linhas)


def _diferenca_numero(amostra, populacao, casas):
    valor = amostra - populacao
    sinal = "+" if valor > 0 else ""
    return sinal + analise.formatar_decimal(valor, casas)


def tabela_comparacao(amostra, populacao):
    linhas = []
    for variavel in analise.QUANTITATIVAS:
        mp = analise.medidas(populacao, variavel["coluna"])
        ma = analise.medidas(amostra, variavel["coluna"])
        nome = variavel["nome"]
        pares = (
            ("Média", "media", variavel["casas"]),
            ("Mediana", "mediana", variavel["casas_mediana"]),
            ("Desvio-padrão", "desvio", variavel["casas"]),
        )
        for rotulo, chave, casas in pares:
            titulo = f"{rotulo} de {nome[0].lower()}{nome[1:]}"
            linhas.append(
                {
                    "Indicador": titulo,
                    "População": analise.formatar_decimal(mp[chave], casas),
                    "Amostra": analise.formatar_decimal(ma[chave], casas),
                    "Diferença": _diferenca_numero(ma[chave], mp[chave], casas),
                }
            )
    for coluna, nome in (
        ("licenciatura", "Proporção de cursos de licenciatura"),
        ("gratuito", "Proporção de cursos gratuitos"),
    ):
        pop = float(populacao[coluna].mean())
        amo = float(amostra[coluna].mean())
        linhas.append(
            {
                "Indicador": nome,
                "População": analise.formatar_percentual(pop, 1),
                "Amostra": analise.formatar_percentual(amo, 1),
                "Diferença": analise.formatar_pontos(amo - pop, 1),
            }
        )
    return pd.DataFrame(linhas)


def _longo(tabela, coluna):
    populacao = tabela[[coluna, "prop_pop"]].rename(columns={"prop_pop": "proporcao"})
    populacao["grupo"] = "População"
    amostra = tabela[[coluna, "prop_amo"]].rename(columns={"prop_amo": "proporcao"})
    amostra["grupo"] = "Amostra"
    return pd.concat([populacao, amostra], ignore_index=True)


def _tabela_freq_comparada(tabela, coluna):
    visivel = tabela.copy()
    visivel["Diferença"] = visivel["diferenca"].map(lambda valor: analise.formatar_pontos(valor, 1))
    visivel["Proporção na população"] = visivel["prop_pop"].map(
        lambda valor: analise.formatar_percentual(valor, 1)
    )
    visivel["Proporção na amostra"] = visivel["prop_amo"].map(
        lambda valor: analise.formatar_percentual(valor, 1)
    )
    visivel = visivel.rename(
        columns={
            coluna: "Categoria",
            "cursos_pop": "Cursos na população",
            "cursos_amo": "Cursos na amostra",
        }
    )
    return visivel[
        [
            "Categoria",
            "Cursos na população",
            "Proporção na população",
            "Cursos na amostra",
            "Proporção na amostra",
            "Diferença",
        ]
    ]


def painel_populacao(populacao):
    matriculas = int(populacao["QT_MAT"].sum())
    media_mat = float(populacao["QT_MAT"].mean())
    mediana_mat = float(populacao["QT_MAT"].median())
    media_vaga = float(populacao["inscritos_por_vaga"].mean())
    mediana_vaga = float(populacao["inscritos_por_vaga"].median())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cursos", analise.formatar_inteiro(len(populacao)))
    c2.metric("Matrículas", analise.formatar_inteiro(matriculas))
    c3.metric("Média de matrículas", analise.formatar_decimal(media_mat, 1))
    c4.metric("Mediana de matrículas", analise.formatar_decimal(mediana_mat, 0))
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Licenciatura", analise.formatar_percentual(populacao["licenciatura"].mean(), 1))
    c6.metric("Gratuitos", analise.formatar_percentual(populacao["gratuito"].mean(), 1))
    c7.metric("Média de inscritos por vaga", analise.formatar_decimal(media_vaga, 2))
    c8.metric("Mediana de inscritos por vaga", analise.formatar_decimal(mediana_vaga, 2))
    markdown("""
        ### Variáveis quantitativas

        A média, a mediana e o desvio-padrão usam o curso como unidade.
        O número de matrículas é a contagem do censo.
        Os inscritos por vaga são `QT_INSCRITO_TOTAL / QT_VG_TOTAL`.
        Nas duas, a média fica acima da mediana porque alguns cursos são muito grandes
        ou têm muitos inscritos para poucas vagas.
    """)
    st.dataframe(_tabela_medidas(populacao), hide_index=True, width="stretch")
    colunas = st.columns(2)
    for coluna_tela, variavel in zip(colunas, analise.QUANTITATIVAS):
        with coluna_tela:
            mostrar(
                grafico_histograma(
                    populacao,
                    variavel["coluna"],
                    variavel["nome"],
                    variavel["nome"],
                )
            )
            st.caption(nota_cauda(populacao, variavel["coluna"], variavel["nome"]))

    markdown("""
        ### Variáveis qualitativas

        As barras e as tabelas mostram a frequência e a proporção dos cursos.
    """)
    _grades_qualitativas(populacao)


def _grades_qualitativas(populacao, amostra=None):
    for indice in range(0, len(analise.QUALITATIVAS), 2):
        par = analise.QUALITATIVAS[indice : indice + 2]
        colunas = st.columns(2)
        for coluna_tela, (coluna, titulo) in zip(colunas, par):
            with coluna_tela:
                if amostra is None:
                    tabela = analise.frequencia(populacao, coluna)
                    mostrar(grafico_barras(tabela, coluna, titulo))
                    visivel = tabela.rename(
                        columns={coluna: "Categoria", "cursos": "Cursos", "proporcao": "Proporção"}
                    )
                    visivel["Proporção"] = visivel["Proporção"].map(
                        lambda valor: analise.formatar_percentual(valor, 1)
                    )
                    st.dataframe(visivel, hide_index=True, width="stretch")
                else:
                    pop = analise.frequencia(populacao, coluna).rename(
                        columns={"cursos": "cursos_pop", "proporcao": "prop_pop"}
                    )
                    amo = analise.frequencia(amostra, coluna).rename(
                        columns={"cursos": "cursos_amo", "proporcao": "prop_amo"}
                    )
                    junto = pop.merge(amo, on=coluna, how="outer").fillna(0)
                    junto["diferenca"] = junto["prop_amo"] - junto["prop_pop"]
                    junto["cursos_pop"] = junto["cursos_pop"].astype(int)
                    junto["cursos_amo"] = junto["cursos_amo"].astype(int)
                    junto = junto.sort_values("prop_pop", ascending=False)
                    mostrar(grafico_barras_comparacao(_longo(junto, coluna), coluna, titulo))
                    st.dataframe(
                        _tabela_freq_comparada(junto, coluna),
                        hide_index=True,
                        width="stretch",
                    )


def painel_amostra(amostra, populacao):
    st.dataframe(tabela_comparacao(amostra, populacao), hide_index=True, width="stretch")
    st.caption(
        "A diferença é a medida da amostra menos a medida da população. "
        "Nas proporções, ela está em pontos percentuais."
    )

    markdown("""
        ### Variáveis quantitativas

        As curvas usam a mesma escala e mostram a proporção dos cursos em cada faixa,
        para a população e para a amostra.
    """)
    colunas = st.columns(2)
    for coluna_tela, variavel in zip(colunas, analise.QUANTITATIVAS):
        with coluna_tela:
            mostrar(
                grafico_histograma_comparacao(
                    populacao,
                    amostra,
                    variavel["coluna"],
                    variavel["nome"],
                    variavel["nome"],
                )
            )
            st.caption(nota_cauda(amostra, variavel["coluna"], variavel["nome"], populacao))

    markdown("""
        ### Variáveis qualitativas

        Cada categoria traz a proporção na população e na amostra, lado a lado,
        e a diferença em pontos percentuais.
    """)
    _grades_qualitativas(populacao, amostra)


def _formatar_resultado(resultado, valor, casas=None):
    return analise.formatar_parametro(
        valor,
        resultado["percentual"],
        resultado["casas"] if casas is None else casas,
    )


def texto_conclusao(resultado):
    referencia = resultado["texto_nulo"]
    if resultado["rejeita"]:
        decisao = (
            f"Ao nível de 5%, rejeita-se $H_0$. A amostra indica que o parâmetro difere de {referencia}."
        )
    else:
        decisao = (
            "Ao nível de 5%, não se rejeita $H_0$. "
            f"A amostra não indica diferença em relação a {referencia}."
        )
    cobertura = (
        "O intervalo contém o parâmetro populacional."
        if resultado["cobre"]
        else "O intervalo não contém o parâmetro populacional."
    )
    diferenca = resultado["estimativa"] - resultado["parametro"]
    if resultado["percentual"]:
        pontos = analise.formatar_decimal(abs(diferenca) * 100, 2)
        unidade = "pontos percentuais"
    else:
        pontos = analise.formatar_decimal(abs(diferenca), resultado["casas"])
        unidade = resultado["unidade"]
    if diferenca > 0:
        distancia = f"A estimativa fica {pontos} {unidade} acima do parâmetro."
    elif diferenca < 0:
        distancia = f"A estimativa fica {pontos} {unidade} abaixo do parâmetro."
    else:
        distancia = "A estimativa coincide com o parâmetro."
    estimativa = _formatar_resultado(resultado, resultado["estimativa"])
    inferior = _formatar_resultado(resultado, resultado["inferior"])
    superior = _formatar_resultado(resultado, resultado["superior"])
    parametro = _formatar_resultado(resultado, resultado["parametro"])
    return em_markdown(f"""
        A estimativa é {estimativa}
        e o intervalo de 95% vai de {inferior}
        a {superior}.
        O parâmetro populacional é {parametro}.
        {cobertura} {distancia} {decisao} {resultado['acordo']}
    """)


def tabela_inferencia(resultados):
    linhas = []
    for item in resultados:
        linhas.append(
            {
                "Parâmetro": item["nome"],
                "População": _formatar_resultado(item, item["parametro"]),
                "Estimativa": _formatar_resultado(item, item["estimativa"]),
                "Intervalo de 95%": (
                    f"[{_formatar_resultado(item, item['inferior'])}; "
                    f"{_formatar_resultado(item, item['superior'])}]"
                ),
                "Cobre a população": "Sim" if item["cobre"] else "Não",
                "Estatística": (
                    f"{item['estatistica_nome']} = {analise.formatar_decimal(item['estatistica'], 2)}"
                ),
                "Valor-p": analise.formatar_valor_p(item["valor_p"]),
                "Conclusão": "Rejeita H0" if item["rejeita"] else "Não rejeita H0",
            }
        )
    return pd.DataFrame(linhas)
