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


def carregar_estudo():
    caminho = analise.preparar_dados.CAMINHO_PARQUET
    versao = caminho.stat().st_mtime_ns if caminho.exists() else 0
    return _carregar_estudo(versao)


@st.cache_data
def _carregar_estudo(_versao):
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
            labelLimit=520,
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
    valores = pd.Series(serie).dropna().astype(float).to_numpy()
    contagem, bordas = np.histogram(valores, bins=bins, range=(0, limite))
    return bordas[:-1], bordas[1:], contagem / len(valores)


def _spec(coluna):
    for variavel in analise.QUANTITATIVAS + analise.QUANTITATIVAS_EXTRA:
        if variavel["coluna"] == coluna:
            return variavel
    return {}


def _formato_eixo(coluna):
    if _spec(coluna).get("percentual"):
        return ".0%"
    if coluna == "QT_MAT":
        return ",.0f"
    return ",.1f"


def _limite_histograma(dados, coluna):
    teto = _spec(coluna).get("teto")
    if teto is not None:
        return float(teto)
    return float(dados[coluna].quantile(0.99))


def grafico_histograma(dados, coluna, titulo, eixo_x):
    limite = _limite_histograma(dados, coluna)
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
            y2=alt.datum(0),
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
    limite = _limite_histograma(populacao, coluna)
    quadros = []
    for grupo, dados in (("População", populacao), ("Amostra", amostra)):
        inicio, fim, proporcao = _faixas(dados[coluna].astype(float), limite)
        quadros.append(
            pd.DataFrame(
                {
                    "inicio": inicio,
                    "fim": fim,
                    "proporcao": proporcao,
                    "grupo": grupo,
                }
            )
        )
    plot = pd.concat(quadros, ignore_index=True)
    formato = _formato_eixo(coluna)
    grafico = (
        alt.Chart(plot)
        .mark_bar(opacity=0.55)
        .encode(
            x=alt.X("inicio:Q", title=eixo_x, axis=alt.Axis(format=formato)),
            x2="fim:Q",
            y=alt.Y("proporcao:Q", title="Proporção dos cursos", axis=alt.Axis(format="%")),
            y2=alt.datum(0),
            color=alt.Color("grupo:N", title=None, scale=_escala_grupo()),
            tooltip=[
                alt.Tooltip("grupo:N", title="Grupo"),
                alt.Tooltip("inicio:Q", title="De", format=formato),
                alt.Tooltip("fim:Q", title="Até", format=formato),
                alt.Tooltip("proporcao:Q", title="Proporção", format=".1%"),
            ],
        )
        .properties(title=titulo, height=280, width="container")
    )
    return _configurar(grafico)


