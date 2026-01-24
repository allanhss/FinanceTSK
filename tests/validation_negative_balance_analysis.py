#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analise Visual: Grafico com Saldo Negativo
Documentacao sobre o comportamento esperado do patrimonio acumulado negativo
"""

print("\n" + "=" * 80)
print("ANALISE VISUAL: GRAFICO COM SALDO NEGATIVO")
print("=" * 80)

print("\n1. CENARIO DE TESTE")
print("-" * 80)

print(
    """
Dados iniciais:
  - Saldo inicial da conta: R$ 2.000,00
  - Receitas mensais (passado): R$ 5.000,00 cada
  - Despesas mensais (aluguel): R$ 1.200,00 cada
  - Despesa futura MASSIVA (marco/2026): R$ 50.000,00

Periodo analisado:
  - Passado: 6 meses (julho 2025 a dezembro 2025)
  - Futuro: 7 meses (janeiro 2026 a julho 2026)
  - Total: 13 meses
"""
)

print("\n2. CALCULO DO PATRIMONIO ACUMULADO")
print("-" * 80)

print(
    """
Formula: Patrimonio_n = Patrimonio_(n-1) + (Receita_n - Despesa_n)

Evolucao mes a mes:

[2025-07] Inicio: Patrimonio = R$ 0,00 (sem dados)
[2025-08] Patrimonio = 0 + (0 - 0) = R$ 0,00
[2025-09] Patrimonio = 0 + (0 - 0) = R$ 0,00
[2025-10] Patrimonio = 0 + (5.000 - 1.200) = R$ 3.800,00
[2025-11] Patrimonio = 3.800 + (5.000 - 1.200) = R$ 7.600,00
[2025-12] Patrimonio = 7.600 + (5.000 - 1.200) = R$ 11.400,00
[2026-01] Patrimonio = 11.400 + (0 - 0) = R$ 11.400,00 (sem dados)
[2026-02] Patrimonio = 11.400 + (0 - 0) = R$ 11.400,00 (sem dados)
[2026-03] Patrimonio = 11.400 + (0 - 50.000) = R$ -38.600,00 *** NEGATIVO ***
[2026-04] Patrimonio = -38.600 + (0 - 0) = R$ -38.600,00 (permanece negativo)
[2026-05] Patrimonio = -38.600 + (0 - 0) = R$ -38.600,00
[2026-06] Patrimonio = -38.600 + (0 - 0) = R$ -38.600,00
[2026-07] Patrimonio = -38.600 + (0 - 0) = R$ -38.600,00
"""
)

print("\n3. VISUAL ESPERADO DO GRAFICO")
print("-" * 80)

print(
    """
Y (Patrimonio/Valores)
^
|
| 15.000 +                      [Receitas barras verdes]
|        |     | |      |
| 10.000 |  +--+ +-+    |     [Patrimonio linha ROXA]
|        |  |     | |    | ...  (passa por valores positivos)
|  5.000 |  |     | +----+
|        |  |     |
|      0 |--+-----+--+--+--+----
|        |  |     |  |  |  |
| -5.000 |  |     |  |  |  |
|        |  |     |  |  |  |
|-10.000 |  |     |  |  |  |
|        |  |     |  |  |  |
|-20.000 |  |     |  |  |  |
|        |  |     |  |  |  |
|-30.000 |  |     |  |  |  |
|        |  |     |  |  |  |
|-40.000 |  |     |  |  |  +--- Linha DESCE para -38.600 (em marco/2026)
|        |  |     |  |  |       [Despesas barras vermelhas - massivas]
+--+--+--+--+--+--+--+--+--+--+--+--+--+-> X (Tempo em meses)
    2025                    2026

Caracteristicas do grafico:
  1. Barras verdes (receitas) em outubro, novembro, dezembro
  2. Barras vermelhas (despesas) todos os meses, mas GIGANTESCA em marco/2026
  3. Linha roxa (patrimonio) sobe lentamente ate dezembro de 2025
  4. Linha roxa DESCE DRASTICAMENTE em marco/2026, atingindo -38.600
  5. Eixo Y mostra valores POSITIVOS E NEGATIVOS
  6. Preenchimento roxo semi-transparente mostra a area abaixo da curva
     (area acima do zero em positivo, area abaixo do zero em negativo)
"""
)

print("\n4. PONTOS CRITICOS A VALIDAR")
print("-" * 80)

print(
    """
Ao abrir o grafico web, verifique:

