#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar produtos ao banco hospital_presidente_dutra
"""
import sqlite3
import os

# Lista de produtos a serem adicionados
PRODUTOS = [
    "ALCOOL EM GEL",
    "ALCOOL LIQUIDO",
    "AVENTAL DESCARTAVEL",
    "BALDE",
    "BECKER CLOREX (CLORO)",
    "BECKPLATER (DETERGENTE)",
    "BORRIFADOR",
    "BRILHO INOX",
    "CERA HOSPITALAR",
    "DESINCRUSTANTE",
    "ESCOVAO OVAL",
    "ESPATULA",
    "ESPONJA DUPLA FACE",
    "FIBRA LEVE (BRANCA)",
    "FIBRA MULTIUSO (VERDE)",
    "LIMPA VIDRO",
    "LUVA AMARELA G",
    "LUVA AMARELA M",
    "LUVA AMARELA P",
    "LUVA TRICOTADA",
    "NAFTALINA",
    "ORDORIZADOR",
    "REMOVEDOR REMOGOLD",
    "SABONETE",
    "SABONETEIRA",
    "SACO COMUM DE 100 LTS",
    "SACO COMUM DE 200 LTS",
    "SACO COMUM DE 60 LTS",
    "SACO HAMPER",
    "VASSOURA NYLON (DESIFENTANTE)",
    "BARBANTE",
    "GADANHO",
    "LIVRO DE PROTOCOLO",
    "LIXEIRA DE 30 LITROS",
    "LIXEIRA DE 60 LITROS",
    "LUVA VERDE G",
    "LUVA VERDE M",
    "LUVA VERDE P",
    "MASCARA BRANCA",
    "MASCARA PFF2S",
    "OCULOS DE PROTEÇÃO",
    "PAPEL HIGIÊNICO",
    "PAPEL INTERFOLHADO",
    "RESMA DE PAPEL CHAMEX",
    "RODO",
    "SACO ALVEJADO (PANO DE CHÃO)",
    "SANTORA PERFEX",
    "SUPORTE DE INTERFOLHADO",
    "SUPORTE DE LT",
    "SUPORTE DE PAPEL HIGIÊNICO",
    "SUPORTE DE PASSADOR DE TETO",
    "TOUCA",
    "VASSOURA GARI",
    "VASSOURA PIACABA",
    "VASSOURA SANITARIA"
]

def adicionar_produtos():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hospital_presidente_dutra.db')
    
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Verificar se a tabela produtos existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produtos'")
    if not cur.fetchone():
        print("Erro: Tabela 'produtos' não existe!")
        conn.close()
        return False
    
    # Contador de produtos adicionados
    adicionados = 0
    ja_existem = 0
    
    for produto in PRODUTOS:
        # Verificar se produto já existe
        cur.execute("SELECT id FROM produtos WHERE nome = ?", (produto,))
        if cur.fetchone():
            print(f"  - {produto} (já existe)")
            ja_existem += 1
        else:
            # Inserir produto com quantidade 0
            cur.execute("""
                INSERT INTO produtos (nome, quantidade, ativo)
                VALUES (?, 0, 1)
            """, (produto,))
            print(f"  + {produto}")
            adicionados += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nConcluído!")
    print(f"  Produtos adicionados: {adicionados}")
    print(f"  Produtos já existentes: {ja_existem}")
    print(f"  Total: {len(PRODUTOS)}")
    
    return True

if __name__ == "__main__":
    print("Adicionando produtos ao banco hospital_presidente_dutra...")
    adicionar_produtos()
