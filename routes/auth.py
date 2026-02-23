# Rotas de Autenticação
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota de login"""
    from app import db, Usuario
    from database_config import get_all_units
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.ativo and check_password_hash(usuario.senha, senha):
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            session['user_email'] = usuario.email
            session['user_tipo'] = usuario.tipo
            session['pode_cadastrar'] = getattr(usuario, 'pode_cadastrar', 1)
            
            if usuario.permissoes_menu:
                try:
                    session['permissoes_menu'] = json.loads(usuario.permissoes_menu)
                except:
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
            flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Rota de cadastro de novo usuário"""
    from app import db, Usuario
    from database_config import get_all_units
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
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
        except Exception as e:
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
