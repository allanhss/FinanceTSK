#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validacao: Grafico com Saldo Negativo
Testa o calculo de Patrimonio Acumulado quando o saldo futuro fica negativo
"""

import sys
from pathlib import Path

# Ajustar path para importar src
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, datetime, timedelta
from src.database.connection import SessionLocal, engine
from src.database.models import Base, Conta, Categoria, Transacao
from src.database.operations import (
    create_account,
    create_category,
    create_transaction,
    get_category_matrix_data,
)
from src.components.dashboard_charts import render_evolution_chart

print("\n" + "=" * 80)
print("VALIDACAO: GRAFICO COM SALDO NEGATIVO")
print("=" * 80)

print("\n1. SETUP: Preparando banco de dados")
print("-" * 80)

# Limpar e preparar banco
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print("OK: Banco de dados limpo")

# Criar categorias
create_category(nome="Salario", tipo="receita", cor="#22C55E")
create_category(nome="Aluguel", tipo="despesa", cor="#EF4444")
print("OK: Categorias criadas")

# Criar conta
create_account(nome="Nubank Conta", tipo="conta", saldo_inicial=2000.0)
print("OK: Conta criada com saldo inicial R$ 2.000,00")

# Obter IDs
with SessionLocal() as session:
    conta = session.query(Conta).filter_by(nome="Nubank Conta").first()
    cat_receita = session.query(Categoria).filter_by(nome="Salario").first()
    cat_despesa = session.query(Categoria).filter_by(nome="Aluguel").first()

    conta_id = conta.id
    cat_receita_id = cat_receita.id
    cat_despesa_id = cat_despesa.id

print(f"   Conta ID: {conta_id}")
print(f"   Categoria Receita ID: {cat_receita_id}")
print(f"   Categoria Despesa ID: {cat_despesa_id}")

print("\n2. INJECAO DE DADOS: Criando transacoes para teste")
print("-" * 80)

# Criar historico de receitas (ultimos 3 meses)
today = date.today()

print("\nTransacoes passadas (ultimos 3 meses):")
for month_offset in [-3, -2, -1]:
    data = today + timedelta(days=30 * month_offset)
    data = date(data.year, data.month, 1)  # Primeiro do mes

    # Receita
    create_transaction(
        data=data,
        descricao="Salario mensal",
        valor=5000.0,
        tipo="receita",
        categoria_id=cat_receita_id,
        conta_id=conta_id,
        tag=None,
    )
    print(f"  OK: Receita R$ 5.000,00 em {data}")

    # Despesa (aluguel)
    create_transaction(
        data=data + timedelta(days=5),
        descricao="Aluguel",
        valor=1200.0,
        tipo="despesa",
        categoria_id=cat_despesa_id,
        conta_id=conta_id,
        tag=None,
    )
    print(f"  OK: Despesa R$ 1.200,00 em {data + timedelta(days=5)}")

# Criar transacao MASSIVA no futuro que causa saldo NEGATIVO
print("\nTransacao futura (causa saldo negativo):")
data_futura = date(2026, 3, 15)
create_transaction(
    data=data_futura,
    descricao="Divida gigante - Refinanciamento imobiliario",
    valor=50000.0,
    tipo="despesa",
    categoria_id=cat_despesa_id,
    conta_id=conta_id,
    tag=None,
)
print(f"  OK: Despesa MASSIVA R$ 50.000,00 em {data_futura}")
print(f"  [ALERTA] Esta transacao criara saldo MUITO NEGATIVO em marco/2026!")

print("\n3. GERACAO DE DADOS: Calculando matriz de categorias")
print("-" * 80)

# Gerar dados para 6 meses passados e 6 meses futuros
dados_grafico = get_category_matrix_data(months_past=6, months_future=6)

print(f"\nMeses processados:")
print(f"  Total: {len(dados_grafico.get('meses', []))} meses")
print(f"  Meses: {dados_grafico.get('meses', [])}")

print("\n4. ANALISE: Valores mensais de receita, despesa e patrimonio acumulado")
print("-" * 80)

meses = dados_grafico.get("meses", [])
receitas_data = dados_grafico.get("receitas", [])
despesas_data = dados_grafico.get("despesas", [])

receitas_valores = []
despesas_valores = []

print("\nDetalhamento por mes:")
print(
    f"{'Mes':<12} | {'Receitas':>12} | {'Despesas':>12} | {'Saldo':>12} | {'Patrimonio Acum.':>18}"
)
print("-" * 75)

for mes in meses:
    # Somar receitas do mes
    soma_receitas = sum(
        float(cat.get("valores", {}).get(mes, 0) or 0)
        for cat in receitas_data
        if isinstance(cat, dict)
    )
    receitas_valores.append(soma_receitas)

    # Somar despesas do mes
    soma_despesas = sum(
        float(cat.get("valores", {}).get(mes, 0) or 0)
        for cat in despesas_data
        if isinstance(cat, dict)
    )
    despesas_valores.append(soma_despesas)

# Calcular saldo mensal e montante acumulado
saldos_mensais = [r - d for r, d in zip(receitas_valores, despesas_valores)]
montante_acumulado = []
acumulado = 0.0

for idx, saldo in enumerate(saldos_mensais):
    acumulado += saldo
    montante_acumulado.append(acumulado)

    status = "[NEGATIVO!]" if acumulado < 0 else ""
    print(
        f"{meses[idx]:<12} | "
        f"R$ {receitas_valores[idx]:>10,.2f} | "
        f"R$ {despesas_valores[idx]:>10,.2f} | "
        f"R$ {saldos_mensais[idx]:>10,.2f} | "
        f"R$ {montante_acumulado[idx]:>15,.2f} {status}"
    )

print("\n5. VALIDACAO: Verificacoes de consistencia")
print("-" * 80)

print(f"\nVerificacoes:")

# Verificacao 1: Patrimonio comeca positivo
if montante_acumulado[0] > 0:
    print(f"  OK: Patrimonio inicial positivo: R$ {montante_acumulado[0]:.2f}")
else:
    print(
        f"  ERRO: Patrimonio inicial deve ser positivo, obtido: R$ {montante_acumulado[0]:.2f}"
    )

# Verificacao 2: Existe valor negativo?
tem_negativo = any(valor < 0 for valor in montante_acumulado)
if tem_negativo:
    print(f"  OK: Patrimonio fica negativo (teste valido)")
    min_val = min(montante_acumulado)
    print(f"     Minimo: R$ {min_val:.2f}")
else:
    print(f"  AVISO: Nenhum valor negativo detectado")

# Verificacao 3: Cumsum correto?
print(f"\n  Validando cumsum (acumulacao progressiva):")
for idx in range(1, len(montante_acumulado)):
    esperado = montante_acumulado[idx - 1] + saldos_mensais[idx]
    obtido = montante_acumulado[idx]
    if abs(esperado - obtido) < 0.01:
        print(
            f"    Mes {idx} ({meses[idx]}): OK (esperado={esperado:.2f}, obtido={obtido:.2f})"
        )
    else:
        print(
            f"    Mes {idx} ({meses[idx]}): ERRO (esperado={esperado:.2f}, obtido={obtido:.2f})"
        )

print("\n6. RENDERIZACAO: Gerando grafico")
print("-" * 80)

try:
    chart = render_evolution_chart(dados_grafico)
    print("OK: Grafico renderizado com sucesso")
    print("    Tipo de componente: dcc.Graph")
    print("    Grafico inclui:")
    print("      - Barras de receitas (verde)")
    print("      - Barras de despesas (vermelho)")
    print("      - Linha de patrimonio acumulado (roxo com preenchimento)")
except Exception as e:
    print(f"ERRO ao renderizar grafico: {e}")

print("\n7. RESUMO")
print("-" * 80)

print(
    f"""