def nota_cauda(dados, coluna, nome, referencia=None):
    if _spec(coluna).get("teto") is not None:
        return ""
    base = referencia if referencia is not None else dados
    limite = float(base[coluna].quantile(0.99))
    acima = int((dados[coluna] > limite).sum())
    if acima == 0:
        return ""
    if acima == 1:
        fora = "1 curso deste grupo fica acima disso"
    else:
        fora = f"{analise.formatar_inteiro(acima)} cursos deste grupo ficam acima disso"
    return em_markdown(f"""
        O eixo de {nome[0].lower()}{nome[1:]} vai até o percentil 99 da população
        ({analise.formatar_decimal(limite, 1)}).
        {fora};
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
        title=(
            "Estimativa, intervalo de "
            f"{analise.formatar_percentual(analise.CONFIANCA, 0)} e parâmetro populacional"
        ),
        height=alt.Step(46),
        width="container",
    )
    return _configurar(grafico)


def _formatar_quantitativo(valor, variavel, casas):
    if variavel.get("percentual"):
        return analise.formatar_percentual(valor, casas)
    return analise.formatar_decimal(valor, casas)


def _tabela_medidas(dados, variaveis=None):
    if variaveis is None:
        variaveis = analise.QUANTITATIVAS
    linhas = []
    for variavel in variaveis:
        item = analise.medidas(dados, variavel["coluna"])
        linhas.append(
            {
                "Variável": variavel["nome"],
                "Média": _formatar_quantitativo(item["media"], variavel, variavel["casas"]),
                "Mediana": _formatar_quantitativo(item["mediana"], variavel, variavel["casas_mediana"]),
                "Desvio-padrão": _formatar_quantitativo(item["desvio"], variavel, variavel["casas"]),
                "Mínimo": _formatar_quantitativo(item["minimo"], variavel, variavel["casas_mediana"]),
                "Máximo": _formatar_quantitativo(item["maximo"], variavel, variavel["casas"]),
                "Assimetria": analise.formatar_decimal(item["assimetria"], 2),
            }
        )
    return pd.DataFrame(linhas)


def _diferenca_numero(amostra, populacao, casas):
    valor = amostra - populacao
    sinal = "+" if valor > 0 else ""
    return sinal + analise.formatar_decimal(valor, casas)


def tabela_comparacao(amostra, populacao, quantitativas=None, proporcoes=None):
    if quantitativas is None:
        quantitativas = analise.QUANTITATIVAS
    if proporcoes is None:
        proporcoes = (
            ("licenciatura", "Proporção de cursos de licenciatura"),
            ("gratuito", "Proporção de cursos gratuitos"),
        )
    linhas = []
    for variavel in quantitativas:
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
            if variavel.get("percentual"):
                diferenca = analise.formatar_pontos(ma[chave] - mp[chave], casas)
            else:
                diferenca = _diferenca_numero(ma[chave], mp[chave], casas)
            linhas.append(
                {
                    "Indicador": titulo,
                    "População": _formatar_quantitativo(mp[chave], variavel, casas),
                    "Amostra": _formatar_quantitativo(ma[chave], variavel, casas),
                    "Diferença": diferenca,
                }
            )
    for coluna, nome in proporcoes:
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
    media_mulheres = float(populacao["proporcao_mulheres"].mean())
    mediana_mulheres = float(populacao["proporcao_mulheres"].median())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cursos", analise.formatar_inteiro(len(populacao)))
    c2.metric("Matrículas", analise.formatar_inteiro(matriculas))
    c3.metric("Média de matrículas", analise.formatar_decimal(media_mat, 1))
    c4.metric("Mediana de matrículas", analise.formatar_decimal(mediana_mat, 0))
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Licenciatura", analise.formatar_percentual(populacao["licenciatura"].mean(), 1))
    c6.metric("Gratuitos", analise.formatar_percentual(populacao["gratuito"].mean(), 1))
    c7.metric("Proporção média de mulheres", analise.formatar_percentual(media_mulheres, 1))
    c8.metric("Proporção mediana de mulheres", analise.formatar_percentual(mediana_mulheres, 1))
    markdown("""
        ## Variáveis quantitativas da análise

        Estas duas médias entram nos testes do painel de inferência.
        A média, a mediana e o desvio-padrão usam o curso como unidade.
        O número de matrículas é a contagem do censo.
        A proporção de mulheres é `QT_MAT_FEM / QT_MAT`, mostrada em percentagem.
        O desvio-padrão dessa proporção está em pontos percentuais.
        Nas matrículas, a média fica acima da mediana porque alguns cursos são muito grandes.
        Na proporção de mulheres, a média fica um pouco abaixo da mediana.
        Cada curso pesa igual nessa média, qualquer que seja o número de matrículas.
    """)
    _bloco_quantitativo(populacao, analise.QUANTITATIVAS)

    markdown("""
        ## Variáveis qualitativas da análise

        Estas duas proporções entram nos testes do painel de inferência.
        Licenciatura separa os cursos de licenciatura dos demais graus.
        Gratuidade separa curso gratuito e pago.
        As barras e as tabelas mostram a frequência e a proporção dos cursos.
    """)
    _grades_qualitativas(populacao, variaveis=analise.QUALITATIVAS)

    markdown("""
        ## Mais variáveis qualitativas relevantes

        A área do conhecimento, o grau acadêmico e a organização acadêmica detalham a oferta.
        O grau separa bacharelado, licenciatura e tecnológico.
        Na seção anterior, a licenciatura junta os outros graus em uma categoria.
    """)
    _grades_qualitativas(populacao, variaveis=analise.QUALITATIVAS_EXTRA, com_tabela=False)

    markdown("""
        ## Mais variáveis quantitativas relevantes

        Estas proporções descrevem a composição do curso e não entram nos testes.
        Ingressantes com 25 anos ou mais é a soma das faixas a partir de 25 anos,
        dividida por `QT_ING`.
        Pretos ou pardos nas matrículas é
        (`QT_MAT_PRETA` + `QT_MAT_PARDA`) / (`QT_MAT` − `QT_MAT_CORND`).
        A cor não declarada fica fora do denominador.
        Cada curso pesa igual, e os valores estão em percentagem.
        O desvio-padrão está em pontos percentuais.
    """)
    _bloco_quantitativo(populacao, analise.QUANTITATIVAS_EXTRA)


def _texto_exclusao(populacao, variaveis, amostra=None):
    frases = []
    for variavel in variaveis:
        motivo = variavel.get("motivo")
        if not motivo:
            continue
        coluna = variavel["coluna"]
        if amostra is None:
            fora = int(populacao[coluna].isna().sum())
            frases.append(
                f"{variavel['nome']}: {analise.formatar_inteiro(fora)} cursos ficam de fora "
                f"porque {motivo}."
            )
        else:
            fora_pop = int(populacao[coluna].isna().sum())
            fora_amo = int(amostra[coluna].isna().sum())
            frases.append(
                f"{variavel['nome']}: {analise.formatar_inteiro(fora_pop)} cursos da população "
                f"e {analise.formatar_inteiro(fora_amo)} da amostra ficam de fora porque {motivo}."
            )
    return " ".join(frases)


def _legenda_quantitativa(dados, variavel, referencia=None):
    return nota_cauda(dados, variavel["coluna"], variavel["nome"], referencia)


def _bloco_quantitativo(populacao, variaveis, amostra=None, tabela=True):
    if tabela and amostra is None:
        st.dataframe(_tabela_medidas(populacao, variaveis), hide_index=True, width="stretch")
    elif tabela:
        st.dataframe(
            tabela_comparacao(amostra, populacao, quantitativas=variaveis, proporcoes=()),
            hide_index=True,
            width="stretch",
        )
    exclusao = _texto_exclusao(populacao, variaveis, amostra)
    if amostra is not None and tabela:
        st.caption(
            "A diferença é a medida da amostra menos a medida da população. "
            "Nas proporções, ela está em pontos percentuais. "
            + exclusao
        )
    elif exclusao:
        st.caption(exclusao)
    colunas = st.columns(len(variaveis))
    for coluna_tela, variavel in zip(colunas, variaveis):
        with coluna_tela:
            if amostra is None:
                mostrar(
                    grafico_histograma(
                        populacao,
                        variavel["coluna"],
                        variavel["nome"],
                        variavel["nome"],
                    )
                )
                nota = _legenda_quantitativa(populacao, variavel)
            else:
                mostrar(
                    grafico_histograma_comparacao(
                        populacao,
                        amostra,
                        variavel["coluna"],
                        variavel["nome"],
                        variavel["nome"],
                    )
                )
                nota = _legenda_quantitativa(amostra, variavel, populacao)
            if nota:
                st.caption(nota)


def _pares_qualitativos(variaveis):
    """A área ocupa a linha inteira. As demais variáveis entram em pares."""
    pares = []
    indice = 0
    while indice < len(variaveis):
        if variaveis[indice][0] == "area" or indice == len(variaveis) - 1:
            pares.append([variaveis[indice]])
            indice += 1
            continue
        par = variaveis[indice : indice + 2]
        if par[-1][0] == "area":
            par = par[:1]
        pares.append(par)
        indice += len(par)
    return pares


def _grades_qualitativas(populacao, amostra=None, variaveis=None, com_tabela=True):
    if variaveis is None:
        variaveis = analise.QUALITATIVAS
    for par in _pares_qualitativos(variaveis):
        colunas = st.columns(len(par))
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
                    if com_tabela:
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
                    if com_tabela:
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
        ### Variáveis quantitativas da análise

        Os histogramas usam a mesma escala e mostram a proporção dos cursos em cada faixa,
        para a população e para a amostra.
    """)
    _bloco_quantitativo(populacao, analise.QUANTITATIVAS, amostra, tabela=False)

    markdown("""
        ### Variáveis qualitativas da análise

        Cada categoria traz a proporção na população e na amostra, lado a lado,
        e a diferença em pontos percentuais.
    """)
    _grades_qualitativas(populacao, amostra, analise.QUALITATIVAS)

    markdown("""
        ### Mais variáveis qualitativas relevantes

        A área, o grau e a organização acadêmica repetem a comparação da população.
    """)
    _grades_qualitativas(populacao, amostra, analise.QUALITATIVAS_EXTRA, com_tabela=False)

    markdown("""
        ### Mais variáveis quantitativas relevantes

        As duas proporções seguem as mesmas definições da população.
        O curso sem ingressante, ou sem cor declarada, fica de fora da respectiva conta.
    """)
    _bloco_quantitativo(populacao, analise.QUANTITATIVAS_EXTRA, amostra)


