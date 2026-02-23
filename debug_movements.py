#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script para verificar movimentações"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hospital_presidente_dutra.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Verificar estrutura da tabela movimentacoes
    print("=== ESTRUTURA DA TABELA MOVIMENTACOES ===")
    cur.execute("PRAGMA table_info(movimentacoes)")
    for row in cur.fetchall():
        print(f"  {row}")
    
    print("\n=== ULTIMAS MOVIMENTACOES ===")
    cur.execute("""
        SELECT m.*, p.nome as produto_nome
        FROM movimentacoes m
        LEFT JOIN produtos p ON m.produto_id = p.id
        ORDER BY m.id DESC
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        print(f"\nMovimentação ID: {row['id']}")
        print(f"  Tipo: {row['tipo']}")
        print(f"  Produto: {row['produto_nome']}")
        print(f"  Quantidade: {row['quantidade']}")
        print(f"  usuario_responsavel_id: {row['usuario_responsavel_id']}")
        print(f"  Data: {row['data_movimentacao']}")
    
    # Verificar usuarios no banco central
    print("\n=== USUARIOS NO BANCO CENTRAL ===")
    central_path = os.path.join(os.path.dirname(__file__), 'instance', 'central.db')
    if os.path.exists(central_path):
        conn2 = sqlite3.connect(central_path)
        conn2.row_factory = sqlite3.Row
        cur2 = conn2.cursor()
        cur2.execute("SELECT id, nome, email FROM usuarios LIMIT 10")
        for row in cur2.fetchall():
            print(f"  ID: {row['id']}, Nome: {row['nome']}, Email: {row['email']}")
        conn2.close()
    else:
        print("  Banco central não encontrado!")
    
    conn.close()
else:
    print(f"Banco não encontrado: {db_path}")
