# Sistema Multi-Tenant de Estoque Hospitalar
# Versão organizada com Flask Blueprints
from flask import Flask, session, g
import os
import sqlite3
from dotenv import load_dotenv
from markupsafe import Markup, escape
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Carregar variáveis de ambiente
load_dotenv()

from database_manager import db_manager
from models import db, Usuario, Unidade
from extensions import csrf, limiter

# ========================
# CONFIGURAÇÃO DO APP
# ========================

# Caminho do banco de dados central - disponível no nível do módulo para imports
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'central.db')

app = Flask(__name__)

# ── Chave secreta ──────────────────────────────────────────────────────────────
_secret = os.getenv('SECRET_KEY', '')
if not _secret:
    raise RuntimeError(
        'SECRET_KEY não definida! Adicione-a ao arquivo .env.'
    )
app.config['SECRET_KEY'] = _secret

# ── Banco de dados central ─────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Aumentar timeout para 30 segundos (padrão é 5) para evitar "database is locked"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 30}
}

# ── Otimização SQLite (WAL Mode) ───────────────────────────────────────────────
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# ── Segurança dos cookies de sessão ────────────────────────────────────────────
app.config['SESSION_COOKIE_HTTPONLY'] = True          # JS não acessa o cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'         # Mitiga CSRF de terceiros
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))

# ── WTF / CSRF ─────────────────────────────────────────────────────────────────
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# Inicializar extensões
db.init_app(app)
csrf.init_app(app)
limiter.init_app(app)

# ── Template Filters ───────────────────────────────────────────────────────────
@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return Markup(escape(s).replace('\n', '<br>\n'))

# ========================
# BEFORE REQUEST HANDLER
# ========================

@app.before_request
def attach_unit_db():
    """Se houver unit_id na sessão, coloca a conexão em g.unit_db"""
    from flask import g

    unit_id = session.get('unit_id')
    if unit_id:
        try:
            g.unit_db = db_manager.get_connection(unit_id)
        except Exception as e:
            g.unit_db = None
            app.logger.exception('Erro ao obter conexão da unidade: %s', e)
    else:
        g.unit_db = None


# ========================
# NGROK WARNING SKIP
# ========================

@app.after_request
def add_ngrok_skip_header(response):
    """Adiciona header para ignorar aviso do ngrok"""
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response


# ========================
# REGISTER BLUEPRINTS
# ========================

# Importar blueprints dos respectivos módulos
from routes.auth import auth_bp
from routes.main import main_bp
from routes.users import users_bp
from routes.units import units_bp
from routes.products import products_bp
from routes.movements import movements_bp
from routes.suppliers import suppliers_bp
from routes.sectors import sectors_bp
from routes.settings import settings_bp
from routes.suggestions import suggestions_bp
from routes.system import system_bp
from routes.reports import reports_bp