def _formatar_resultado(resultado, valor, casas=None):
    return analise.formatar_parametro(
        valor,
        resultado["percentual"],
        resultado["casas"] if casas is None else casas,
    )


def texto_conclusao(resultado):
    referencia = resultado["texto_nulo"]
    nivel = analise.formatar_percentual(analise.ALPHA, 0)
    lado = resultado.get("lado", "bilateral")
    if lado == "maior":
        if resultado["rejeita"]:
            decisao = (
                f"Ao nível de {nivel}, rejeita-se $H_0$. "
                f"A amostra indica que a média não está abaixo de {referencia}."
            )
        else:
            decisao = (
                f"Ao nível de {nivel}, não se rejeita $H_0$. "
                f"A amostra não indica que a média deixe de estar abaixo de {referencia}."
            )
    elif resultado["rejeita"]:
        decisao = (
            f"Ao nível de {nivel}, rejeita-se $H_0$. A amostra indica que o parâmetro difere de {referencia}."
        )
    else:
        decisao = (
            f"Ao nível de {nivel}, não se rejeita $H_0$. "
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
        e o intervalo de {analise.formatar_percentual(analise.CONFIANCA, 0)} vai de {inferior}
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
                f"Intervalo de {analise.formatar_percentual(analise.CONFIANCA, 0)}": (
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
