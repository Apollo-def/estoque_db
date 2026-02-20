# Sistema Multi-Tenant de Estoque Hospitalar
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import ast
from datetime import datetime, timezone
import json
import os
import sqlite3
import time
import shutil
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from database_manager import db_manager
from database_config import get_all_units, get_database_config

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sistema_estoque_hospitalar_2024')

# Configuração do banco de dados central com caminho absoluto
import os
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'central.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Usuário (banco central)
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), default='user')  # 'admin' ou 'user'
    unidades_acesso = db.Column(db.Text)  # JSON com unidades permitidas
    pode_cadastrar = db.Column(db.Integer, default=1)  # Permissão para cadastrar
    permissoes_menu = db.Column(db.Text)  # JSON com permissões de menu
    ativo = db.Column(db.Integer, default=1)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_unidades_acesso(self):
        """Retorna lista de unidades que o usuário pode acessar"""
        if not self.unidades_acesso or not self.unidades_acesso.strip():
            return []
        # Primeiro, tentar JSON padrão
        try:
            return json.loads(self.unidades_acesso)
        except Exception:
            # Suporte a formatos legados (representação Python: "['a','b']")
            try:
                val = ast.literal_eval(self.unidades_acesso)
                if isinstance(val, list):
                    return val
            except Exception:
                # Tentativa final: substituir aspas simples por duplas e carregar como JSON
                try:
                    s = self.unidades_acesso.replace("'", '"')
                    return json.loads(s)
                except Exception:
                    return []
        return []
    
    def pode_acessar_unidade(self, unit_id):
        """Verifica se usuário pode acessar determinada unidade"""
        unidades = self.get_unidades_acesso()
        return unit_id in unidades or self.tipo == 'admin'
    
    def is_admin(self):
        return self.tipo == 'admin'
    
    def __repr__(self):
        return f'<Usuario {self.nome}>'

# Modelo de Unidade (banco central)
class Unidade(db.Model):
    __tablename__ = 'unidades'
    id = db.Column(db.String(50), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    # Campos para persistir arquivo/tipo do banco da unidade
    database = db.Column(db.String(200))
    type = db.Column(db.String(50))
    ativa = db.Column(db.Integer, default=1)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Unidade {self.nome}>'

# Modelos do banco da unidade (serão criados dinamicamente)
class Produto:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_all(self):
        cursor = self.db.execute('SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome')
        return cursor.fetchall()
    
    def get_by_id(self, id):
        cursor = self.db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (id,))
        return cursor.fetchone()
    
    def create(self, data):
        cursor = self.db.execute('''
            INSERT INTO produtos (nome, descricao, quantidade, categoria, usuario_id, codigo_barras, unidade_medida, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['nome'], data.get('descricao'), data['quantidade'], 
              data.get('categoria'), data['usuario_id'], data.get('codigo_barras'),
              data.get('unidade_medida', 'un'), data.get('estoque_minimo', 5)))
        self.db.commit()
        return cursor.lastrowid

class Movimentacao:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_all(self):
        cursor = self.db.execute('''
            SELECT m.*, p.nome as produto_nome 
            FROM movimentacoes m 
            JOIN produtos p ON m.produto_id = p.id 
            ORDER BY m.data_movimentacao DESC
        ''')
        return cursor.fetchall()
    
    def create(self, data):
        cursor = self.db.execute('''
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario_responsavel_id, origem, destino, nota_fiscal, ordem_servico, motivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['produto_id'], data['tipo'], data['quantidade'], 
              data['usuario_responsavel_id'], data.get('origem'), data.get('destino'),
              data.get('nota_fiscal'), data.get('ordem_servico'), data.get('motivo')))
        self.db.commit()
        return cursor.lastrowid

# Funções auxiliares para banco de dados dinâmico
def get_unit_db():
    """Obtém conexão com o banco da unidade atual"""
    # Primeiro tenta a conexão armazenada no contexto da request
    from flask import g
    if hasattr(g, 'unit_db') and g.unit_db:
        return g.unit_db

    if 'unit_id' in session:
        # fallback: obter via db_manager (irá usar cache se implementado)
        try:
            conn = db_manager.get_connection(session['unit_id'])
            return conn
        except Exception:
            return None
    return None

def init_unit_models():
    """Inicializa modelos da unidade atual"""
    unit_db = get_unit_db()
    if unit_db:
        globals()['produto_model'] = Produto(unit_db)
        globals()['movimentacao_model'] = Movimentacao(unit_db)


@app.before_request
def attach_unit_db():
    """Se houver unit_id na sessão, coloca a conexão em g.unit_db para uso nas views.

    Usa tenant_db.get_connection que pode retornar sqlite3.Connection (para sqlite)
    ou um SQLAlchemy Connection para outros DBs.
    """
    from flask import g
    from tenant_db import get_db_adapter as get_tenant_connection

    unit_id = session.get('unit_id')
    if unit_id:
        try:
            g.unit_db = get_tenant_connection(unit_id)
        except Exception as e:
            g.unit_db = None
            app.logger.exception('Erro ao obter conexão da unidade: %s', e)
    else:
        g.unit_db = None

# Rotas
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Se não há unidade selecionada, mostrar seleção
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    # Dashboard da unidade
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    # Estatísticas da unidade
    cursor = unit_db.execute('SELECT COUNT(*) FROM produtos WHERE ativo = 1')
    total_produtos = cursor.fetchone()[0]
    
    cursor = unit_db.execute('SELECT COUNT(*) FROM produtos WHERE ativo = 1 AND quantidade <= estoque_minimo')
    produtos_baixo_estoque = cursor.fetchone()[0]
    
    cursor = unit_db.execute('SELECT COUNT(*) FROM movimentacoes WHERE tipo = "entrada"')
    total_entradas = cursor.fetchone()[0]
    
    cursor = unit_db.execute('SELECT COUNT(*) FROM movimentacoes WHERE tipo = "saida"')
    total_saidas = cursor.fetchone()[0]
    
    # Movimentações recentes (apenas se houver dados)
    cursor = unit_db.execute('''
        SELECT m.*, p.nome as produto_nome
        FROM movimentacoes m
        JOIN produtos p ON m.produto_id = p.id
        WHERE p.ativo = 1
        ORDER BY m.data_movimentacao DESC
        LIMIT 5
    ''')
    movimentacoes_recentes = cursor.fetchall()
    
    # Informações da unidade
    unit_config = get_database_config(session['unit_id'])
    
    return render_template('index.html', 
                         total_produtos=total_produtos,
                         produtos_baixo_estoque=produtos_baixo_estoque,
                         total_entradas=total_entradas,
                         total_saidas=total_saidas,
                         movimentacoes_recentes=movimentacoes_recentes,
                         unidade_atual=unit_config)

