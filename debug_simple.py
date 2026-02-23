#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug simples para verificar permissões"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'central.db')
print(f"DB Path: {db_path}")
print(f"DB Exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Verificar estrutura da tabela
print("\n=== ESTRUTURA DA TABELA USUARIOS ===")
cur.execute("PRAGMA table_info(usuarios)")
for col in cur.fetchall():
    print(f"  {col[1]}: {col[2]}")

# Verificar usuários
print("\n=== USUARIOS ===")
cur.execute("SELECT id, nome, tipo, pode_cadastrar FROM usuarios")
for row in cur.fetchall():
    admin = row['tipo'] == 'admin'
    pode = row['pode_cadastrar']
    # Simular a lógica de permissão
    tem_acesso = admin or pode
    print(f"  {row['nome']} | tipo={row['tipo']} | pode_cadastrar={pode} | ACESSO={tem_acesso}")

conn.close()
