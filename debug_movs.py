#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug para ver movimentações e responsável"""
import sqlite3
import os

# Verificar banco central
central_path = os.path.join(os.path.dirname(__file__), 'instance', 'central.db')
conn_central = sqlite3.connect(central_path)
conn_central.row_factory = sqlite3.Row
cur_central = conn_central.cursor()

# Listar unidades
print("=== UNIDADES ===")
cur_central.execute("SELECT id, nome, database FROM unidades")
for row in cur_central.fetchall():
    print(f"  {row['id']}: {row['nome']} -> {row['database']}")

conn_central.close()

# Verificar movimentações em cada banco de unidade
print("\n=== MOVIMENTACOES POR UNIDADE ===")
for db_file in os.listdir('instance'):
    if db_file.endswith('.db') and db_file not in ['central.db', 'usuarios.db']:
        unit_path = os.path.join('instance', db_file)
        if os.path.isfile(unit_path):
            try:
                conn = sqlite3.connect(unit_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # Verificar se tem movimentacoes
                cur.execute("SELECT COUNT(*) as total FROM movimentacoes")
                total = cur.fetchone()[0]
                
                if total > 0:
                    print(f"\n--- {db_file} ---")
                    cur.execute("SELECT id, tipo, quantidade, usuario_responsavel_id FROM movimentacoes ORDER BY id DESC LIMIT 5")
                    for row in cur.fetchall():
                        print(f"  Mov {row['id']}: tipo={row['tipo']}, qtd={row['quantidade']}, responsavel_id={row['usuario_responsavel_id']}")
                
                conn.close()
            except Exception as e:
                print(f"Erro em {db_file}: {e}")