@app.route('/selecionar-unidade', methods=['GET', 'POST'])
def selecionar_unidade():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        unit_id = request.form.get('unit_id')
        
        # Verificar se usuário pode acessar esta unidade
        usuario = db.session.get(Usuario, session['user_id'])
        
        if not usuario.pode_acessar_unidade(unit_id):
            flash('Você não tem permissão para acessar esta unidade', 'danger')
            return redirect(url_for('selecionar_unidade'))
        
        # Verificar se unidade existe e está ativa
        unit_config = get_database_config(unit_id)
        if not unit_config:
            flash('Unidade não encontrada', 'danger')
            return redirect(url_for('selecionar_unidade'))
        
        # Conectar ao banco da unidade
        try:
            unit_db = db_manager.get_connection(unit_id)
            session['unit_id'] = unit_id
            session['unit_name'] = unit_config['name']
            flash(f'Bem-vindo à {unit_config["name"]}!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Erro ao conectar com a unidade', 'danger')
            return redirect(url_for('selecionar_unidade'))
    
    # GET - mostrar lista de unidades disponíveis
    usuario = db.session.get(Usuario, session['user_id'])
    
    if usuario.is_admin():
        # Admin pode ver todas as unidades
        unidades = get_all_units()
    else:
        # Usuário comum vê apenas unidades permitidas
        unidades_permitidas = usuario.get_unidades_acesso()
        todas_unidades = get_all_units()
        unidades = {k: v for k, v in todas_unidades.items() if k in unidades_permitidas}
    
    return render_template('selecionar_unidade.html', unidades=unidades)

@app.route('/trocar-unidade')
def trocar_unidade():
    """Remove unidade da sessão e redireciona para seleção"""
    if 'unit_id' in session:
        del session['unit_id']
    if 'unit_name' in session:
        del session['unit_name']
    return redirect(url_for('selecionar_unidade'))

# Decorator para verificar se é admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Permitir acesso se for admin OU se o usuário tiver permissão de cadastro
        try:
            usuario = db.session.get(Usuario, session['user_id'])
        except Exception:
            usuario = None

        if not usuario:
            flash('Acesso negado! Usuário inválido.', 'danger')
            return redirect(url_for('login'))

        # usuario.tipo == 'admin' tem acesso total;
        # usuários com pode_cadastrar==1 também podem realizar ações de cadastro/edição
        if usuario.tipo != 'admin' and not getattr(usuario, 'pode_cadastrar', 0):
            flash('Acesso negado! Apenas administradores ou usuários com permissão de cadastro.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.ativo and check_password_hash(usuario.senha, senha):
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            session['user_email'] = usuario.email
            session['user_tipo'] = usuario.tipo
            
            # Carregar permissões de menu do usuário
            if usuario.permissoes_menu:
                try:
                    session['permissoes_menu'] = json.loads(usuario.permissoes_menu)
                except:
                    # Se houver erro ao carregar, definir permissões padrão
                    if usuario.tipo == 'admin':
                        session['permissoes_menu'] = {
                            'dashboard': True,
                            'produtos': True,
                            'movimentacoes': True,
                            'usuarios': True,
                            'unidades': True,
                            'fornecedores': True,
                            'categorias': True,
                            'setores': True,
                            'configuracoes': True,
                            'relatorios': True,
                            'backup': True,
                            'logs': True
                        }
                    else:
                        session['permissoes_menu'] = {}
            else:
                # Se não houver permissões definidas
                if usuario.tipo == 'admin':
                    # Admin tem acesso a tudo por padrão
                    session['permissoes_menu'] = {
                        'dashboard': True,
                        'produtos': True,
                        'movimentacoes': True,
                        'usuarios': True,
                        'unidades': True,
                        'fornecedores': True,
                        'categorias': True,
                        'setores': True,
                        'configuracoes': True,
                        'relatorios': True,
                        'backup': True,
                        'logs': True
                    }
                else:
                    # Usuário comum não tem acesso a nada por padrão
                    session['permissoes_menu'] = {}
            
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(url_for('selecionar_unidade'))
        else:
            flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        # Validações
        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return render_template('cadastro.html')

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email já está cadastrado!', 'danger')
            return render_template('cadastro.html')

        # Criar novo usuário
        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash)

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça seu login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Erro ao cadastrar usuário: %s', e)
            flash('Erro ao cadastrar usuário!', 'danger')

    # Passar get_all_units para o template se for admin
    unidades = get_all_units() if session.get('user_tipo') == 'admin' else {}
    return render_template('cadastro.html', get_all_units=lambda: unidades)


