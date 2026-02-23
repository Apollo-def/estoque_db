#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script para verificar permissões dos usuários"""
import sqlite3
import os
import json

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'central.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=== USUARIOS E PERMISSOES ===\n")
    cur.execute("SELECT id, nome, email, tipo, pode_cadastrar, permissoes_menu FROM usuarios")
    
    for row in cur.fetchall():
        print(f"Usuário: {row['nome']} (ID: {row['id']})")
        print(f"  Email: {row['email']}")
        print(f"  Tipo: {row['tipo']}")
        print(f"  Pode Cadastrar: {row['pode_cadastrar']}")
        
        if row['permissoes_menu']:
            try:
                permissoes = json.loads(row['permissoes_menu'])
                print(f"  Permissões de Menu:")
                for k, v in permissoes.items():
                    print(f"    - {k}: {v}")
            except:
                print(f"  permissoes_menu (raw): {row['permissoes_menu']}")
        else:
            print(f"  Permissões de Menu: (vazio)")
        print()
    
    conn.close()
else:
    print(f"Banco não encontrado: {db_path}")
