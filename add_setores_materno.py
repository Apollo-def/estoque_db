#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar setores ao banco hospital_presidente_materno
"""
import sqlite3
import os

# Lista de setores a serem adicionados
SETORES = [
    
    "ADMINISTRAÇÃO (0%)",
    "ALMOXARIFADO (0%)",
    "ALA A 3° ANDAR (20%)",
    "ALA A 4° ANDAR (20%)",
    "ALA D 3° ANDAR (20%)",
    "ALA E 3° ANDAR (20%)",
    "ALA E 4° ANDAR (20%)",
    "ALMOXARIFADO ESCADARIA (0%)",
    "ALMOXARIFE (0%)",
    "AMBULATÓRIO GERAL (20%)",
    "AMBULATÓRIO OBSTÉTRICO (20%)",
    "AMBULATÓRIO PEDIÁTRICO (20%)",
    "APOIO PRÉ-PARTO E CENTRO CIRÚRGICO (20%)",
    "BANCO DE LEITE (20%)",
    "BANCO DE TUMORES (20%)",
    "CCI - CENTRO CIRÚRGICO INFANTIL (20%)",
    "CCO - CENTRO CIRÚRGICO OBSTÉTRICO (20%)",
    "CME (40%)",
    "COBERTURA (0%)",
    "COLETORES (40%)",
    "FARMÁCIA (20%)",
    "LABORATÓRIO BANCO DE SANGUE (20%)",
    "PÁTIO 1° e 2° ANDAR (0%)",
    "PRÉ-PARTO (20%)",
    "RECEPÇÃO ACOLHIMENTO (20%)",
    "SECRETARIAS 3° e 4° ANDAR (0%)",
    "SUBSOLO (0%)",
    "UTI e UCI - NEO (20%)",
    "UTI PEDIÁTRICA (20%)"
]

def adicionar_setores():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hospital_presidente_materno.db')
    
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Verificar se a tabela setores existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='setores'")
    if not cur.fetchone():
        print("Erro: Tabela 'setores' não existe!")
        conn.close()
        return False
    
    # Contador de setores adicionados
    adicionados = 0
    ja_existem = 0
    
    for setor in SETORES:
        # Verificar se setor já existe
        cur.execute("SELECT id FROM setores WHERE nome = ?", (setor,))
        if cur.fetchone():
            print(f"  - {setor} (já existe)")
            ja_existem += 1
        else:
            # Inserir setor
            cur.execute("""
                INSERT INTO setores (nome, ativo)
                VALUES (?, 1)
            """, (setor,))
            print(f"  + {setor}")
            adicionados += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nConcluído!")
    print(f"  Setores adicionados: {adicionados}")
    print(f"  Setores já existentes: {ja_existem}")
    print(f"  Total: {len(SETORES)}")
    
    return True

if __name__ == "__main__":
    print("Adicionando setores ao banco hospital_presidente_materno...")
    adicionar_setores()