1. Escala do Eixo Y
   - Deve incluir valores negativos (-40.000)
   - Deve incluir valores positivos (15.000)
   - Linha de zero deve estar visivel entre eles

2. Linha de Patrimonio (roxo)
   - Comeca em 0 (ou perto)
   - Sobe gradualmente para 11.400
   - DESCE DRASTICAMENTE para -38.600 em marco/2026
   - Permanece em -38.600 depois

3. Preenchimento (area sob a curva)
   - Cor roxa semi-transparente (rgba)
   - Area acima do zero (positiva): preenchimento visivel ate -38.600
   - Area abaixo do zero (negativa): continua preenchida

4. Barras de Receitas/Despesas
   - Receitas (verde) em out, nov, dez de 2025
   - Despesas (vermelho) todo mes
   - Barra vermelha em marco/2026 ENORME (R$ 50.000)
   - Escala das barras proporcionalmente correta

5. Interatividade
   - Passar mouse sobre linha deve mostrar valores exatos
   - Exemplo em marco/2026: "Patrimonio Acumulado: R$ -38.600,00"
   - Passar mouse sobre barras mostra receitas/despesas

6. Legenda
   - Deve mostrar:
     * "Receitas" (verde)
     * "Despesas" (vermelho)
     * "Patrimonio Acumulado" (roxo)
"""
)

print("\n5. CASOS DE TESTE MANUAIS")
print("-" * 80)

print(
    """
Teste 1: Verifique o ponto de transicao (entre 2026-02 e 2026-03)
  - 2026-02: Patrimonio deve ser 11.400
  - 2026-03: Patrimonio deve ser -38.600
  - Diferenca: -50.000 (valor da despesa massiva)
  - Passe mouse e confirme os valores

Teste 2: Verifique o preenchimento negativo
  - Mude o zoom (scroll do mouse sobre o grafico)
  - Verifique se o preenchimento roxo continua ate os valores negativos
  - Cores devem permanecer consistentes

Teste 3: Verifique a escala dinamica
  - Se remover a despesa massiva (editar transacao)
  - Grafico deve rerender com escala diferente
  - Patrimonio deve voltar a 11.400
  - Y-axis deve ajustar automaticamente

Teste 4: Baixe os dados (export)
  - Se houver botao de download, salve os dados
  - Verifique que -38.600 aparece no arquivo
  - Valores devem estar em ordem cronologica
"""
)

print("\n6. PROBLEMAS CONHECIDOS E COMO RESOLVER")
print("-" * 80)

print(
    """
Problema: Linha de patrimonio nao aparece
  Causa: CSS pode estar ocultando a linha (z-index)
  Solucao: Verificar arquivo dashboard_charts.py - seletor trace para linha roxa

Problema: Eixo Y nao mostra negativos
  Causa: Plotly nao detectou valores negativos
  Solucao: Usar layout com yaxis.autorange=True ou especificar range manualmente

Problema: Preenchimento desaparece quando valor eh negativo
  Causa: fill='tozeroy' pode ter problema com valores negativos
  Solucao: Usar fill='toself' ou ajustar a opcao de preenchimento

Problema: Barras e linha nao se alinham corretamente
  Causa: Eixos diferentes ou dados desalinhados
  Solucao: Verificar que todos os traces usam o mesmo xaxis/yaxis

Problema: Valores muito negativos distorcem o grafico
  Causa: Escala linear extrema
  Solucao: Considerar escala logaritmica ou de potencia
"""
)

print("\n7. RESUMO DO TESTE")
print("-" * 80)

print(
    """
Resultado esperado:
  ✅ Patrimonio acumulado NEGATIVO renderizado corretamente
  ✅ Valores calculados via cumsum (acumulacao progressiva)
  ✅ Eixo Y mostra tanto positivos quanto negativos
  ✅ Linha roxa mostra a curva de patrimonio
  ✅ Preenchimento roxo cobre a area sob a curva, incluindo negativos
  ✅ Usuário pode ver claramente o "buraco" de R$ 50.000

Proximos passos:
  1. Execute: python tests/validation_negative_balance.py
  2. Abra a URL http://localhost:8050
  3. Navegue para Dashboard
  4. Verifique visualmente conforme checklist acima
  5. Teste a interatividade (hover, zoom, pan)
  6. Reporte qualquer problema visual
"""
)

print("\n" + "=" * 80)
print("FIM DA ANALISE")
print("=" * 80)