@app.route('/unidades/novo', methods=['GET', 'POST'])
@admin_required
def novo_unidade():
    from database_config import DATABASES

    if request.method == 'POST':
        unit_id = request.form.get('unit_id', '').strip()
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        arquivo_db = request.form.get('arquivo_db', '').strip()

        # Validações básicas
        if not unit_id or not nome or not arquivo_db:
            flash('Preencha id, nome e arquivo do banco (database).', 'danger')
            return render_template('novo_unidade.html')

        # unit_id deve ser alfanumérico com underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+$', unit_id):
            flash('Id da unidade inválido. Use letras, números, traço ou underscore.', 'danger')
            return render_template('novo_unidade.html')

        # Verificar se já existe no DATABASES
        if unit_id in DATABASES:
            flash('Já existe uma unidade com este id.', 'danger')
            return render_template('novo_unidade.html')

        # Verificar tabela central e garantir colunas
        try:
            conn = db_manager.get_connection(None)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(unidades)")
            cols = [r['name'] for r in cur.fetchall()]
            if 'database' not in cols:
                cur.execute("ALTER TABLE unidades ADD COLUMN database TEXT")
            if 'type' not in cols:
                cur.execute("ALTER TABLE unidades ADD COLUMN type TEXT")
            conn.commit()
        except Exception:
            # não fatal, prossegue
            app.logger.exception('Erro ao verificar/alterar tabela unidades no central DB')

        # Verificar se já existe na tabela central
        if db.session.get(Unidade, unit_id):
            flash('Já existe uma unidade com este id na base central.', 'danger')
            return render_template('novo_unidade.html')

        # Inserir na tabela central
        try:
            nova = Unidade(id=unit_id, nome=nome, descricao=descricao, database=arquivo_db, type='sqlite')
            db.session.add(nova)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Erro ao criar unidade no central DB: %s', e)
            flash('Erro ao salvar unidade no banco central.', 'danger')
            return render_template('novo_unidade.html')

        # Atualizar DATABASES em memória (apenas para sqlite local)
        DATABASES[unit_id] = {
            'name': nome,
            'database': arquivo_db,
            'host': 'localhost',
            'type': 'sqlite',
            'description': descricao
        }

        # Inicializar banco da unidade
        try:
            db_manager.init_database(unit_id)
            flash('Unidade criada com sucesso e banco inicializado.', 'success')
            return redirect(url_for('tabela'))
        except Exception as e:
            app.logger.exception('Erro ao inicializar DB da unidade: %s', e)
            flash('Unidade criada no central, mas falha ao inicializar o banco da unidade. Verifique logs.', 'warning')
            return redirect(url_for('tabela'))

    return render_template('novo_unidade.html')


@app.route('/unidades/editar/<unit_id>', methods=['GET', 'POST'])
@admin_required
def editar_unidade(unit_id):
    unidade = Unidade.query.get_or_404(unit_id)
    from database_config import DATABASES

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        arquivo_db = request.form.get('arquivo_db', '').strip()
        ativa = 1 if request.form.get('ativa') == 'on' else 0

        if not nome or not arquivo_db:
            flash('Nome e arquivo do banco são obrigatórios.', 'danger')
            return render_template('editar_unidade.html', unidade=unidade)

        # Se o nome do arquivo mudou, tentar renomear o arquivo físico em instance/
        old_file = unidade.database or ''
        new_file = arquivo_db
        try:
            if old_file and old_file != new_file:
                old_path = os.path.join(os.path.dirname(db_path), old_file)
                new_path = os.path.join(os.path.dirname(db_path), new_file)
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    os.rename(old_path, new_path)
        except Exception as e:
            app.logger.exception('Não foi possível renomear arquivo DB da unidade: %s', e)
            flash('Unidade atualizada, mas falha ao renomear arquivo do DB (ver logs).', 'warning')

        # Atualizar registro central
        unidade.nome = nome
        unidade.descricao = descricao
        unidade.database = arquivo_db
        unidade.ativa = ativa
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Erro ao atualizar unidade: %s', e)
            flash('Erro ao salvar alterações.', 'danger')
            return render_template('editar_unidade.html', unidade=unidade)

        # Atualizar cache em memória
        DATABASES[unit_id] = {
            'name': unidade.nome,
            'database': unidade.database,
            'host': 'localhost',
            'type': unidade.type or 'sqlite',
            'description': unidade.descricao
        }

        flash('Unidade atualizada com sucesso.', 'success')
        return redirect(url_for('tabela'))

    return render_template('editar_unidade.html', unidade=unidade)


@app.route('/unidades/excluir/<unit_id>', methods=['GET', 'POST'])
@admin_required
def excluir_unidade(unit_id):
    unidade = Unidade.query.get_or_404(unit_id)

    if request.method == 'POST':
        # Fazer backup do arquivo da unidade e remover o registro central
        arquivo = unidade.database or ''
        instance_dir = os.path.dirname(db_path)
        try:
            if arquivo:
                src = os.path.join(instance_dir, arquivo)
                if os.path.exists(src):
                    backups_dir = os.path.join(instance_dir, 'backups')
                    os.makedirs(backups_dir, exist_ok=True)
                    ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                    dst = os.path.join(backups_dir, f"{unit_id}_{ts}.db")
                    shutil.copy2(src, dst)

                    # Opcional: remover arquivo físico (somente se checkbox 'remover_arquivo' recebido)
                    if request.form.get('remover_arquivo') == 'on':
                        try:
                            os.remove(src)
                        except Exception:
                            app.logger.exception('Falha ao remover arquivo da unidade')

            # Remover registro da tabela central
            db.session.delete(unidade)

            # Atualizar usuarios: remover unit_id das listas de unidades_acesso
            usuarios = Usuario.query.all()
            for u in usuarios:
                try:
                    unidades = u.get_unidades_acesso()
                    if unit_id in unidades:
                        unidades.remove(unit_id)
                        u.unidades_acesso = json.dumps(unidades) if unidades else None
                except Exception:
                    # ignorar falhas para um usuário específico
                    app.logger.exception('Erro ao atualizar unidades_acesso para usuario %s', u.email)

            db.session.commit()
            # Remover do cache em memória se presente
            try:
                from database_config import DATABASES
                if unit_id in DATABASES:
                    del DATABASES[unit_id]
            except Exception:
                pass

            flash('Unidade excluída (registro removido). Backup criado em instance/backups/.', 'success')
            return redirect(url_for('tabela'))

        except Exception as e:
            db.session.rollback()
            app.logger.exception('Erro ao excluir unidade: %s', e)
            flash('Erro ao excluir unidade. Verifique logs.', 'danger')
            return redirect(url_for('tabela'))

    # GET -> confirmar exclusão
    return render_template('confirmar_excluir_unidade.html', unidade=unidade)


