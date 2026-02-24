# Rotas de Autenticação
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import limiter
import json
import re

auth_bp = Blueprint('auth', __name__)


def _validar_senha_forte(senha: str) -> str | None:
    """
    Retorna mensagem de erro se a senha for fraca, ou None se for válida.
    Regras: mínimo 8 chars, ao menos 1 maiúscula, 1 minúscula, 1 dígito.
    """
    if len(senha) < 8:
        return 'A senha deve ter pelo menos 8 caracteres.'
    if not re.search(r'[A-Z]', senha):
        return 'A senha deve conter pelo menos uma letra maiúscula.'
    if not re.search(r'[a-z]', senha):
        return 'A senha deve conter pelo menos uma letra minúscula.'
    if not re.search(r'\d', senha):
        return 'A senha deve conter pelo menos um número.'
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    """Rota de login"""
    from app import db, Usuario
    from database_config import get_all_units
    from datetime import datetime, timezone

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email).first()

        # Verificar bloqueio por brute force
        if usuario and usuario.esta_bloqueado():
            flash(
                'Conta temporariamente bloqueada por excesso de tentativas. '
                'Tente novamente em 15 minutos.',
                'danger'
            )
            return render_template('login.html')

        if usuario and usuario.ativo and check_password_hash(usuario.senha, senha):
            # Login bem-sucedido — resetar contador de falhas
            usuario.resetar_tentativas()
            db.session.commit()

            # Proteção contra session fixation: limpar sessão antiga antes de popular
            session.clear()
            session.permanent = True

            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            session['user_email'] = usuario.email
            session['user_tipo'] = usuario.tipo
            session['pode_cadastrar'] = getattr(usuario, 'pode_cadastrar', 1)

            if usuario.permissoes_menu:
                try:
                    session['permissoes_menu'] = json.loads(usuario.permissoes_menu)
                except Exception:
                    if usuario.tipo == 'admin':
                        session['permissoes_menu'] = {
                            'dashboard': True, 'produtos': True, 'movimentacoes': True,
                            'usuarios': True, 'unidades': True, 'fornecedores': True,
                            'categorias': True, 'setores': True, 'configuracoes': True,
                            'relatorios': True, 'backup': True, 'logs': True
                        }
                    else:
                        session['permissoes_menu'] = {}
            else:
                if usuario.tipo == 'admin':
                    session['permissoes_menu'] = {
                        'dashboard': True, 'produtos': True, 'movimentacoes': True,
                        'usuarios': True, 'unidades': True, 'fornecedores': True,
                        'categorias': True, 'setores': True, 'configuracoes': True,
                        'relatorios': True, 'backup': True, 'logs': True
                    }
                else:
                    session['permissoes_menu'] = {}

            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(url_for('main.selecionar_unidade'))
        else:
            # Registrar tentativa falha apenas se o usuário existe
            if usuario:
                usuario.registrar_tentativa_falha()
                db.session.commit()
            # Mensagem genérica — não revela se o email existe ou não
            flash('Email ou senha incorretos.', 'danger')

    return render_template('login.html')


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Rota de cadastro de novo usuário"""
    from app import db, Usuario
    from database_config import get_all_units

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        # Validação de força da senha
        erro_senha = _validar_senha_forte(senha)
        if erro_senha:
            flash(erro_senha, 'danger')
            return render_template('cadastro.html')

        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return render_template('cadastro.html')

        # Validação básica de formato de e-mail
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            flash('Endereço de e-mail inválido.', 'danger')
            return render_template('cadastro.html')

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email já está cadastrado!', 'danger')
            return render_template('cadastro.html')

        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash)

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça seu login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('Erro ao cadastrar usuário!', 'danger')

    unidades = get_all_units() if session.get('user_tipo') == 'admin' else {}
    return render_template('cadastro.html', get_all_units=lambda: unidades)


@auth_bp.route('/logout')
def logout():
    """Rota de logout"""
    session.clear()
    flash('Você saiu do sistema!', 'info')
    return redirect(url_for('auth.login'))
