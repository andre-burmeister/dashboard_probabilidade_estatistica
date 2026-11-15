"""Painel 2: análise descritiva da amostra aleatória simples."""

import streamlit as st

import analise
from interface import aplicar_estilo, carregar_estudo, markdown, painel_amostra

aplicar_estilo()
populacao, amostra, plano, _metadados = carregar_estudo()

st.title("Análise descritiva da amostra")
markdown(f"""
    A amostra tem **{analise.formatar_inteiro(plano['n'])}** cursos,
    sorteados sem reposição com a semente {plano['semente']}.
    Os gráficos repetem os da população. A diferença é a medida da amostra
    menos a medida da população, e vem da variabilidade amostral.
""")
painel_amostra(amostra, populacao)
