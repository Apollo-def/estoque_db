# Rotas de Gerenciamento de Usuários
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
import json
from routes.helpers import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/tabela')
@admin_required
def tabela():
    """Lista todos os usuários (admin)"""
    from app import db, Usuario
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    usuarios = Usuario.query.all()
    return render_template('tabela.html', usuarios=usuarios)


@users_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Editar usuário"""
    from app import db, Usuario
    from database_config import get_all_units
    from database_manager import db_manager
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    MENUS_DISPONIVEIS = [
        {'id': 'dashboard', 'nome': 'Dashboard', 'icone': 'fas fa-tachometer-alt'},
        {'id': 'produtos', 'nome': 'Produtos', 'icone': 'fas fa-boxes'},
        {'id': 'movimentacoes', 'nome': 'Movimentações', 'icone': 'fas fa-exchange-alt'},
        {'id': 'categorias', 'nome': 'Categorias', 'icone': 'fas fa-tags'},
        {'id': 'setores', 'nome': 'Setores', 'icone': 'fas fa-building'},
        {'id': 'fornecedores', 'nome': 'Fornecedores', 'icone': 'fas fa-truck'},
        {'id': 'unidades', 'nome': 'Unidades', 'icone': 'fas fa-hospital-alt'},
        {'id': 'usuarios', 'nome': 'Usuários', 'icone': 'fas fa-users', 'admin_only': True},
        {'id': 'configuracoes', 'nome': 'Configurações', 'icone': 'fas fa-cog'}
    ]

    usuario = Usuario.query.get_or_404(id)
    unidades = None
    permissoes_atual = json.loads(usuario.permissoes_menu) if usuario.permissoes_menu else {}

    if session.get('user_tipo') != 'admin' and session.get('user_id') != usuario.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        nova_senha = request.form.get('nova_senha')

        usuario_existente = Usuario.query.filter(Usuario.email == email, Usuario.id != id).first()
        if usuario_existente:
            flash('Este email já está cadastrado para outro usuário!', 'danger')
            return render_template('editar.html', 
                                usuario=usuario,
                                menus_disponiveis=MENUS_DISPONIVEIS,
                                permissoes_atual=permissoes_atual,
                                unidades=unidades)

        usuario.nome = nome
        usuario.email = email

        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)

        if session.get('user_tipo') == 'admin':
            usuario.tipo = request.form.get('tipo', usuario.tipo)
            
            unidades = request.form.getlist('unidades')
            usuario.unidades_acesso = json.dumps(unidades) if unidades else None
            
            pode_cadastrar = request.form.get('pode_cadastrar')
            usuario.pode_cadastrar = 1 if pode_cadastrar == '1' or pode_cadastrar == 'on' else 0
            
            permissoes_menu = request.form.getlist('permissoes_menu')
            
            todas_permissoes = {}
            for menu in MENUS_DISPONIVEIS:
                todas_permissoes[menu['id']] = False
            
            for permissao in permissoes_menu:
                if permissao in todas_permissoes:
                    todas_permissoes[permissao] = True
            
            if usuario.tipo == 'admin':
                for menu in MENUS_DISPONIVEIS:
                    todas_permissoes[menu['id']] = True
            
            usuario.permissoes_menu = json.dumps(todas_permissoes)
            permissoes_atual = todas_permissoes
            
            if session.get('user_id') == usuario.id:
                session['permissoes_menu'] = todas_permissoes

        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('users.tabela'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar usuário!', 'danger')

    if session.get('user_tipo') == 'admin':
        unidades = get_all_units()

    # Garantir colunas necessárias
    try:
        conn = db_manager.get_connection(None)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(usuarios)")
        cols = [r['name'] for r in cur.fetchall()]
        
        if 'pode_cadastrar' not in cols:
            cur.execute("ALTER TABLE usuarios ADD COLUMN pode_cadastrar INTEGER DEFAULT 1")
        
        if 'permissoes_menu' not in cols:
            cur.execute("ALTER TABLE usuarios ADD COLUMN permissoes_menu TEXT")
        
        conn.commit()
    except Exception as e:
        pass
    
    return render_template('editar.html', 
                         usuario=usuario, 
                         unidades=unidades,
                         menus_disponiveis=MENUS_DISPONIVEIS,
                         permissoes_atual=permissoes_atual)


@users_bp.route('/novo_usuario', methods=['GET', 'POST'])
@admin_required
def novo_usuario():
    """Criar novo usuário"""
    from app import db, Usuario
    from database_config import get_all_units
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form.get('tipo', 'user')
        unidades = request.form.getlist('unidades')
        pode_cadastrar = request.form.get('pode_cadastrar', '1')
        
        if not nome or not email:
            flash('Preencha todos os campos obrigatórios!', 'danger')
            unidades = get_all_units()
            return render_template('novo_usuario.html', unidades=unidades)
        
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'danger')
            unidades = get_all_units()
            return render_template('novo_usuario.html', unidades=unidades)
        
        senha_hash = generate_password_hash(senha)
        
        unidades_acesso = None
        if unidades:
            unidades_acesso = json.dumps(unidades)
        
        permissoes_menu = {}
        if tipo == 'admin':
            permissoes_menu = {
                'dashboard': True, 'produtos': True, 'movimentacoes': True,
                'categorias': True, 'setores': True, 'fornecedores': True,
                'usuarios': True, 'unidades': True, 'configuracoes': True,
                'relatorios': True, 'backup': True, 'logs': True
            }
        else:
            permissoes_menu = {
                'dashboard': False, 'produtos': False, 'movimentacoes': False,
                'categorias': False, 'setores': False, 'fornecedores': False,
                'usuarios': False, 'unidades': False, 'configuracoes': False,
                'relatorios': False, 'backup': False, 'logs': False
            }
        
        novo_usuario = Usuario(
            nome=nome, 
            email=email, 
            senha=senha_hash, 
            tipo=tipo, 
            unidades_acesso=unidades_acesso, 
            pode_cadastrar=int(pode_cadastrar),
            permissoes_menu=json.dumps(permissoes_menu)
        )
        
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('users.usuarios'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar usuário!', 'danger')
    
    unidades = get_all_units()
    return render_template('novo_usuario.html', unidades=unidades)


@users_bp.route('/usuarios')
@admin_required
def usuarios():
    """Lista todos os usuários"""
    from app import db, Usuario
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    usuarios_lista = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios_lista)


@users_bp.route('/excluir/<int:id>')
@admin_required
def excluir(id):
    """Excluir usuário"""
    from app import db, Usuario
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == session['user_id']:
        flash('Você não pode excluir seu próprio usuário!', 'danger')
        return redirect(url_for('users.usuarios'))
    
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir usuário!', 'danger')
    
    return redirect(url_for('users.usuarios'))


@users_bp.route('/redefinir-senha/<int:id>', methods=['GET', 'POST'])
@admin_required
def redefinir_senha(id):
    """Redefinir senha de usuário"""
    from app import db, Usuario
    
    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar = request.form.get('confirmar_senha')
        if not nova_senha or len(nova_senha) < 6:
            flash('A senha deve ter ao menos 6 caracteres.', 'danger')
            return render_template('redefinir_senha.html', usuario=usuario)
        if nova_senha != confirmar:
            flash('As senhas não coincidem.', 'danger')
            return render_template('redefinir_senha.html', usuario=usuario)

        usuario.senha = generate_password_hash(nova_senha)
        try:
            db.session.commit()
            flash(f'Senha do usuário {usuario.email} atualizada com sucesso.', 'success')
            return redirect(url_for('users.tabela'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao redefinir a senha.', 'danger')

    return render_template('redefinir_senha.html', usuario=usuario)