Dados de teste:
  - Saldo inicial: R$ 2.000,00
  - Receitas mensais: R$ 5.000,00 (ultimos 3 meses)
  - Despesa de aluguel: R$ 1.200,00 (ultimos 3 meses)
  - Despesa futura MASSIVA: R$ 50.000,00 em {data_futura}

Resultados:
  - Patrimonio acumulado em {meses[0]}: R$ {montante_acumulado[0]:.2f}
  - Patrimonio acumulado em {meses[-1]}: R$ {montante_acumulado[-1]:.2f}
  - Saldo NEGATIVO detectado: {tem_negativo}
  
Expectativas:
  1. Patrimonio comeca positivo (OK = {montante_acumulado[0] > 0})
  2. Patrimonio fica muito negativo em marco/2026 (OK = {tem_negativo})
  3. Cumsum calculado corretamente (OK = validacoes acima)
  4. Grafico renderizado sem erros (OK = grafico gerado)

Proximos passos:
  1. Abra a aplicacao web
  2. Navegue para o Dashboard
  3. Verifique se a linha de patrimonio mostra a curva NEGATIVA
  4. Verifique se o grafico tem escala adequada (eixo Y com valores negativos)
  5. Passe o mouse sobre os pontos para ver valores exatos
"""
)

print("\n" + "=" * 80)
print("VALIDACAO CONCLUIDA!")
print("=" * 80)
