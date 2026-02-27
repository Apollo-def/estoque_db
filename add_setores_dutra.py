#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar setores ao banco hospital_presidente_dutra
"""
import sqlite3
import os

# Lista de setores a serem adicionados
SETORES = [
    "ADMINISTRAÇÃO 1º ANDAR",
    "SUPERINTENDÊNCIA (20%)",
    "ALMOXARIFADO (20%)",
    "ÁREA EXTERNA DA NUTRIÇÃO",
    "LAVANDERIA",
    "SAME (20%)",
    "BANCO DE SANGUE",
    "LABORATÓRIO 2º ANDAR (20%)",
    "CARDIOVASCULAR 2º ANDAR (20%)",
    "CENTRO CIRÚRGICO (20%)",
    "CENTRO CIRÚRGICO OFTALMOLOGIA – ANEXO (20%)",
    "CLÍNICA CIRÚRGICA 'A'",
    "CLÍNICA MÉDICA 'A' MASCULINA (20%)",
    "CLÍNICA MÉDICA 'B' FEMININA (20%)",
    "CME (20%)",
    "CORREDOR PRINCIPAL 2º ANDAR (20%)",
    "ENDOSCOPIA (20%)",
    "ENSINO E EXTENSÃO",
    "4º ANDAR (20%)",
    "FARMÁCIA (20%)",
    "HEMODINÂMICA (20%)",
    "MARCAÇÃO DE CONSULTA (20%)",
    "NEFROLOGIA (20%)",
    "NEURO-ORTOPEDIA – EXPANSÃO (20%)",
    "NTI",
    "INFRAESTRUTURA (20%)",
    "PAPADOR (20%)",
    "PÁTIO ",
    "ÁREA EXTERNA",
    "ENTRADA INCOR",
    "CALÇADAS EXTERNAS (0%)",
    "RECEPÇÃO",
    "AMBULATÓRIO DE ORTOPEDIA",
    "INTERNAÇÃO (20%)",
    "SECRETARIAS",
    "CORREDORES",
    "RAMPAS E BANHEIROS (3º ANDAR) (20%)",
    "TRANSPLANTE (3º ANDAR) (20%)",
    "UTI CARDIO (20%)",
    "UTI GERAL (20%)"
]

def adicionar_setores():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hospital_presidente_dutra.db')
    
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
    print("Adicionando setores ao banco hospital_presidente_dutra...")
    adicionar_setores()
