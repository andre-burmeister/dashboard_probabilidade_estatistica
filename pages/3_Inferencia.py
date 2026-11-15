"""Painel 3: intervalos, testes e comparação com a população."""

import streamlit as st

import analise
from interface import (
    aplicar_estilo,
    carregar_estudo,
    em_markdown,
    grafico_intervalos,
    markdown,
    mostrar,
    tabela_inferencia,
    texto_conclusao,
)

aplicar_estilo()
populacao, amostra, plano, _metadados = carregar_estudo()
resultados = analise.inferir(populacao, amostra)
fpc = resultados[0]["fpc"]

st.title("Inferência e comparação com a população")
markdown(fr"""
    Os parâmetros populacionais foram calculados com os
    {analise.formatar_inteiro(plano['N'])} cursos.
    Os intervalos e os testes usam só os
    {analise.formatar_inteiro(plano['n'])} cursos da amostra.
    O nível de significância é 5%, e os intervalos têm confiança de 95%.

    Para as proporções, o intervalo é o de Wald e o teste é o $z$ bilateral.
    Para as médias, o intervalo e o teste são $t$ de Student, com
    {analise.formatar_inteiro(plano['n'] - 1)} graus de liberdade.
    O erro-padrão dos dois casos leva a correção de população finita,
    {analise.formatar_decimal(fpc, 3)}.

    $$
    z = \frac{{\hat{{p}} - p_0}}{{\sqrt{{p_0(1-p_0)/n}}\,\sqrt{{(N-n)/(N-1)}}}}
    \qquad
    t = \frac{{\bar{{x}} - \mu_0}}{{(s/\sqrt{{n}})\,\sqrt{{(N-n)/(N-1)}}}}
    $$

    No intervalo da proporção, o erro-padrão troca $p_0$ por $\hat{{p}}$
    e o quantil é $z$ = 1,96.
    No intervalo da média, o quantil é o da distribuição $t$.
""")

proporcoes = [item for item in resultados if item["tipo"] == "proporcao"]
medias = [item for item in resultados if item["tipo"] == "media"]
mostrar(grafico_intervalos(proporcoes, 0.5, "%", "Proporção dos cursos"))
st.caption(
    "A barra é o intervalo de 95%. O círculo é a estimativa amostral. "
    "O losango é o parâmetro populacional. A linha tracejada é a hipótese nula, em 50%."
)
for media in medias:
    formato = ",.0f" if media["coluna"] == "QT_MAT" else ",.2f"
    mostrar(grafico_intervalos([media], media["valor_nulo"], formato, media["nome"]))
    st.caption(
        "A linha tracejada é a hipótese nula, em "
        f"{media['texto_nulo']}."
    )
st.dataframe(tabela_inferencia(resultados), hide_index=True, width="stretch")

for resultado in resultados:
    markdown(f"""
        ### {resultado['nome']}

        **{resultado['pergunta']}**

        {resultado['justificativa']}

        $H_0$: {resultado['h0']}. $H_1$: {resultado['h1']}.
    """)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("População", analise.formatar_parametro(resultado["parametro"], resultado["percentual"], resultado["casas"]))
    c2.metric("Estimativa", analise.formatar_parametro(resultado["estimativa"], resultado["percentual"], resultado["casas"]))
    c3.metric(
        "Intervalo de 95%",
        (
            f"{analise.formatar_parametro(resultado['inferior'], resultado['percentual'], resultado['casas'])} a "
            f"{analise.formatar_parametro(resultado['superior'], resultado['percentual'], resultado['casas'])}"
        ),
    )
    c4.metric("Valor-p", analise.formatar_valor_p(resultado["valor_p"]))
    if resultado["tipo"] == "proporcao":
        detalhe = f"""
            Sucessos na amostra: {analise.formatar_inteiro(resultado['sucessos'])}
            de {analise.formatar_inteiro(resultado['n'])} cursos.
            Estatística $z$ = {analise.formatar_decimal(resultado['estatistica'], 2)}.
            Erro-padrão do intervalo = {analise.formatar_decimal(resultado['erro_padrao'], 4)}.
            Erro-padrão sob $H_0$ = {analise.formatar_decimal(resultado['erro_padrao_h0'], 4)}.
        """
    else:
        detalhe = f"""
            Desvio-padrão amostral = {analise.formatar_decimal(resultado['desvio'], 3)}.
            Estatística $t$ = {analise.formatar_decimal(resultado['estatistica'], 2)},
            com {analise.formatar_inteiro(resultado['graus_liberdade'])} graus de liberdade
            e valor crítico {analise.formatar_decimal(resultado['critico'], 3)}.
            Erro-padrão = {analise.formatar_decimal(resultado['erro_padrao'], 4)}.
        """
    markdown(f"""
        {em_markdown(detalhe)}

        {resultado['condicoes']}

        {texto_conclusao(resultado)}
    """)

markdown(f"""
    ### Limitações

    As matrículas e os inscritos por vaga são assimétricos. Alguns cursos muito
    grandes, ou com muitos inscritos para poucas vagas, puxam a média para cima
    da mediana. O intervalo e o teste descrevem essa média. A mediana, no painel
    descritivo, acompanha o curso típico.

    Cursos presenciais sem vaga registrada ficam fora da população, porque
    inscritos por vaga não existe quando o denominador é zero.

    O intervalo de Wald e o teste $z$ usam a aproximação normal. Com mais de mil
    cursos e proporções longe de 0 e de 1, $np$ e $n(1-p)$ ficam folgados.
    O intervalo $t$ usa o desvio-padrão amostral $s$. A correção de população finita
    vale {analise.formatar_decimal(fpc, 3)}, perto de 1, porque a amostra é
    uma fração pequena da população.

    Os quatro procedimentos usam a mesma amostra. A estimativa muda se o sorteio
    mudar, e o intervalo é a faixa compatível com essa variabilidade.
    Como a população está disponível, dá para ver se o intervalo a contém e se
    a decisão do teste coincide com o parâmetro conhecido.
    A educação a distância não entra nesta população. O recorte usa a modalidade
    presencial, `TP_MODALIDADE_ENSINO = 1`.
""")
