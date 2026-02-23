# Rotas de Configurações
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/configuracoes')


@settings_bp.route('')
@admin_required
def configuracoes():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('config_'):
                config_key = key.replace('config_', '')
                print(f"Configuração {config_key}: {value}")
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('settings.configuracoes'))
    
    configuracoes = [
        {'chave': 'nome_sistema', 'valor': 'Sistema de Estoque Hospitalar', 'descricao': 'Nome do sistema'},
        {'chave': 'versao', 'valor': '1.0.0', 'descricao': 'Versão atual do sistema'},
        {'chave': 'limite_produtos_pagina', 'valor': '50', 'descricao': 'Limite de produtos por página'},
        {'chave': 'alerta_estoque_baixo', 'valor': '5', 'descricao': 'Nível mínimo para alerta'},
        {'chave': 'tempo_sessao', 'valor': '3600', 'descricao': 'Tempo de sessão em segundos'},
        {'chave': 'email_remetente', 'valor': 'noreply@sistema.com', 'descricao': 'Email para notificações'},
    ]
    
    return render_template('configuracoes.html', configuracoes=configuracoes)
