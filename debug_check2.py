#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('instance/central.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT id, nome, tipo, pode_cadastrar FROM usuarios')
for row in cur.fetchall():
    tipo = row['tipo']
    pode = row['pode_cadastrar']
    nome = row['nome']
    # Simular a lógica do template
    template_check = tipo == 'admin' or pode
    print(f'{nome}: tipo={tipo}, pode_cadastrar={pode} ({type(pode).__name__}), template_check={template_check}')
conn.close()
