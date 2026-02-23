#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para verificar a estrutura da tabela produtos"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hospital_presidente_dutra.db')

print(f"Verificando banco: {db_path}")
print(f"Existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Verificar tabelas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("\nTabelas existentes:")
    for row in cur.fetchall():
        print(f"  - {row[0]}")
    
    # Verificar estrutura da tabela produtos
    cur.execute("PRAGMA table_info(produtos)")
    print("\nEstrutura da tabela produtos:")
    for row in cur.fetchall():
        print(f"  {row}")
    
    # Verificar produtos existentes
    cur.execute("SELECT id, nome, quantidade FROM produtos LIMIT 10")
    print("\nProdutos existentes (primeiros 10):")
    for row in cur.fetchall():
        print(f"  ID: {row[0]}, Nome: {row[1]}, Qtd: {row[2]}")
    
    conn.close()
else:
    print("Banco não existe!")
