# Funções auxiliares compartilhadas entre os módulos de rotas
# Evita duplicação de código em múltiplos arquivos
from functools import wraps
from flask import g, session, redirect, url_for, flash


def get_unit_db():
    """Obtém conexão com o banco da unidade atual"""
    from database_manager import db_manager
    
    if hasattr(g, 'unit_db') and g.unit_db:
        return g.unit_db

    if 'unit_id' in session:
        try:
            conn = db_manager.get_connection(session['unit_id'])
            return conn
        except Exception:
            return None
    return None


def login_required(f):
    """Decorator que exige que o usuário esteja autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para verificar se é admin ou tem permissão de cadastro"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        from app import db, Usuario
        try:
            usuario = db.session.get(Usuario, session['user_id'])
        except Exception:
            usuario = None

        if not usuario:
            flash('Acesso negado! Usuário inválido.', 'danger')
            return redirect(url_for('auth.login'))

        if usuario.tipo != 'admin' and not getattr(usuario, 'pode_cadastrar', 0):
            flash('Acesso negado! Apenas administradores ou usuários com permissão.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def check_permission():
    """Verifica permissão do usuário para cadastrar/editar"""
    from app import db, Usuario
    from flask import current_app
    
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        usuario = db.session.get(Usuario, user_id)
        if not usuario:
            return False
        
        tipo = usuario.tipo
        pode = getattr(usuario, 'pode_cadastrar', 0)
        
        if tipo != 'admin' and not pode:
            return False
            
        return True
    except Exception as e:
        current_app.logger.error(f'check_permission: exception={str(e)}')
        return False


def require_unit(f):
    """Decorator para verificar se a unidade está selecionada"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'unit_id' not in session:
            flash('Selecione uma unidade primeiro.', 'warning')
            return redirect(url_for('main.selecionar_unidade'))
        return f(*args, **kwargs)
    return decorated_function


def require_auth(f):
    """Decorator para verificar se o usuário está autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