@app.route('/unidades')
def listar_unidades():
    # Verificar se usuário está logado
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Admin sempre tem acesso
    if session.get('user_tipo') == 'admin':
        unidades = Unidade.query.order_by(Unidade.id).all()
        return render_template('listar_unidades.html', unidades=unidades)
    
    # Verificar permissão específica para unidades
    user_permissoes = session.get('permissoes_menu', {})
    
    if not user_permissoes.get('unidades', False):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    unidades = Unidade.query.order_by(Unidade.id).all()
    return render_template('listar_unidades.html', unidades=unidades)

@app.route('/tabela')
@admin_required
def tabela():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuarios = Usuario.query.all()
    return render_template('tabela.html', usuarios=usuarios)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Definir menus disponíveis para permissão como uma constante global da função
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

    # Inicializar variáveis
    usuario = Usuario.query.get_or_404(id)
    unidades = None
    permissoes_atual = json.loads(usuario.permissoes_menu) if usuario.permissoes_menu else {}

    # Se não for admin e estiver editando outro usuário, negar
    if session.get('user_tipo') != 'admin' and session.get('user_id') != usuario.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        nova_senha = request.form.get('nova_senha')

        # Verificar se email já existe (exceto para o usuário atual)
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

        # Atualizar senha se fornecida
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)

        # Se admin, permitir atualizar tipo, unidades e permissões
        if session.get('user_tipo') == 'admin':
            usuario.tipo = request.form.get('tipo', usuario.tipo)
            
            # Atualizar unidades de acesso
            unidades = request.form.getlist('unidades')
            usuario.unidades_acesso = json.dumps(unidades) if unidades else None
            
            # Atualizar permissão para cadastrar
            usuario.pode_cadastrar = 1 if request.form.get('pode_cadastrar') == 'on' else 0
            
            # Atualizar permissões de menu
            permissoes_menu = request.form.getlist('permissoes_menu')
            
            # Criar dicionário com todas as permissões como False
            todas_permissoes = {}
            for menu in MENUS_DISPONIVEIS:
                todas_permissoes[menu['id']] = False
            
            # Atualizar para True as permissões selecionadas
            for permissao in permissoes_menu:
                if permissao in todas_permissoes:
                    todas_permissoes[permissao] = True
            
            # Se for admin, garantir acesso total
            if usuario.tipo == 'admin':
                for menu in MENUS_DISPONIVEIS:
                    todas_permissoes[menu['id']] = True
            
            # Salvar permissões no usuário
            usuario.permissoes_menu = json.dumps(todas_permissoes)
            permissoes_atual = todas_permissoes
            
            # Atualizar a sessão se o usuário estiver editando a si mesmo
            if session.get('user_id') == usuario.id:
                session['permissoes_menu'] = todas_permissoes

        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('tabela'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Erro ao atualizar usuário: %s', e)
            flash('Erro ao atualizar usuário!', 'danger')

    # Se admin, carregar lista de unidades para seleção
    if session.get('user_tipo') == 'admin':
        unidades = get_all_units()

    # Garantir colunas necessárias na tabela usuarios (compatibilidade com DBs legados)
    try:
        conn = db_manager.get_connection(None)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(usuarios)")
        cols = [r['name'] for r in cur.fetchall()]
        
        # Adicionar coluna 'pode_cadastrar' se não existir
        if 'pode_cadastrar' not in cols:
            cur.execute("ALTER TABLE usuarios ADD COLUMN pode_cadastrar INTEGER DEFAULT 1")
        
        # Adicionar coluna 'permissoes_menu' se não existir
        if 'permissoes_menu' not in cols:
            cur.execute("ALTER TABLE usuarios ADD COLUMN permissoes_menu TEXT")
        
        conn.commit()
    except Exception as e:
        app.logger.exception(f'Falha ao garantir colunas na tabela usuarios: {str(e)}')
    
    return render_template('editar.html', 
                         usuario=usuario, 
                         unidades=unidades,
                         menus_disponiveis=MENUS_DISPONIVEIS,
                         permissoes_atual=permissoes_atual)

@app.route('/novo_usuario', methods=['GET', 'POST'])
@admin_required
def novo_usuario():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form.get('tipo', 'user')
        unidades = request.form.getlist('unidades')
        pode_cadastrar = request.form.get('pode_cadastrar', '1')
        
        # Validações básicas
        if not nome or not email:
            flash('Preencha todos os campos obrigatórios!', 'danger')
            unidades = get_all_units()
            return render_template('novo_usuario.html', unidades=unidades)
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'danger')
            unidades = get_all_units()
            return render_template('novo_usuario.html', unidades=unidades)
        
        # Hash da senha
        senha_hash = generate_password_hash(senha)
        
        # Converter unidades para JSON
        unidades_acesso = None
        if unidades:
            unidades_acesso = json.dumps(unidades)
        
        # Definir permissões de menu
        permissoes_menu = {}
        if tipo == 'admin':
            # Se for admin, tem acesso a tudo
            permissoes_menu = {
                'dashboard': True,
                'produtos': True,
                'movimentacoes': True,
                'categorias': True,
                'setores': True,
                'fornecedores': True,
                'usuarios': True,
                'unidades': True,
                'configuracoes': True,
                'relatorios': True,
                'backup': True,
                'logs': True
            }
        else:
            # Se não for admin, não tem acesso a nada por padrão
            permissoes_menu = {
                'dashboard': False,
                'produtos': False,
                'movimentacoes': False,
                'categorias': False,
                'setores': False,
                'fornecedores': False,
                'usuarios': False,
                'unidades': False,
                'configuracoes': False,
                'relatorios': False,
                'backup': False,
                'logs': False
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
            return redirect(url_for('usuarios'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar usuário!', 'danger')
    
    unidades = get_all_units()
    return render_template('novo_usuario.html', unidades=unidades)

@app.route('/usuarios')
@admin_required
def usuarios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuarios_lista = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios_lista)

@app.route('/excluir/<int:id>')
@admin_required
def excluir(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Não permitir que o usuário exclua a si mesmo
    if usuario.id == session['user_id']:
        flash('Você não pode excluir seu próprio usuário!', 'danger')
        return redirect(url_for('usuarios'))
    
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir usuário!', 'danger')
    
    return redirect(url_for('usuarios'))

@app.route('/redefinir-senha/<int:id>', methods=['GET', 'POST'])
@admin_required
def redefinir_senha(id):
    # Apenas admin pode redefinir senha de outros usuários
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
            return redirect(url_for('tabela'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Erro ao redefinir senha: %s', e)
            flash('Erro ao redefinir a senha.', 'danger')

    return render_template('redefinir_senha.html', usuario=usuario)

# Rotas de Fornecedores
@app.route('/fornecedores')
@admin_required
def fornecedores():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM fornecedores WHERE ativo = 1 ORDER BY nome')
    fornecedores = cursor.fetchall()
    
    return render_template('fornecedores.html', fornecedores=fornecedores)

@app.route('/fornecedores/novo', methods=['GET', 'POST'])
@admin_required
def novo_fornecedor():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form.get('cnpj', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        endereco = request.form.get('endereco', '')
        
        if not nome:
            flash('O nome do fornecedor é obrigatório!', 'danger')
            return render_template('novo_fornecedor.html')
        
        try:
            cursor = unit_db.execute('''
                INSERT INTO fornecedores (nome, cnpj, telefone, email, endereco)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, cnpj, telefone, email, endereco))
            unit_db.commit()
            flash('Fornecedor cadastrado com sucesso!', 'success')
            return redirect(url_for('fornecedores'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao cadastrar fornecedor!', 'danger')
    
    return render_template('novo_fornecedor.html')

@app.route('/fornecedores/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_fornecedor(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM fornecedores WHERE id = ? AND ativo = 1', (id,))
    fornecedor = cursor.fetchone()
    
    if not fornecedor:
        flash('Fornecedor não encontrado!', 'danger')
        return redirect(url_for('fornecedores'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form.get('cnpj', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        endereco = request.form.get('endereco', '')
        
        if not nome:
            flash('O nome do fornecedor é obrigatório!', 'danger')
            return render_template('editar_fornecedor.html', fornecedor=fornecedor)
        
        try:
            cursor = unit_db.execute('''
                UPDATE fornecedores 
                SET nome = ?, cnpj = ?, telefone = ?, email = ?, endereco = ?
                WHERE id = ?
            ''', (nome, cnpj, telefone, email, endereco, id))
            unit_db.commit()
            flash('Fornecedor atualizado com sucesso!', 'success')
            return redirect(url_for('fornecedores'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao atualizar fornecedor!', 'danger')
    
    return render_template('editar_fornecedor.html', fornecedor=fornecedor)

@app.route('/fornecedores/excluir/<int:id>')
@admin_required
def excluir_fornecedor(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM fornecedores WHERE id = ? AND ativo = 1', (id,))
    fornecedor = cursor.fetchone()
    
    if not fornecedor:
        flash('Fornecedor não encontrado!', 'danger')
        return redirect(url_for('fornecedores'))
    
    try:
        cursor = unit_db.execute('UPDATE fornecedores SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Fornecedor excluído com sucesso!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir fornecedor!', 'danger')
    
    return redirect(url_for('fornecedores'))

# Rotas de Categorias
@app.route('/categorias')
@admin_required
def categorias():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
    categorias = cursor.fetchall()
    
    return render_template('categorias.html', categorias=categorias)

@app.route('/categorias/nova', methods=['GET', 'POST'])
@admin_required
def nova_categoria():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        
        if not nome:
            flash('O nome da categoria é obrigatório!', 'danger')
            return render_template('nova_categoria.html')
        
        try:
            cursor = unit_db.execute('''
                INSERT INTO categorias (nome, descricao)
                VALUES (?, ?)
            ''', (nome, descricao))
            unit_db.commit()
            flash('Categoria cadastrada com sucesso!', 'success')
            return redirect(url_for('categorias'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao cadastrar categoria!', 'danger')
    
    return render_template('nova_categoria.html')

@app.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_categoria(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM categorias WHERE id = ? AND ativo = 1', (id,))
    categoria = cursor.fetchone()
    
    if not categoria:
        flash('Categoria não encontrada!', 'danger')
        return redirect(url_for('categorias'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        
        if not nome:
            flash('O nome da categoria é obrigatório!', 'danger')
            return render_template('editar_categoria.html', categoria=categoria)
        
        try:
            cursor = unit_db.execute('''
                UPDATE categorias 
                SET nome = ?, descricao = ?
                WHERE id = ?
            ''', (nome, descricao, id))
            unit_db.commit()
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('categorias'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao atualizar categoria!', 'danger')
    
    return render_template('editar_categoria.html', categoria=categoria)

@app.route('/categorias/excluir/<int:id>')
@admin_required
def excluir_categoria(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM categorias WHERE id = ? AND ativo = 1', (id,))
    categoria = cursor.fetchone()
    
    if not categoria:
        flash('Categoria não encontrada!', 'danger')
        return redirect(url_for('categorias'))
    
    try:
        cursor = unit_db.execute('UPDATE categorias SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Categoria excluída com sucesso!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir categoria!', 'danger')
    
    return redirect(url_for('categorias'))

# Rotas de Setores
@app.route('/setores')
@admin_required
def setores():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM setores WHERE ativo = 1 ORDER BY nome')
    setores = cursor.fetchall()
    
    return render_template('setores.html', setores=setores)

@app.route('/setores/novo', methods=['GET', 'POST'])
@admin_required
def novo_setor():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        responsavel = request.form.get('responsavel', '')
        
        if not nome:
            flash('O nome do setor é obrigatório!', 'danger')
            return render_template('novo_setor.html')
        
        try:
            cursor = unit_db.execute('''
                INSERT INTO setores (nome, descricao, responsavel)
                VALUES (?, ?, ?)
            ''', (nome, descricao, responsavel))
            unit_db.commit()
            flash('Setor cadastrado com sucesso!', 'success')
            return redirect(url_for('setores'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao cadastrar setor!', 'danger')
    
    return render_template('novo_setor.html')

@app.route('/setores/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_setor(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM setores WHERE id = ? AND ativo = 1', (id,))
    setor = cursor.fetchone()
    
    if not setor:
        flash('Setor não encontrado!', 'danger')
        return redirect(url_for('setores'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        responsavel = request.form.get('responsavel', '')
        
        if not nome:
            flash('O nome do setor é obrigatório!', 'danger')
            return render_template('editar_setor.html', setor=setor)
        
        try:
            cursor = unit_db.execute('''
                UPDATE setores 
                SET nome = ?, descricao = ?, responsavel = ?
                WHERE id = ?
            ''', (nome, descricao, responsavel, id))
            unit_db.commit()
            flash('Setor atualizado com sucesso!', 'success')
            return redirect(url_for('setores'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao atualizar setor!', 'danger')
    
    return render_template('editar_setor.html', setor=setor)

@app.route('/setores/excluir/<int:id>')
@admin_required
def excluir_setor(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    cursor = unit_db.execute('SELECT * FROM setores WHERE id = ? AND ativo = 1', (id,))
    setor = cursor.fetchone()
    
    if not setor:
        flash('Setor não encontrado!', 'danger')
        return redirect(url_for('setores'))
    
    try:
        cursor = unit_db.execute('UPDATE setores SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Setor excluído com sucesso!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir setor!', 'danger')
    
    return redirect(url_for('setores'))

@app.route('/configuracoes', methods=['GET', 'POST'])
@admin_required
def configuracoes():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        # Salvar configurações do formulário
        for key, value in request.form.items():
            if key.startswith('config_'):
                config_key = key.replace('config_', '')
                # Aqui você poderia salvar no banco ou em arquivo
                print(f"Configuração {config_key}: {value}")
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('configuracoes'))
    
    # Configurações padrão do sistema
    configuracoes = [
        {'chave': 'nome_sistema', 'valor': 'Sistema de Estoque Hospitalar', 'descricao': 'Nome do sistema'},
        {'chave': 'versao', 'valor': '1.0.0', 'descricao': 'Versão atual do sistema'},
        {'chave': 'limite_produtos_pagina', 'valor': '50', 'descricao': 'Limite de produtos por página na listagem'},
        {'chave': 'alerta_estoque_baixo', 'valor': '5', 'descricao': 'Nível mínimo para alerta de estoque baixo'},
        {'chave': 'tempo_sessao', 'valor': '3600', 'descricao': 'Tempo de sessão em segundos (1 hora)'},
        {'chave': 'email_remetente', 'valor': 'noreply@sistema.com', 'descricao': 'Email para notificações do sistema'},
    ]
    
    return render_template('configuracoes.html', configuracoes=configuracoes)

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema!', 'info')
    return redirect(url_for('login'))

# Rotas de Produtos
@app.route('/produtos')
def produtos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    # Filtros
    categoria = request.args.get('categoria', '')
    estoque_status = request.args.get('estoque', '')
    
    # Query base
    query = 'SELECT * FROM produtos WHERE ativo = 1'
    params = []
    
    if categoria:
        query += ' AND categoria = ?'
        params.append(categoria)
    
    if estoque_status == 'baixo':
        query += ' AND quantidade <= estoque_minimo'
    elif estoque_status == 'zerado':
        query += ' AND quantidade = 0'
    
    query += ' ORDER BY nome'
    
    cursor = unit_db.execute(query, params)
    produtos = cursor.fetchall()
    
    # Adicionar informações dos usuários aos produtos
    produtos_com_info = []
    for produto in produtos:
        produto_dict = dict(produto)  # Converter Row para dicionário
        if produto_dict.get('usuario_id'):
            try:
                # Buscar nome do usuário no banco central
                usuario = db.session.get(Usuario, produto_dict['usuario_id'])
                if usuario:
                    produto_dict['usuario_nome'] = usuario.nome
                else:
                    produto_dict['usuario_nome'] = 'Usuário não encontrado'
            except Exception:
                produto_dict['usuario_nome'] = 'Erro ao carregar'
        else:
            produto_dict['usuario_nome'] = None
        produtos_com_info.append(produto_dict)
    
    # Obter categorias únicas
    cursor = unit_db.execute('SELECT DISTINCT categoria FROM produtos WHERE ativo = 1 AND categoria IS NOT NULL ORDER BY categoria')
    categorias = [row[0] for row in cursor.fetchall()]
    
    return render_template('produtos.html', produtos=produtos_com_info, categorias=categorias)

@app.route('/produtos/novo', methods=['GET', 'POST'])
def novo_produto():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    # Verificar permissão de cadastro
    try:
        usuario = db.session.get(Usuario, session['user_id'])
        if not usuario or (usuario.tipo != 'admin' and not usuario.pode_cadastrar):
            flash('Acesso negado! Você não tem permissão para cadastrar produtos.', 'danger')
            return redirect(url_for('produtos'))
    except Exception:
        flash('Erro ao verificar permissões!', 'danger')
        return redirect(url_for('produtos'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        quantidade = int(request.form['quantidade'])
        categoria = request.form.get('categoria', '')
        codigo_barras = request.form.get('codigo_barras', '')
        unidade_medida = request.form.get('unidade_medida', 'un')
        estoque_minimo = int(request.form.get('estoque_minimo', 5))
        
        try:
            cursor = unit_db.execute('''
                INSERT INTO produtos (nome, descricao, quantidade, categoria, usuario_id, codigo_barras, unidade_medida, estoque_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, descricao, quantidade, categoria, session['user_id'], codigo_barras, unidade_medida, estoque_minimo))
            unit_db.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('produtos'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao cadastrar produto!', 'danger')
    
    return render_template('novo_produto.html')

@app.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    # Verificar permissão de edição
    try:
        usuario = db.session.get(Usuario, session['user_id'])
        if not usuario or (usuario.tipo != 'admin' and not usuario.pode_cadastrar):
            flash('Acesso negado! Você não tem permissão para editar produtos.', 'danger')
            return redirect(url_for('produtos'))
    except Exception:
        flash('Erro ao verificar permissões!', 'danger')
        return redirect(url_for('produtos'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    # Buscar produto
    cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (id,))
    produto = cursor.fetchone()
    
    if not produto:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('produtos'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        quantidade = int(request.form['quantidade'])
        categoria = request.form.get('categoria', '')
        codigo_barras = request.form.get('codigo_barras', '')
        unidade_medida = request.form.get('unidade_medida', 'un')
        estoque_minimo = int(request.form.get('estoque_minimo', 5))
        
        try:
            cursor = unit_db.execute('''
                UPDATE produtos 
                SET nome = ?, descricao = ?, quantidade = ?, categoria = ?, 
                    codigo_barras = ?, unidade_medida = ?, estoque_minimo = ?,
                    data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (nome, descricao, quantidade, categoria, codigo_barras, unidade_medida, estoque_minimo, id))
            unit_db.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao atualizar produto!', 'danger')
    
    # Converter Row para dicionário e formatar datas
    produto_dict = dict(produto)
    
    # Adicionar informações do usuário se existir usuario_id
    if 'usuario_id' in produto_dict and produto_dict['usuario_id']:
        try:
            # Buscar nome do usuário no banco central
            usuario = db.session.get(Usuario, produto_dict['usuario_id'])
            if usuario:
                produto_dict['usuario'] = {'nome': usuario.nome}
            else:
                produto_dict['usuario'] = {'nome': 'Usuário não encontrado'}
        except Exception as e:
            print(f"Erro ao buscar usuário: {e}")
            produto_dict['usuario'] = {'nome': 'Erro ao carregar'}
    else:
        produto_dict['usuario'] = {'nome': 'Não informado'}
    
    # Converter strings de data para objetos datetime
    from datetime import datetime, timezone
    if 'data_criacao' in produto_dict and produto_dict['data_criacao']:
        if isinstance(produto_dict['data_criacao'], str):
            try:
                # Tentar diferentes formatos de data
                data_str = produto_dict['data_criacao']
                if 'T' in data_str:
                    produto_dict['data_criacao'] = datetime.fromisoformat(data_str.replace('T', ' ').replace('Z', ''))
                else:
                    produto_dict['data_criacao'] = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Erro ao converter data_criacao: {e}")
                produto_dict['data_criacao'] = datetime.now()
    
    if 'data_atualizacao' in produto_dict and produto_dict['data_atualizacao']:
        if isinstance(produto_dict['data_atualizacao'], str):
            try:
                # Tentar diferentes formatos de data
                data_str = produto_dict['data_atualizacao']
                if 'T' in data_str:
                    produto_dict['data_atualizacao'] = datetime.fromisoformat(data_str.replace('T', ' ').replace('Z', ''))
                else:
                    produto_dict['data_atualizacao'] = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Erro ao converter data_atualizacao: {e}")
                produto_dict['data_atualizacao'] = datetime.now()
    
    return render_template('editar_produto.html', produto=produto_dict)

@app.route('/produtos/excluir/<int:id>')
@admin_required
def excluir_produto(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    try:
        cursor = unit_db.execute('UPDATE produtos SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir produto!', 'danger')
    
    return redirect(url_for('produtos'))

# Rotas de Movimentação
@app.route('/movimentacoes')
def movimentacoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    # Filtros
    tipo = request.args.get('tipo', '')
    produto_id = request.args.get('produto_id', '')
    
    cursor = unit_db.execute('''
        SELECT m.*, p.nome as produto_nome, p.categoria
        FROM movimentacoes m
        LEFT JOIN produtos p ON m.produto_id = p.id
        WHERE 1=1
    ''')
    params = []
    
    if tipo:
        cursor = unit_db.execute('''
            SELECT m.*, p.nome as produto_nome, p.categoria
            FROM movimentacoes m
            LEFT JOIN produtos p ON m.produto_id = p.id
            WHERE m.tipo = ?
        ''', (tipo,))
        movimentacoes = cursor.fetchall()
    elif produto_id:
        cursor = unit_db.execute('''
            SELECT m.*, p.nome as produto_nome, p.categoria
            FROM movimentacoes m
            LEFT JOIN produtos p ON m.produto_id = p.id
            WHERE m.produto_id = ?
        ''', (produto_id,))
        movimentacoes = cursor.fetchall()
    else:
        cursor = unit_db.execute('''
            SELECT m.*, p.nome as produto_nome, p.categoria
            FROM movimentacoes m
            LEFT JOIN produtos p ON m.produto_id = p.id
            ORDER BY m.data_movimentacao DESC
        ''')
        movimentacoes = cursor.fetchall()
    
    # Adicionar informações do usuário responsável
    movimentacoes_com_info = []
    for mov in movimentacoes:
        mov_dict = dict(mov)  # Converter Row para dicionário
        
        # Buscar nome do usuário responsável
        if mov_dict.get('usuario_responsavel_id'):
            try:
                usuario = db.session.get(Usuario, mov_dict['usuario_responsavel_id'])
                if usuario:
                    mov_dict['usuario_responsavel'] = {'nome': usuario.nome}
                else:
                    mov_dict['usuario_responsavel'] = {'nome': 'Usuário não encontrado'}
            except Exception:
                mov_dict['usuario_responsavel'] = {'nome': 'Erro ao carregar'}
        else:
            mov_dict['usuario_responsavel'] = {'nome': 'Não informado'}
        
        movimentacoes_com_info.append(mov_dict)
    
    # Obter produtos para filtro e estatísticas
    cursor = unit_db.execute('SELECT id, nome, quantidade FROM produtos WHERE ativo = 1 ORDER BY nome')
    produtos = cursor.fetchall()
    
    # Calcular saldo geral
    cursor = unit_db.execute('SELECT SUM(quantidade) as total FROM produtos WHERE ativo = 1')
    saldo_geral = cursor.fetchone()[0] or 0
    
    return render_template('movimentacoes.html', 
                         movimentacoes=movimentacoes, 
                         produtos=produtos,
                         saldo_geral=saldo_geral)

@app.route('/movimentacoes/entrada', methods=['GET', 'POST'])
def entrada_produto():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    # Verificar permissão de movimentação
    try:
        usuario = db.session.get(Usuario, session['user_id'])
        if not usuario or (usuario.tipo != 'admin' and not usuario.pode_cadastrar):
            flash('Acesso negado! Você não tem permissão para movimentar produtos.', 'danger')
            return redirect(url_for('movimentacoes'))
    except Exception:
        flash('Erro ao verificar permissões!', 'danger')
        return redirect(url_for('movimentacoes'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])
        origem = request.form.get('origem', '')
        nota_fiscal = request.form.get('nota_fiscal', '')
        motivo = request.form.get('motivo', '')
        
        # Buscar produto e verificar se existe
        cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (produto_id,))
        produto = cursor.fetchone()
        
        if not produto:
            flash('Produto não encontrado!', 'danger')
            produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
            return render_template('entrada_produto.html', produtos=produtos)
        
        try:
            # Inserir movimentação
            cursor = unit_db.execute('''
                INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario_responsavel_id, origem, nota_fiscal, motivo)
                VALUES (?, 'entrada', ?, ?, ?, ?, ?)
            ''', (produto_id, quantidade, session['user_id'], origem, nota_fiscal, motivo))
            
            # Atualizar quantidade do produto
            cursor = unit_db.execute('UPDATE produtos SET quantidade = quantidade + ?, data_atualizacao = CURRENT_TIMESTAMP WHERE id = ?', 
                                    (quantidade, produto_id))
            
            unit_db.commit()
            flash(f'Entrada de {quantidade} unidades de {produto["nome"]} registrada com sucesso!', 'success')
            return redirect(url_for('movimentacoes'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao registrar entrada!', 'danger')
    
    produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
    return render_template('entrada_produto.html', produtos=produtos)

@app.route('/movimentacoes/saida', methods=['GET', 'POST'])
def saida_produto():
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    # Verificar permissão de movimentação
    try:
        usuario = db.session.get(Usuario, session['user_id'])
        if not usuario or (usuario.tipo != 'admin' and not usuario.pode_cadastrar):
            flash('Acesso negado! Você não tem permissão para movimentar produtos.', 'danger')
            return redirect(url_for('movimentacoes'))
    except Exception:
        flash('Erro ao verificar permissões!', 'danger')
        return redirect(url_for('movimentacoes'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])
        destino = request.form.get('destino', '')
        ordem_servico = request.form.get('ordem_servico', '')
        motivo = request.form.get('motivo', '')
        
        # Buscar produto e verificar se existe
        cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (produto_id,))
        produto = cursor.fetchone()
        
        if not produto:
            flash('Produto não encontrado!', 'danger')
            produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
            return render_template('saida_produto.html', produtos=produtos)
        
        # Verificar se há estoque suficiente
        if produto['quantidade'] < quantidade:
            flash(f'Estoque insuficiente! Produto tem apenas {produto["quantidade"]} unidades.', 'danger')
            produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
            return render_template('saida_produto.html', produtos=produtos)
        
        try:
            # Atualizar quantidade do produto
            cursor = unit_db.execute('UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?', (quantidade, produto_id))
            
            # Inserir movimentação
            cursor = unit_db.execute('''
                INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario_responsavel_id, destino, ordem_servico, motivo)
                VALUES (?, 'saida', ?, ?, ?, ?, ?)
            ''', (produto_id, quantidade, session['user_id'], destino, ordem_servico, motivo))
            
            unit_db.commit()
            flash(f'Saída de {quantidade} unidades de {produto["nome"]} registrada com sucesso!', 'success')
            return redirect(url_for('movimentacoes'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao registrar saída!', 'danger')
    
    produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
    return render_template('saida_produto.html', produtos=produtos)

@app.route('/movimentacoes/excluir/<int:id>')
def excluir_movimentacao(id):
    if 'unit_id' not in session:
        return redirect(url_for('selecionar_unidade'))
    
    # Verificar permissão
    try:
        usuario = db.session.get(Usuario, session['user_id'])
        if not usuario or (usuario.tipo != 'admin' and not usuario.pode_cadastrar):
            flash('Acesso negado! Você não tem permissão para excluir movimentações.', 'danger')
            return redirect(url_for('movimentacoes'))
    except Exception:
        flash('Erro ao verificar permissões!', 'danger')
        return redirect(url_for('movimentacoes'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('selecionar_unidade'))
    
    try:
        # Buscar movimentação
        cursor = unit_db.execute('SELECT * FROM movimentacoes WHERE id = ?', (id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            flash('Movimentação não encontrada!', 'danger')
            return redirect(url_for('movimentacoes'))
        
        # Buscar produto para reverter estoque
        cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ?', (movimentacao['produto_id'],))
        produto = cursor.fetchone()
        
        if produto:
            # Reverter a movimentação no estoque
            if movimentacao['tipo'] == 'entrada':
                nova_quantidade = produto['quantidade'] - movimentacao['quantidade']
            else:
                nova_quantidade = produto['quantidade'] + movimentacao['quantidade']
            
            # Atualizar quantidade do produto
            cursor = unit_db.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (nova_quantidade, movimentacao['produto_id']))
        
        # Excluir movimentação
        cursor = unit_db.execute('DELETE FROM movimentacoes WHERE id = ?', (id,))
        unit_db.commit()
        flash('Movimentação excluída e estoque atualizado!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir movimentação!', 'danger')
    
    return redirect(url_for('movimentacoes'))

if __name__ == '__main__':
    # Antes de iniciar, garantir que o schema central contenha colunas esperadas
    def ensure_central_schema():
        conn = None
        try:
            # Usar sqlite3 para inspeção e alteração direta do arquivo central.db
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(usuarios)")
            cols = [r[1] for r in cur.fetchall()]

            # Adicionar coluna pode_cadastrar se ausente
            if 'pode_cadastrar' not in cols:
                cur.execute("ALTER TABLE usuarios ADD COLUMN pode_cadastrar INTEGER DEFAULT 1")
                conn.commit()
                print('Coluna pode_cadastrar adicionada em usuarios (central.db)')
                
            # Adicionar coluna permissoes_menu se ausente
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
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # Inicializar banco central se não existir e garantir colunas compatíveis
    try:
        ensure_central_schema()
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Aviso: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)
