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
    O nível de significância é {analise.formatar_percentual(plano['alpha'], 0)}, e os intervalos têm confiança de {analise.formatar_percentual(plano['confianca'], 0)}.

    Para as proporções, o intervalo é o de Wald e o teste é o $z$ bilateral.
    Para as médias, o intervalo é $t$ de Student, com
    {analise.formatar_inteiro(plano['n'] - 1)} graus de liberdade.
    O teste da proporção de mulheres também é bilateral.
    O teste das matrículas é unilateral: $H_0$ afirma que a média está abaixo de 150,
    e só uma média amostral suficientemente alta a rejeita.
    O erro-padrão dos dois casos leva a correção de população finita,
    {analise.formatar_decimal(fpc, 3)}.

    $$
    z = \frac{{\hat{{p}} - p_0}}{{\sqrt{{p_0(1-p_0)/n}}\,\sqrt{{(N-n)/(N-1)}}}}
    \qquad
    t = \frac{{\bar{{x}} - \mu_0}}{{(s/\sqrt{{n}})\,\sqrt{{(N-n)/(N-1)}}}}
    $$

    No intervalo da proporção, o erro-padrão troca $p_0$ por $\hat{{p}}$
    e o quantil é $z$ = {analise.formatar_decimal(plano['z'], 2)}.
    No intervalo da média, o quantil é o da distribuição $t$.
""")

proporcoes = [item for item in resultados if item["tipo"] == "proporcao"]
medias = [item for item in resultados if item["tipo"] == "media"]
for indice, proporcao in enumerate(proporcoes):
    mostrar(grafico_intervalos([proporcao], proporcao["valor_nulo"], "%", "Proporção dos cursos"))
    legenda = ""
    if indice == 0:
        legenda = (
            f"A barra é o intervalo de {analise.formatar_percentual(plano['confianca'], 0)}. "
            "O círculo verde é a estimativa amostral. "
            "O losango vermelho é o parâmetro populacional. "
        )
    st.caption(legenda + f"A linha tracejada é a hipótese nula, em {proporcao['texto_nulo']}.")
for media in medias:
    if media["percentual"]:
        formato = ".1%"
    elif media["coluna"] == "QT_MAT":
        formato = ",.0f"
    else:
        formato = ",.2f"
    mostrar(grafico_intervalos([media], media["valor_nulo"], formato, media["nome"]))
    if media.get("lado") == "maior":
        st.caption(
            "A linha tracejada é o limite da hipótese nula, em "
            f"{media['texto_nulo']}. À esquerda dela, a média fica abaixo de 150 e H0 se mantém."
        )
    else:
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
        f"Intervalo de {analise.formatar_percentual(plano['confianca'], 0)}",
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
            O valor crítico bilateral é {analise.formatar_decimal(resultado['critico'], 2)}.
            Rejeita-se $H_0$ se $|z|$ passar desse valor.
            Erro-padrão do intervalo = {analise.formatar_decimal(resultado['erro_padrao'], 4)}.
            Erro-padrão sob $H_0$ = {analise.formatar_decimal(resultado['erro_padrao_h0'], 4)}.
        """
    else:
        if resultado["percentual"]:
            desvio = f"{analise.formatar_decimal(resultado['desvio'] * 100, 1)} pontos percentuais"
            erro = f"{analise.formatar_decimal(resultado['erro_padrao'] * 100, 2)} pontos percentuais"
        else:
            desvio = analise.formatar_decimal(resultado["desvio"], 3)
            erro = analise.formatar_decimal(resultado["erro_padrao"], 4)
        if resultado.get("lado") == "maior":
            regra = (
                f"O valor crítico unilateral é {analise.formatar_decimal(resultado['critico'], 3)}. "
                "Rejeita-se $H_0$ se $t$ passar desse valor."
            )
        else:
            regra = (
                f"O valor crítico bilateral é {analise.formatar_decimal(resultado['critico'], 3)}. "
                "Rejeita-se $H_0$ se $|t|$ passar desse valor."
            )
        detalhe = f"""
            Desvio-padrão amostral = {desvio}.
            Estatística $t$ = {analise.formatar_decimal(resultado['estatistica'], 2)},
            com {analise.formatar_inteiro(resultado['graus_liberdade'])} graus de liberdade.
            {regra}
            Erro-padrão = {erro}.
        """
    markdown(f"""
        {em_markdown(detalhe)}

        {resultado['condicoes']}

        {texto_conclusao(resultado)}
    """)

markdown(f"""
    ### Limitações

    As matrículas são assimétricas. Alguns cursos muito grandes puxam a média
    para cima da mediana. O intervalo e o teste descrevem essa média. A mediana,
    no painel descritivo, acompanha o curso típico.

    A proporção de mulheres varia de 0% a 100% e a assimetria é leve. A média
    fica perto da mediana. Cada curso pesa igual nessa média. A proporção de
    mulheres entre todas as matrículas, somando os alunos, é outra conta, porque
    os cursos grandes pesam mais.

    Cursos presenciais sem matrícula ficam fora da população, porque a proporção
    de mulheres não existe quando `QT_MAT` é zero.

""")
