"""Painel 1: análise descritiva da população."""

import streamlit as st

import analise
from interface import aplicar_estilo, carregar_estudo, markdown, painel_populacao

aplicar_estilo()
populacao, _amostra, _plano, _metadados = carregar_estudo()

st.title("Análise descritiva da população")
markdown(f"""
    Cada número desta página usa os
    {analise.formatar_inteiro(len(populacao))} cursos presenciais
    com ao menos um matriculado. A unidade é o curso.
""")
painel_populacao(populacao)
