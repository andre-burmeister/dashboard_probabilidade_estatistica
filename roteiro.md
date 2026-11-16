# Roteiro do vídeo (máximo 5 minutos)

Fala única, sem cortes. São cerca de 520 palavras. Lida em ritmo calmo, duas palavras por segundo, dura cerca de **4 minutos e 20 segundos**. Numa leitura lenta, fica perto de **4 minutos e 40**. A margem some se houver pausa em silêncio.

Antes de gravar, leia a fala em voz alta com o cronômetro. Se o ensaio ficar entre 4:10 e 4:45, grave assim. Se passar de 4:45, emende uma frase na outra. Não apague trecho no meio da gravação e não repita número errado: siga na frase seguinte.

Não abra com saudação. A primeira frase já entra no critério da base de dados.

## O que fica na tela

Três cliques, feitos enquanto a frase continua. Não pare para a página carregar e não role no meio de um número.

| Quando você disser | Página | Onde parar |
| --- | --- | --- |
| «A base é o Censo…» | Base e amostra | Topo. Não role. |
| «O tamanho amostral…» | Base e amostra | Um scroll até Dimensionamento da amostra. Pare. |
| «Na população, 15,8%…» | Amostra | Tabela de comparação, no topo. Não role. |
| «Intervalo e teste usam só…» | Inferência | Role até a tabela das quatro linhas e fique nela até o fim. |

A tabela de inferência mostra duas casas nas proporções (15,77%, 12,03%). Fale uma casa, como está escrito abaixo. Não corrija ao vivo.

## Fala

Os tempos são o relógio do ensaio, no ritmo de duas palavras por segundo.

### 0:00 — Base e população

A base é o Censo da Educação Superior de 2024, do Inep: cerca de 720 mil registros de curso ou de local de oferta, com 223 variáveis.

A unidade amostral é o curso presencial de graduação com ao menos uma matrícula. A população tem 32.765 cursos, em 2.420 instituições, e pouco mais de 5 milhões de matrículas. Os parâmetros são licenciatura, gratuidade, média de matrículas e proporção média de mulheres no curso.

### 0:35 — Tamanho e sorteio da amostra

O tamanho da amostra foi calculado para uma confiança de 95%, margem de erro de 4% e proporção de planejamento de 50%, para maximizar a variância. Isso gera uma amostra de 590 cursos.

A seleção é uma amostra aleatória simples no NumPy, usando sempre a mesma semente (2024). A mesma amostra serve às quatro inferências.

### 1:10 — População e amostra

Na população, 15,8% dos cursos são licenciaturas e 31,7% são gratuitos. A média de matrículas é 153,8 e a mediana é 91, porque cursos grandes puxam a média. A proporção média de mulheres é 55,2%.

Na amostra, licenciatura cai para 12,0% e gratuidade para 29,5%. A média sobe para 165,4 e a mediana para 103. A proporção média de mulheres fica em 54,6%. O desenho se repete. Os valores se deslocam.

### 1:50 — Como a inferência foi feita

Intervalo e teste usam só os 590 cursos. A população entra depois, para conferir. A significância é 5%. Proporções usam intervalo de Wald e teste z. Médias usam intervalo e teste t, com correção de população finita.

### 2:05 — Licenciatura

A hipótese nula é 20%, e a alternativa é diferente de 20%. A estimativa é 12,0%, e o intervalo vai de 9,4% a 14,6%. O valor-p fica abaixo de 0,001, e rejeitamos a nula. A população tem 15,8%, também distante de 20%, então a decisão acerta. O intervalo não cobre esses 15,8%. A amostra ficou 3,7 pontos abaixo, além da margem.

### 2:35 — Gratuidade

A hipótese nula é 30%, e a alternativa é diferente de 30%. A estimativa é 29,5%, e o intervalo vai de 25,8% a 33,1%. Cobre os 30% e também o parâmetro, de 31,7%. O valor-p é 0,79, e não rejeitamos a nula. A população difere de 30% por pouco, e esta amostra não detecta a diferença.

### 3:05 — Matrículas

A hipótese nula é uma média abaixo de 150, e só uma média amostral bem mais alta a rejeita. A estimativa é 165,4, e o intervalo vai de 146,8 a 184,1, cobrindo os 153,8 da população. O valor-p é 0,052. A 5% não rejeitamos a nula, embora a população esteja pouco acima de 150.

### 3:30 — Mulheres

A hipótese nula é 50%, e a alternativa é diferente de 50%. A estimativa é 54,6%, e o intervalo vai de 52,6% a 56,6%. O valor-p fica abaixo de 0,001, e rejeitamos a nula. A população tem 55,2%. O intervalo cobre esse valor, e a decisão acerta. Nessa média cada curso pesa igual, e um curso grande não a puxa.

### 4:00 — Comparação

Três intervalos contêm o parâmetro. O da licenciatura não. Longe da nula, o teste rejeita: licenciatura e mulheres. Perto dela, ou com desvio grande, não rejeita: gratuidade e matrículas. A população só entra aqui para essa conferência.

## Cola, se travar num número

| | População | Amostra | Intervalo de 95% | Decisão |
| --- | --- | --- | --- | --- |
| Licenciatura | 15,8% | 12,0% | 9,4% a 14,6% | Rejeita 20%. O intervalo não cobre a população. |
| Curso gratuito | 31,7% | 29,5% | 25,8% a 33,1% | Não rejeita 30%. O intervalo cobre a população. |
| Média de matrículas | 153,8 (mediana 91) | 165,4 (mediana 103) | 146,8 a 184,1 | Não rejeita «abaixo de 150». Valor-p 0,052. |
| Média de mulheres | 55,2% | 54,6% | 52,6% a 56,6% | Rejeita 50%. O intervalo cobre a população. |

Outros valores que não precisam ser procurados na tela: 32.765 cursos, 2.420 instituições, pouco mais de 5 milhões de matrículas, n = 590, semente 2024, confiança 95%, margem 4 pontos, p de planejamento 50%.

Na tabela, o valor-p da gratuidade aparece como 0,7856: fale 0,79. O das matrículas aparece como 0,0519: fale 0,052. NumPy se lê «num pai». Wald se lê «uóld».
