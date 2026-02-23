#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste de acesso aos dados de movimentação"""
from flask import Flask, render_template_string

app = Flask(__name__)

# Simulando dados como dicionários
movimentacao_dict = {
    'id': 1,
    'tipo': 'entrada',
    'quantidade': 10,
    'usuario_responsavel': {'nome': 'Daniel'}  # Dict
}

# Simulando dados como objetos
class AttrDict:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

movimentacao_obj = AttrDict({
    'id': 1,
    'tipo': 'entrada',
    'quantidade': 10,
    'usuario_responsavel': AttrDict({'nome': 'Daniel'})  # Objeto
})

# Testar template com dict
template_dict = """
{% for mov in movimentacoes %}
{{ mov.usuario_responsavel.nome }}
{% endfor %}
"""

print("=== Teste com dict ===")
with app.test_request_context():
    try:
        result = render_template_string(template_dict, movimentacoes=[movimentacao_dict])
        print(f"Dict funciona: '{result.strip()}'")
    except Exception as e:
        print(f"Dict ERRO: {e}")

print("\n=== Teste com objeto ===")
with app.test_request_context():
    try:
        result = render_template_string(template_dict, movimentacoes=[movimentacao_obj])
        print(f"Objeto funciona: '{result.strip()}'")
    except Exception as e:
        print(f"Objeto ERRO: {e}")
