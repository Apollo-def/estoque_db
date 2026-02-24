# Sistema Multi-Tenant de Estoque Hospitalar
# Versão organizada com Flask Blueprints
from flask import Flask, session, g
import os
import sqlite3
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from database_manager import db_manager
from models import db, Usuario, Unidade

# ========================
# CONFIGURAÇÃO DO APP
# ========================

# Caminho do banco de dados central - disponível no nível do módulo para imports
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'central.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sistema_estoque_hospitalar_2024')

# Configuração do banco de dados central
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy com o app
db.init_app(app)


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
from routes.categories import categories_bp
from routes.sectors import sectors_bp
from routes.settings import settings_bp

# Registrar blueprints (url_prefix definido em cada blueprint)
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(users_bp)
app.register_blueprint(units_bp)
app.register_blueprint(products_bp)
app.register_blueprint(movements_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(sectors_bp)
app.register_blueprint(settings_bp)


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
    'categorias': 'categories.categorias',
    'nova_categoria': 'categories.nova_categoria',
    'editar_categoria': 'categories.editar_categoria',
    'excluir_categoria': 'categories.excluir_categoria',
    'setores': 'sectors.setores',
    'novo_setor': 'sectors.novo_setor',
    'editar_setor': 'sectors.editar_setor',
    'excluir_setor': 'sectors.excluir_setor',
    'configuracoes': 'settings.configuracoes'
}

from flask import url_for as original_url_for

@app.context_processor
def override_url_for():
    """Override url_for to add blueprint prefix automatically"""
    from functools import wraps
    
    @wraps(original_url_for)
    def new_url_for(endpoint=None, **values):
        # Se o endpoint não tem ponto (ou seja, é uma rota antiga sem blueprint)
        if endpoint and '.' not in endpoint and endpoint in ROUTE_MAPPING:
            endpoint = ROUTE_MAPPING[endpoint]
        return original_url_for(endpoint, **values)
    
    return dict(url_for=new_url_for)


# ========================
# MAIN ENTRY POINT
# ========================

if __name__ == '__main__':
    
    # Garantir que o banco central tenha as colunas necessárias
    def ensure_central_schema():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(usuarios)")
            cols = [r[1] for r in cur.fetchall()]

            if 'pode_cadastrar' not in cols:
                cur.execute("ALTER TABLE usuarios ADD COLUMN pode_cadastrar INTEGER DEFAULT 1")
                conn.commit()
                print('Coluna pode_cadastrar adicionada em usuarios (central.db)')
                
            if 'permissoes_menu' not in cols:
                cur.execute("ALTER TABLE usuarios ADD COLUMN permissoes_menu TEXT")
                conn.commit()
                print('Coluna permissoes_menu adicionada em usuarios (central.db)')

        except Exception as e:
            print(f"Aviso ao garantir schema central: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # Inicializar banco central
    try:
        ensure_central_schema()
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Aviso: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)