# Registrar blueprints (url_prefix definido em cada blueprint)
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(users_bp)
app.register_blueprint(units_bp)
app.register_blueprint(products_bp)
app.register_blueprint(movements_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(sectors_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(suggestions_bp)
app.register_blueprint(system_bp)
app.register_blueprint(reports_bp)


# ========================
# URL_FOR BACKWARD COMPATIBILITY
# ========================

# Mapeamento de rotas antigas para novas (blueprint.endpoint)
ROUTE_MAPPING = {
    'login': 'auth.login',
    'logout': 'auth.logout',
    'cadastro': 'auth.cadastro',
    'index': 'main.index',
    'selecionar_unidade': 'main.selecionar_unidade',
    'trocar_unidade': 'main.trocar_unidade',
    'tabela': 'users.tabela',
    'editar': 'users.editar',
    'novo_usuario': 'users.novo_usuario',
    'usuarios': 'users.usuarios',
    'excluir': 'users.excluir',
    'redefinir_senha': 'users.redefinir_senha',
    'listar_unidades': 'units.listar_unidades',
    'novo_unidade': 'units.novo_unidade',
    'editar_unidade': 'units.editar_unidade',
    'excluir_unidade': 'units.excluir_unidade',
    'produtos': 'products.produtos',
    'novo_produto': 'products.novo_produto',
    'editar_produto': 'products.editar_produto',
    'excluir_produto': 'products.excluir_produto',
    'movimentacoes': 'movements.movimentacoes',
    'entrada_produto': 'movements.entrada_produto',
    'saida_produto': 'movements.saida_produto',
    'excluir_movimentacao': 'movements.excluir_movimentacao',
    'fornecedores': 'suppliers.fornecedores',
    'novo_fornecedor': 'suppliers.novo_fornecedor',
    'editar_fornecedor': 'suppliers.editar_fornecedor',
    'excluir_fornecedor': 'suppliers.excluir_fornecedor',
    'setores': 'sectors.setores',
    'novo_setor': 'sectors.novo_setor',
    'editar_setor': 'sectors.editar_setor',
    'excluir_setor': 'sectors.excluir_setor',
    'configuracoes': 'settings.configuracoes',
    'minhas_sugestoes': 'suggestions.minhas_sugestoes',
    'nova_sugestao': 'suggestions.nova_sugestao',
    'admin_sugestoes': 'suggestions.admin_sugestoes',
    'responder_sugestao': 'suggestions.responder_sugestao',
    'create_backup': 'system.create_backup',
    'read_notification': 'system.read_notification',
    'mark_all_notifications_as_read': 'system.mark_all_notifications_as_read',
    'perfil': 'users.perfil',
    'relatorio_geral': 'reports.relatorio_geral'
}

from flask import url_for as original_url_for

@app.context_processor
def override_url_for():
    """Override url_for to add blueprint prefix automatically"""
    from functools import wraps
    from database_config import get_all_units
    from models import Notificacao
    
    @wraps(original_url_for)
    def new_url_for(endpoint=None, **values):
        # Se o endpoint não tem ponto (ou seja, é uma rota antiga sem blueprint)
        if endpoint and '.' not in endpoint and endpoint in ROUTE_MAPPING:
            endpoint = ROUTE_MAPPING[endpoint]
        return original_url_for(endpoint, **values)
    
    # Inject notifications
    unread_count = 0
    notifications = []
    if 'user_id' in session:
        user_id = session['user_id']
        try:
            unread_count = Notificacao.query.filter_by(usuario_id=user_id, lida=False).count()
            notifications = Notificacao.query.filter_by(usuario_id=user_id).order_by(Notificacao.data_criacao.desc()).limit(5).all()
        except Exception:
            # A tabela pode não existir na primeira execução
            pass

    return dict(
        url_for=new_url_for, 
        get_all_units=get_all_units,
        unread_notifications=unread_count,
        notifications=notifications
    )


# ========================
# MAIN ENTRY POINT
# ========================

if __name__ == '__main__':

    # Inicializar banco central
    try:
        # A criação/atualização de tabelas deve ser feita por scripts de migração
        # Ex: flask db upgrade (com Flask-Migrate) ou python scripts/migrate.py
        with app.app_context():
            db.create_all()
            
            # Migração automática para adicionar coluna ultimo_login se não existir
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Tenta selecionar a coluna. Se falhar, ela não existe.
                cursor.execute("SELECT ultimo_login FROM usuarios LIMIT 1")
                conn.close()
            except sqlite3.OperationalError:
                # Coluna não existe, adicionar
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("ALTER TABLE usuarios ADD COLUMN ultimo_login DATETIME")
                conn.commit()
                conn.close()
                print("Coluna 'ultimo_login' adicionada com sucesso.")
    except Exception as e:
        print(f"Aviso: {e}")

    _debug = os.getenv('FLASK_DEBUG', 'False').strip().lower() in ('1', 'true')
    app.run(debug=_debug, host='0.0.0.0', port=5000)
